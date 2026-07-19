import logging, time, redis
from datetime import datetime
from django.http import JsonResponse
from limiter.services.memory_limiter import MemoryRateLimiter
from limiter.services.stats import rate_limit_stats
from limiter.services.events import event_manager, EventType
from limiter.utils.key_builder import build_rate_limit_key
from limiter.config import REDIS_RETRY_AFTER,RATE_LIMITER,RATE_LIMITS, PLAN_LIMITS
from limiter.utils.resolve_limits import resolve_limits
from limiter.utils.limiter_factory import build_limiter

logger = logging.getLogger(__name__)

MONITORING_ENDPOINTS = {
    "/dashboard/",
    "/api/rate-limit/health/",
    "/api/rate-limit/health",
    "/api/rate-limit/stats/",
    "/api/rate-limit/events/",
    "/api/rate-limit/config/",
    "/favicon.ico",
}

class RateLimitMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_down_until = 0
    
    def __call__(self, request):
        now = time.time()

        #configure path
        path = request.path

        #exclude monitoring endpoints 
        if path in MONITORING_ENDPOINTS:
            return self.get_response(request)

        rate_limit_stats.increment_total()
        rate_limit_stats.increment_endpoint(path)

        # Load rate limit policy for the requested endpoint.
        route_config = RATE_LIMITS.get(
            path,
            {"capacity" : 10 , "refill_rate" : 1}
        )

        plan = request.headers.get("X-plan", "free")
        
        # Determine the caller's subscription tier.
        # Defaults to free when no plan is provided.
        plan_config = PLAN_LIMITS.get(
            plan, 
            PLAN_LIMITS["free"]
        )

        # Resolve the effective limits after applying
        # both route-specific and plan-specific policies.
        limits = resolve_limits(route_config, plan_config)       

        #create limiter dynamically
        limiter = build_limiter(
            RATE_LIMITER,
            limits
        )

        memory_limiter = MemoryRateLimiter(
            limit= limits["capacity"],
            window_size= 60
        )

        #Build a unique identifier so each user/IP and route
        key = build_rate_limit_key(request)

        if now < self.redis_down_until:
            result = memory_limiter.is_allowed(key)
            rate_limit_stats.active_limiter = "memory"
            
            rate_limit_stats.increment_memory_requests()
        else:
            #apply limiter
            try:
                result = limiter.is_allowed(key)

                if not rate_limit_stats.redis_available:
                    rate_limit_stats.redis_available = True
                    event_manager.add_event(
                        EventType.REDIS_RESTORED,
                        "Redis connection restored"
                    )
                if rate_limit_stats.fallback_active:
                    rate_limit_stats.fallback_active = False
                    event_manager.add_event(
                        EventType.FALLBACK_DISABLED,
                        "Memory limiter turned off"
                    )

                rate_limit_stats.active_limiter = "redis"
                
                rate_limit_stats.fallback_active = False
                
                rate_limit_stats.increment_redis_requests()

                if not rate_limit_stats.redis_available:
                    logger.warning("Redis connection restored, switching back to redis limiter.")
                    
            except redis.exceptions.ConnectionError:
                logger.warning("Redis unavailable, using memory fallback")

                if rate_limit_stats.redis_available:
                    event_manager.add_event(
                        EventType.REDIS_LOST,
                        "Redis connection lost"
                    )
                    rate_limit_stats.redis_available = False
                if not rate_limit_stats.fallback_active:
                    event_manager.add_event(
                        EventType.FALLBACK_ENABLED,
                        "Switched to memory limiter"
                    )
                    rate_limit_stats.fallback_active = True

                self.redis_down_until = now + REDIS_RETRY_AFTER
                result = memory_limiter.is_allowed(key)

                rate_limit_stats.active_limiter = "memory"
                
                rate_limit_stats.increment_memory_requests()

        # Reject requests that exceed the configured limit.
        if not result["allowed"]:
            rate_limit_stats.increment_blocked()

            rate_limit_stats.add_request(
                False,
                request.path,
                datetime.now().strftime("%H:%M:%S"),
            )

            logger.warning(
                "rate limit exceeded",
                extra={
                    "key" : key,
                    "path" : request.path,
                    "retry_after" : result["retry_after"],
                }
            )

            event_manager.add_event(
                EventType.BLOCK,
                "rate limit exceeded",
                path = request.path,
                retry_after = result["retry_after"],
                limiter= rate_limit_stats.active_limiter,
            )

            return JsonResponse(
                {
                    "error" : "rate limit exceeded",
                    "retry_after" : result["retry_after"],
                },
                status = 429,
                headers = {
                    "Retry-After" : str(int(result["retry_after"]))     #retry_after may get float value so to round it up it is int and http response needs to be string
                }
            )
        
        #continue request
        response = self.get_response(request)

        rate_limit_stats.increment_allowed()
        rate_limit_stats.add_request(
            True,
            request.path,
            datetime.now().strftime("%H:%M:%S"),
        )

        event_manager.add_event(
            EventType.ALLOW,
            "Request allowed",
            path=request.path,
            limiter= rate_limit_stats.active_limiter,
        )

        #attach headers
        response["x-ratelimit-limit"] = result["limit"]
        response["x-ratelimit-remaining"] = result["remaining"]

        return response
    
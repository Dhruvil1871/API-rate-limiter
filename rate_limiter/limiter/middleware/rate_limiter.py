import logging, time, redis
from django.http import JsonResponse
from limiter.services.memory_limiter import MemoryRateLimiter
from limiter.utils.key_builder import build_rate_limit_key
from limiter.config import REDIS_RETRY_AFTER,RATE_LIMITER,RATE_LIMITS, PLAN_LIMITS
from limiter.utils.resolve_limits import resolve_limits
from limiter.utils.limiter_factory import build_limiter

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.redis_down_until = 0
        self.redis_available = True 
    
    def __call__(self, request):
        now = time.time()

        #configure path
        path = request.path

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
        else:
            #apply limiter
            try:
                result = limiter.is_allowed(key) 

                if not self.redis_available:
                    logger.warning("Redis connection restored, switching back to redis limiter.")
                    self.redis_available = True
                    
            except redis.exceptions.ConnectionError:
                logger.warning("Redis unavailable, using memory fallback")

                self.redis_available = False

                self.redis_down_until = now + REDIS_RETRY_AFTER
                result = memory_limiter.is_allowed(key)



        # Reject requests that exceed the configured limit.
        if not result["allowed"]:
            logger.warning(
                "rate limit exceeded",
                extra={
                    "key" : key,
                    "path" : request.path,
                    "retry_after" : result["retry_after"],
                }
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

        #attach headers
        response["x-ratelimit-limit"] = result["limit"]
        response["x-ratelimit-remaining"] = result["remaining"]

        return response
    
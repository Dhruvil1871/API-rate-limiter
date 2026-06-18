from django.http import JsonResponse
from limiter.services.token_bucket import TokenBucketRateLimiter
from limiter.utils.key_builder import build_rate_limit_key
from limiter.config import RATE_LIMITER,RATE_LIMITS, PLAN_LIMITS
from limiter.utils.resolve_limits import resolve_limits
from limiter.utils.limiter_factory import build_limiter
class RateLimitMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
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

        #Build a unique identifier so each user/IP and route
        key = build_rate_limit_key(request)

        #apply limiter
        result = limiter.is_allowed(key) 

        # Reject requests that exceed the configured limit.
        if not result["allowed"]:
            return JsonResponse(
                {
                    "error" : "rate limit exceeded",
                    "retry_after" : result["retry_after"],
                },
                status = 429
            )
        
        #continue request
        response = self.get_response(request)

        #attach headers
        response["x-ratelimit-limit"] = result["limit"]
        response["x-ratelimit-remaining"] = result["remaining"]

        return response
    
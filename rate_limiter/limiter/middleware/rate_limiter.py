from django.http import JsonResponse
from limiter.services.token_bucket import TokenBucketRateLimiter
from limiter.utils.key_builder import buid_rate_limit_key
from  limiter.config import RATE_LIMITS

class RateLimitMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        #configure path
        path = request.path
        config = RATE_LIMITS.get(
            path,
            {"capacity" : 10 , "refill_rate" : 1}
        )

        #create limiter dynamically
        self.limiter = TokenBucketRateLimiter(
            capacity=config["capacity"], 
            refill_rate=config["refill_rate"]
        )

        #build key
        key = buid_rate_limit_key(request)

        #apply limiter
        result = self.limiter.is_allowed(key)

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
    
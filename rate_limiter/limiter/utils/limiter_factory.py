from limiter.services.fixed_window import FixedWindowRateLimiter
from limiter.services.token_bucket import TokenBucketRateLimiter

def build_limiter(algorith, limits):

    if algorith == "fixed_window":
        return FixedWindowRateLimiter(
            limit = limits["capacity"],
            window_size = 60
        )
    
    if algorith == "token_bucket":
        return TokenBucketRateLimiter(
            capacity= limits["capacity"],
            refill_rate= limits["refill_rate"]
        )
    
    raise ValueError(f"unknown algorithm : {algorith}")
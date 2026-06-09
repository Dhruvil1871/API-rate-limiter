from limiter.utils.redis_client import redis_client

class FixedWindowRateLimiter:
    def __init__(self, limit = 5, window_size = 60):
        self.limit = limit
        self.window_size = window_size

    def is_allowed(self, key):
        current_count = redis_client.incr(key)

        if current_count  == 1:
            redis_client.expire(key, self.window_size)

        remaining = self.limit - current_count
        
        if current_count <= self.limit:
            return {
                "allowed": True,
                "ramaining": max(0, remaining),
                "limit" : self.limit,
                "retry_after": 0
            }
        
        return {
            "allowed": False,
            "ramaining": 0,
            "limit" : self.limit,
            "retry_after": redis_client.ttl(key)
        }
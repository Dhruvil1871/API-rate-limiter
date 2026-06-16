#reconstruct bucket state according how many tokens should be refilled after last request

import time
from limiter.utils.redis_client import redis_client

class TokenBucketRateLimiter:
    def __init__(self, capacity = 5, refill_rate = 1):
        self.capacity = capacity
        self.refill_rate = refill_rate
    
    def is_allowed(self, key):
        data = redis_client.hgetall(key)

        if not data:
            tokens = self.capacity
            last_refill = time.time()
        else:
            tokens = float(data.get("tokens", self.capacity))
            last_refill = float(data.get("last_refill", time.time()))
        
        now = time.time()
        elapsed = now - last_refill

        tokens = min(
            self.capacity,
            tokens + (elapsed * self.refill_rate)
        )

        if tokens >= 1:
            allowed = True
            tokens -= 1
            retry_after = 0
        else:
            allowed = False
            retry_after = (1 - tokens) / self.refill_rate

        redis_client.hset(key, mapping={
            "tokens" : tokens,
            "last_refill" : now
        })

        redis_client.expire(key, int(self.capacity / self.refill_rate) + 1)

        return {
            "allowed" : allowed,
            "remaining" : int(tokens),
            "limit" : self.capacity,
            "retry_after" : retry_after
        }
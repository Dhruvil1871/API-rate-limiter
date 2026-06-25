import time

storage = {}

class MemoryRateLimiter:

    def __init__(self, limit, window_size):
        self.limit = limit
        self.window_size = window_size

    def is_allowed(self, key):
        now = time.time()

        if key not in storage:
            storage[key] = {
                "count" : 1,
                "window_start" : now
            }

            return{
                "allowed" : True,
                "remaining" : self.limit - 1,
                "limit" : self.limit,
                "retry_after" : 0
            }
        
        data = storage[key]

        count = data["count"]
        window_start = data["window_start"]

        # window expired
        if now - window_start >= self.window_size:
            storage[key] = {
                "count" : 1,
                "window_start" : now
            }

            return{
                "allowed" : True,
                "remaining" : self.limit - 1,
                "limit" : self.limit,
                "retry_after" : 0
            }
        elif count < self.limit:
            count += 1
            data["count"] = count

            return{
                "allowed" : True,
                "remaining" : self.limit - count,
                "limit" : self.limit,
                "retry_after" : 0
            }
        else:
            retry_after = self.window_size + window_start - now
            return{
                "allowed" : False,
                "remaining" : 0,
                "limit" : self.limit,
                "retry_after" : retry_after
            }
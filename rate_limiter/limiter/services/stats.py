import time
from collections import deque
stats = {}

class Stats:
    def __init__(self):
        self.total_requests = 0
        self.allowed_requests = 0
        self.blocked_requests = 0
        self.redis_requests = 0
        self.memory_fallback_requests = 0

        #runtime stats
        self.redis_available = True
        self.fallback_active = False

        self.active_limiter = "redis"

        self.endpoint_requests = {}

        self.start_time = time.time()

        self.request_history = deque(maxlen=100)

    def increment_total(self):
        self.total_requests += 1

    def increment_allowed(self):
        self.allowed_requests += 1

    def increment_blocked(self):
        self.blocked_requests += 1

    def increment_redis_requests(self):
        self.redis_requests += 1

    def increment_memory_requests(self):
        self.memory_fallback_requests += 1

    def get_uptime(self):
        return int(time.time() - self.start_time)
    
    def increment_endpoint(self, path):
        if path not in self.endpoint_requests:
            self.endpoint_requests[path] = 0

        self.endpoint_requests[path] += 1
    
    def add_request(self, allowed, path, timestamp):
        self.request_history.append({
            "allowed": allowed,
            "path" : path,
            "timestamp": timestamp,
        })

    def to_dict(self):
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "blocked_requests": self.blocked_requests,
            "redis_requests": self.redis_requests,
            "memory_requests": self.memory_fallback_requests,
            "endpoint_requests" : self.endpoint_requests,
            "uptime" : self.get_uptime(),
            "request_history" : list(self.request_history),
        }
    
rate_limit_stats = Stats()
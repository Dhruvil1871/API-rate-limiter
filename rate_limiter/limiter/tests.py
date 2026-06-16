from django.test import TestCase

# Create your tests here.
import time
from limiter.services.fixed_window import FixedWindowRateLimiter
from limiter.services.token_bucket import TokenBucketRateLimiter
from limiter.utils.redis_client import redis_client


class FixedWindowTest(TestCase):

    def test_fixed_window_blocks_after_limit(self):

        key = "test::fixed_window"

        redis_client.delete(key)

        limiter = FixedWindowRateLimiter(
            limit=3,
            window_size=2
        )

        for _ in range(3):
            result = limiter.is_allowed(key)
            self.assertTrue(result["allowed"])

        result = limiter.is_allowed(key)
        self.assertFalse(result["allowed"])

    def test_fixed_window_blocks_after_expiry(self):

        key = "test::fixed_window"

        redis_client.delete(key)

        limiter = FixedWindowRateLimiter(
            limit=3,
            window_size=2
        )

        for _ in range(3):
            result = limiter.is_allowed(key)
            self.assertTrue(result["allowed"])

        result = limiter.is_allowed(key)
        self.assertFalse(result["allowed"])

        time.sleep(3)

        result = limiter.is_allowed(key)
        self.assertTrue(result["allowed"])

class TokenBucketTest(TestCase):

    def test_token_bucket_after_limit(self):
        key = "test::token_bucket"

        redis_client.delete(key)

        limiter = TokenBucketRateLimiter(
            capacity= 3,
            refill_rate= 1
        )

        for _ in range(3):
            result = limiter.is_allowed(key)
            self.assertTrue(result["allowed"])
        
        result = limiter.is_allowed(key)
        self.assertFalse(result["allowed"])

    def test_token_bucket_refill(self):
        key = "user::token_bucket"

        redis_client.delete(key)

        limiter = TokenBucketRateLimiter(
            capacity= 3,
            refill_rate= 1
        )

        for _ in range(3):
            result = limiter.is_allowed(key)
            self.assertTrue(result["allowed"])
        
        result = limiter.is_allowed(key)
        self.assertFalse(result["allowed"])

        time.sleep(2)

        result = limiter.is_allowed(key)
        self.assertTrue(int(result["remaining"]), 1)
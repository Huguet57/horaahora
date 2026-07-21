from __future__ import annotations

import time
import uuid

from redis import Redis


class RedisRateLimiter:
    """Portable Redis sorted-set sliding-window limiter."""

    def __init__(self, redis_url: str, max_requests: int = 30, window_seconds: int = 600) -> None:
        self.client = Redis.from_url(redis_url, decode_responses=True)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def allow(self, identifier: str) -> tuple[bool, int]:
        now = time.time()
        key = f"rate-limit:{identifier}"
        cutoff = now - self.window_seconds
        with self.client.pipeline(transaction=True) as pipeline:
            pipeline.zremrangebyscore(key, 0, cutoff)
            pipeline.zcard(key)
            _, count = pipeline.execute()
        if int(count) >= self.max_requests:
            oldest = self.client.zrange(key, 0, 0, withscores=True)
            reset = self.window_seconds
            if oldest:
                reset = max(1, int(self.window_seconds - (now - oldest[0][1])))
            return False, reset
        member = f"{now}:{uuid.uuid4()}"
        with self.client.pipeline(transaction=True) as pipeline:
            pipeline.zadd(key, {member: now})
            pipeline.expire(key, self.window_seconds)
            pipeline.execute()
        return True, self.window_seconds

import time

from fastapi import HTTPException

from app.redis_client import RedisClient


class RateLimiter:
    def __init__(self, redis_client: RedisClient, limit: int, window_seconds: int):
        self._redis = redis_client
        self._limit = limit
        self._window = window_seconds

    async def check(self, user_id: str) -> None:
        now = time.time()
        key = f"rate:{user_id}"
        pipe = self._redis.client.pipeline()
        pipe.zremrangebyscore(key, 0, now - self._window)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, self._window)
        removed, count, *_ = await pipe.execute()
        _ = removed

        if int(count) >= self._limit:
            retry_after = self._window
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(self._limit),
                    "Retry-After": str(retry_after),
                },
            )


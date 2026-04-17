from __future__ import annotations

import redis.asyncio as redis


class RedisClient:
    def __init__(self, url: str):
        self._url = url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        self._client = redis.from_url(self._url, decode_responses=True)
        await self._client.ping()

    @property
    def client(self) -> redis.Redis:
        if not self._client:
            raise RuntimeError("redis not connected")
        return self._client

    async def ping(self) -> bool:
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


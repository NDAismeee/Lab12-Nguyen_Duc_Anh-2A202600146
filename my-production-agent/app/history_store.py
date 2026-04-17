import json
import time

from app.redis_client import RedisClient


class HistoryStore:
    def __init__(self, redis_client: RedisClient, max_messages: int):
        self._redis = redis_client
        self._max = max_messages

    def _key(self, user_id: str) -> str:
        return f"history:{user_id}"

    async def append(self, user_id: str, role: str, content: str) -> None:
        item = json.dumps({"role": role, "content": content, "ts": time.time()}, ensure_ascii=False)
        key = self._key(user_id)
        pipe = self._redis.client.pipeline()
        pipe.rpush(key, item)
        pipe.ltrim(key, -self._max, -1)
        pipe.expire(key, 7 * 24 * 3600)
        await pipe.execute()

    async def get_history(self, user_id: str) -> list[dict]:
        key = self._key(user_id)
        raw = await self._redis.client.lrange(key, 0, -1)
        out: list[dict] = []
        for s in raw:
            try:
                out.append(json.loads(s))
            except Exception:
                continue
        return out


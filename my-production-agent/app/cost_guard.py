import time

from fastapi import HTTPException

from app.redis_client import RedisClient


class CostGuard:
    def __init__(self, redis_client: RedisClient, monthly_budget_usd: float):
        self._redis = redis_client
        self._monthly_budget = float(monthly_budget_usd)

    def _month_key(self) -> str:
        return time.strftime("%Y-%m")

    def estimate_cost_usd(self, question: str, answer: str) -> float:
        input_tokens = max(1, len(question.split()) * 2)
        output_tokens = max(1, len(answer.split()) * 2) if answer else 1
        price_per_1k_in = 0.00015
        price_per_1k_out = 0.0006
        return round((input_tokens / 1000) * price_per_1k_in + (output_tokens / 1000) * price_per_1k_out, 6)

    async def check_budget(self, user_id: str, estimated_cost: float) -> None:
        key = f"budget:{user_id}:{self._month_key()}"
        current_raw = await self._redis.client.get(key)
        current = float(current_raw or 0.0)
        if current + float(estimated_cost) > self._monthly_budget:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Monthly budget exceeded",
                    "used_usd": round(current, 6),
                    "budget_usd": self._monthly_budget,
                    "month": self._month_key(),
                },
            )

    async def record_usage(self, user_id: str, cost_usd: float) -> None:
        key = f"budget:{user_id}:{self._month_key()}"
        await self._redis.client.incrbyfloat(key, float(cost_usd))
        await self._redis.client.expire(key, 35 * 24 * 3600)


from __future__ import annotations

import asyncio
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app import mock_llm


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def _to_openai_messages(history: list[dict], question: str) -> list[dict[str, Any]]:
    msgs: list[dict[str, Any]] = []
    msgs.append({"role": "system", "content": "You are a helpful assistant."})
    for m in history:
        role = m.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = m.get("content")
        if isinstance(content, str) and content:
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": question})
    return msgs


async def chat(question: str, history: list[dict]) -> tuple[str, dict]:
    if not (settings.openai_api_key or "").strip():
        answer = await asyncio.to_thread(mock_llm.ask, question)
        return answer, {}

    client = _get_client()
    messages = _to_openai_messages(history, question)
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
    )
    answer = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None)
    usage_dict = usage.model_dump() if usage else {}
    return answer, usage_dict


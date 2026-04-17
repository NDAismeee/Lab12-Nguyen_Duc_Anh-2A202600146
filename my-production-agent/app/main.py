import json
import logging
import signal
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import CostGuard
from app.history_store import HistoryStore
from app.history_api import router as history_router
from app.logging_utils import configure_logging
from app.openai_chat import chat as openai_chat
from app.rate_limiter import RateLimiter
from app.redis_client import RedisClient


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


START_TIME = time.time()
_ready = False
_shutting_down = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ready, _shutting_down

    configure_logging(settings.log_level)
    logger = logging.getLogger("app")

    app.state.redis = RedisClient(settings.redis_url)
    app.state.rate_limiter = RateLimiter(app.state.redis, limit=settings.rate_limit_per_minute, window_seconds=60)
    app.state.cost_guard = CostGuard(app.state.redis, monthly_budget_usd=settings.monthly_budget_usd)
    app.state.history = HistoryStore(app.state.redis, max_messages=settings.history_max_messages)

    logger.info(json.dumps({"event": "startup", "environment": settings.environment, "port": settings.port}))
    await app.state.redis.connect()
    _ready = True

    try:
        yield
    finally:
        _shutting_down = True
        _ready = False
        logger.info(json.dumps({"event": "shutdown_start"}))
        await app.state.redis.close()
        logger.info(json.dumps({"event": "shutdown_complete"}))


app = FastAPI(title="My Production Agent", version="1.0.0", lifespan=lifespan)
app.include_router(history_router)


@app.middleware("http")
async def request_context(request: Request, call_next):
    logger = logging.getLogger("http")
    start = time.time()
    try:
        response: Response = await call_next(request)
        return response
    finally:
        ms = int((time.time() - start) * 1000)
        logger.info(json.dumps({"event": "request", "method": request.method, "path": request.url.path, "ms": ms}))


@app.get("/health")
def health():
    return {"status": "ok", "uptime_seconds": round(time.time() - START_TIME, 1)}


@app.get("/ready")
async def ready():
    if _shutting_down or not _ready:
        raise HTTPException(status_code=503, detail="not ready")
    ok = await app.state.redis.ping()
    if not ok:
        raise HTTPException(status_code=503, detail="redis not ready")
    return {"ready": True}


@app.post("/ask")
async def ask(
    body: AskRequest,
    user_id: str = Depends(verify_api_key),
):
    if _shutting_down or not _ready:
        raise HTTPException(status_code=503, detail="shutting down")

    await app.state.rate_limiter.check(user_id)

    estimated_cost = app.state.cost_guard.estimate_cost_usd(body.question, "")
    await app.state.cost_guard.check_budget(user_id, estimated_cost)

    history = await app.state.history.get_history(user_id)
    answer, _usage = await openai_chat(body.question, history)

    actual_cost = app.state.cost_guard.estimate_cost_usd(body.question, answer)
    await app.state.cost_guard.record_usage(user_id, actual_cost)

    await app.state.history.append(user_id, "user", body.question)
    await app.state.history.append(user_id, "assistant", answer)

    return {"question": body.question, "answer": answer}


def _handle_sigterm(signum, _frame):
    global _shutting_down
    _shutting_down = True


signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)


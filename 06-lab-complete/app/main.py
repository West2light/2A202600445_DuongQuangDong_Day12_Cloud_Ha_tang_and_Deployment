"""
Production AI Agent — Kết hợp tất cả Day 12 concepts

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Rate limiting (10 req/min per user, Redis-backed)
  ✅ Cost guard ($10/month per user, Redis-backed)
  ✅ Conversation history (Redis-backed, stateless)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
  ✅ Security headers
  ✅ CORS
  ✅ Error handling
"""
import json
import signal
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
import uvicorn
import logging

from app.config import settings
from utils.mock_llm import ask as llm_ask

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Redis Client (optional — fallback to in-memory)
# ─────────────────────────────────────────────────────────
_redis = None
if settings.redis_url:
    try:
        import redis as _redis_lib
        _redis = _redis_lib.from_url(settings.redis_url, decode_responses=True)
        _redis.ping()
        logger.info(json.dumps({"event": "redis_connected"}))
    except Exception as e:
        logger.warning(json.dumps({"event": "redis_unavailable", "error": str(e)}))
        _redis = None

# ─────────────────────────────────────────────────────────
# Rate Limiter — Redis (sliding window sorted set) hoặc in-memory
# ─────────────────────────────────────────────────────────
_mem_rate: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str):
    limit = settings.rate_limit_per_minute
    now = time.time()

    if _redis:
        window_key = f"rate:{key}"
        pipe = _redis.pipeline()
        pipe.zremrangebyscore(window_key, 0, now - 60)
        pipe.zcard(window_key)
        results = pipe.execute()
        count = results[1]
        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail={"error": "Rate limit exceeded", "limit": limit, "window_seconds": 60},
                headers={"Retry-After": "60"},
            )
        _redis.zadd(window_key, {str(now): now})
        _redis.expire(window_key, 70)
    else:
        window = _mem_rate[key]
        while window and window[0] < now - 60:
            window.popleft()
        if len(window) >= limit:
            raise HTTPException(
                status_code=429,
                detail={"error": "Rate limit exceeded", "limit": limit, "window_seconds": 60},
                headers={"Retry-After": "60"},
            )
        window.append(now)


# ─────────────────────────────────────────────────────────
# Cost Guard — per-user monthly, Redis hoặc in-memory fallback
# ─────────────────────────────────────────────────────────
_mem_monthly: dict[str, float] = defaultdict(float)
_mem_month_key: str = time.strftime("%Y-%m")


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * 0.15 + (output_tokens / 1_000_000) * 0.60


def check_and_record_cost(user_key: str, input_tokens: int, output_tokens: int):
    cost = _estimate_cost(input_tokens, output_tokens)
    budget = settings.monthly_budget_usd

    if _redis:
        month = time.strftime("%Y-%m")
        cost_key = f"cost:{user_key}:{month}"
        current = float(_redis.get(cost_key) or 0)
        if current >= budget:
            raise HTTPException(
                status_code=402,
                detail=f"Monthly budget of ${budget} exhausted. Try next month.",
            )
        _redis.incrbyfloat(cost_key, cost)
        _redis.expire(cost_key, 35 * 24 * 3600)
    else:
        global _mem_month_key
        month = time.strftime("%Y-%m")
        if month != _mem_month_key:
            _mem_monthly.clear()
            _mem_month_key = month
        if _mem_monthly[user_key] >= budget:
            raise HTTPException(
                status_code=402,
                detail=f"Monthly budget of ${budget} exhausted. Try next month.",
            )
        _mem_monthly[user_key] += cost


# ─────────────────────────────────────────────────────────
# Conversation History — Redis list (stateless)
# ─────────────────────────────────────────────────────────
HISTORY_MAX_TURNS = 10  # 10 lượt = 20 messages


def get_history(user_key: str, session_id: str) -> list[dict]:
    if not _redis or not session_id:
        return []
    key = f"history:{user_key}:{session_id}"
    raw = _redis.lrange(key, -HISTORY_MAX_TURNS * 2, -1)
    return [json.loads(m) for m in raw]


def save_history(user_key: str, session_id: str, question: str, answer: str):
    if not _redis or not session_id:
        return
    key = f"history:{user_key}:{session_id}"
    pipe = _redis.pipeline()
    pipe.rpush(key, json.dumps({"role": "user", "content": question}))
    pipe.rpush(key, json.dumps({"role": "assistant", "content": answer}))
    pipe.expire(key, 2 * 3600)  # 2h TTL
    pipe.execute()


# ─────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include header: X-API-Key: <your-key>",
        )
    if api_key != settings.agent_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key


# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "redis": "connected" if _redis else "in-memory",
    }))
    time.sleep(0.1)
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception:
        _error_count += 1
        raise


# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(None, description="Session ID để track conversation history")


class AskResponse(BaseModel):
    question: str
    answer: str
    session_id: str | None
    history_turns: int
    model: str
    timestamp: str


# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Gửi câu hỏi tới AI agent.

    - **question**: Câu hỏi (1–2000 ký tự)
    - **session_id**: (tuỳ chọn) Session ID để lưu lịch sử hội thoại vào Redis
    - **Authentication**: Header `X-API-Key: <your-key>`
    """
    user_bucket = _key[:8]

    # 1. Rate limit (per API key)
    check_rate_limit(user_bucket)

    # 2. Budget check (per API key, monthly)
    input_tokens = len(body.question.split()) * 2
    check_and_record_cost(user_bucket, input_tokens, 0)

    # 3. Load conversation history từ Redis
    history = get_history(user_bucket, body.session_id)

    logger.info(json.dumps({
        "event": "agent_call",
        "q_len": len(body.question),
        "session_id": body.session_id,
        "history_turns": len(history) // 2,
        "client": str(request.client.host) if request.client else "unknown",
    }))

    # 4. Gọi LLM
    answer = llm_ask(body.question)

    # 5. Ghi cost output
    output_tokens = len(answer.split()) * 2
    check_and_record_cost(user_bucket, 0, output_tokens)

    # 6. Lưu history vào Redis
    save_history(user_bucket, body.session_id, body.question, answer)

    return AskResponse(
        question=body.question,
        answer=answer,
        session_id=body.session_id,
        history_turns=len(history) // 2,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe — container còn sống không?"""
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "redis": "connected" if _redis else "in-memory",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe — sẵn sàng nhận traffic chưa?"""
    if not _is_ready:
        raise HTTPException(status_code=503, detail="Not ready yet.")
    checks = {"app": "ok"}
    if _redis:
        try:
            _redis.ping()
            checks["redis"] = "ok"
        except Exception:
            raise HTTPException(status_code=503, detail="Redis unavailable.")
    return {"ready": True, "checks": checks}


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    """Metrics cơ bản (yêu cầu API key)."""
    user_bucket = _key[:8]
    monthly_spend = 0.0
    if _redis:
        month = time.strftime("%Y-%m")
        monthly_spend = float(_redis.get(f"cost:{user_bucket}:{month}") or 0)
    else:
        monthly_spend = _mem_monthly.get(user_bucket, 0.0)

    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "monthly_spend_usd": round(monthly_spend, 6),
        "monthly_budget_usd": settings.monthly_budget_usd,
        "budget_used_pct": round(monthly_spend / settings.monthly_budget_usd * 100, 1),
    }


# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_sigterm(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, _handle_sigterm)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )

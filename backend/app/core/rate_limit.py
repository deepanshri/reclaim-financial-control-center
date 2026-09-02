import time
from collections import defaultdict, deque
from typing import Deque, DefaultDict

from fastapi import HTTPException, Request, status

from app.core.config import settings

_hits: DefaultDict[str, Deque[float]] = defaultdict(deque)
_login_hits: DefaultDict[str, Deque[float]] = defaultdict(deque)
_PUBLIC_PREFIXES = ("/api/health", "/api/auth/login", "/docs", "/redoc", "/openapi.json", "/")


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _trim_and_check(bucket: Deque[float], now: float, limit: int) -> None:
    window = 60.0
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a moment and try again.",
        )
    bucket.append(now)


async def enforce_rate_limit(request: Request) -> None:
    path = request.url.path
    if path == "/" or any(path.startswith(prefix) for prefix in _PUBLIC_PREFIXES if prefix != "/"):
        if path in ("/", "/api/health") or path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
            return
    now = time.time()
    key = client_key(request)
    if path == "/api/auth/login":
        _trim_and_check(_login_hits[key], now, settings.login_rate_limit_per_minute)
        return
    _trim_and_check(_hits[key], now, settings.rate_limit_per_minute)

"""HTTP security headers and simple in-process rate limits."""
from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# path prefix -> (max_events, window_seconds)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/login": (12, 60),
    "/register": (5, 60),
    "/refresh": (20, 60),
}

_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("cf-connecting-ip")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return (request.client.host or "unknown")[:64]
    return "unknown"


def check_rate_limit(request: Request, path: str) -> JSONResponse | None:
    rule = RATE_LIMITS.get(path)
    if not rule:
        return None
    max_events, window = rule
    key = f"{_client_ip(request)}:{path}"
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= max_events:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many attempts. Wait a minute and try again."},
                headers={"Retry-After": str(window)},
            )
        q.append(now)
    return None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if request.method == "POST" and path in RATE_LIMITS:
            limited = check_rate_limit(request, path)
            if limited is not None:
                return limited

        response = await call_next(request)
        # Harden browser-facing responses without breaking the SPA
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # CSP: allow self + Google Fonts used by the SPA; block framing and mixed content
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        # API JSON is not framed; CSP allows same-origin SPA assets
        if path.startswith("/api") or path.startswith("/printers") or path.startswith("/agent") or path in (
            "/login",
            "/register",
            "/me",
            "/health",
        ):
            response.headers.setdefault("Cache-Control", "no-store")
        if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

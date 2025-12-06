# middlewares.py
import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from exceptions.exceptions import AuthException, app_exception_handler
from logger import log_success


class RequestSizeLimiter(BaseHTTPMiddleware):
    """
    Rejects requests with Content-Length or body size > max_size (bytes).
    Must be added FIRST (highest priority).
    """

    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10 MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.method not in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length is not None:
            if int(content_length) > self.max_size:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"Request body too large. Max size: {self.max_size:,} bytes.",
                    ),
                )

        # In case no Content-Length header (chunked), we stream and count
        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > self.max_size:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"Request body too large. Max size: {self.max_size:,} bytes.",
                    ),
                )

        # Re-inject the body so the route still sees it
        request._body = body
        request.scope["body"] = body
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        # HSTS disable; needed in dev
        # response.headers["Strict-Transport-Security"] = (
        #     "max-age=31536000; includeSubDomains"
        # )
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if response.status_code < 400:
            log_success(request, response.status_code)
        return response


limiter = Limiter(key_func=get_remote_address)


def add_middlewares(app: FastAPI) -> None:
    # 1. Highest priority – reject huge bodies FIRST
    app.add_middleware(RequestSizeLimiter, max_size=10 * 1024 * 1024)  # 10 MB

    app.state.limiter = limiter
    # 2. Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(AuthException, app_exception_handler)
    app.add_middleware(
        SlowAPIMiddleware
    )  # <-- this must come AFTER limiter is in state

    # 5. CORS – locked down (configure origins as needed)
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=["http://localhost:8000",
        # "http:/http://127.0.0.1:8000"
        # ], # to be populated
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

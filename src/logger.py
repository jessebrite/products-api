import logging
import sys
import uuid
from contextvars import ContextVar
from copy import deepcopy
from typing import Any
from unittest.mock import Mock

from fastapi import Request
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
_request_id: ContextVar[str] = ContextVar("request_id", default=None)


def setup_logger():
    """Set up the logger for the application."""
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "@timestamp", "levelname": "level"},
        static_fields={"service": "products-api"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


SENSITIVE_KEYS: set[str] = {
    "password",
    "new_password",
    "current_password",
    "access_token",
    "refresh_token",
    "token",
    "jwt",
    "authorization",
    "api_key",
    "secret",
    "private_key",
    "credit_card",
    "ssn",
    "cvv",
}

# Optional: also catch common variations
SENSITIVE_KEYWORDS: set[str] = {
    "pass",
    "token",
    "secret",
    "key",
    "auth",
    "jwt",
    "bearer",
}


def _redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive fields in dicts (and lists of dicts)."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            key_lower = k.lower()
            any_sensitive_keyword = any(
                word in key_lower for word in SENSITIVE_KEYWORDS
            )
            is_exact_match = key_lower in SENSITIVE_KEYS

            if is_exact_match or any_sensitive_keyword:
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = _redact_sensitive_data(v)
        return redacted

    elif isinstance(data, list):
        return [_redact_sensitive_data(item) for item in data]

    else:
        return data


def _get_log_context(
    request: Request,
    status_code: int | None = None,
    detail: str | None = None,
    response_body: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build structured log context with safe attribute access."""
    # Ensure we have a request_id (generate if missing)
    request_id = _request_id.get()
    if not request_id:
        request_id = str(uuid.uuid4())
        _request_id.set(request_id)

    # Safely extract user ID (avoid leaking Mock objects in tests)
    user_id = None
    if hasattr(request, "state") and request.state:
        user = getattr(request.state, "user", None)
        if user is not None:
            user_id_candidate = getattr(user, "id", None)
            if not isinstance(user_id_candidate, Mock):
                user_id = user_id_candidate

    final_request_id = (
        getattr(request.state, "request_id", None) or request_id
        if hasattr(request, "state")
        else request_id
    )
    safe_response_body = None
    if response_body:
        safe_response_body = _redact_sensitive_data(deepcopy(response_body))

    return {
        "request_id": final_request_id,
        "method": request.method,
        "path": request.url.path if request.url else None,
        "query_params": request.url.query
        if request.url and request.url.query
        else None,
        "status_code": status_code,
        "user_id": user_id,
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "detail": detail,
        "response_body": safe_response_body,
    }


def log_response(
    request: Request,
    exc: Exception | None = None,
    response_body: dict | None = None,
    status_code: int | None = None,
):
    """Log a response with full context."""
    is_error: bool = exc is not None
    code: int = exc.status_code if exc else status_code
    detail: str = exc.detail if exc else None

    log_context: dict[str, str] = _get_log_context(request, code, detail, response_body)

    if is_error:
        if code >= 500:
            logger.error(f"Server error: {code}", extra=log_context, exc_info=True)
        elif code == 400:
            logger.error(f"Bad Request: {code}", extra=log_context)
        elif code == 401:
            logger.error(f"Unauthorized: {code}", extra=log_context)
        elif code in (404, 409):
            logger.error(
                f"{'Not found' if code == 404 else 'Conflict'}: {code}",
                extra=log_context,
            )
        else:
            logger.error(f"Client error: {code}", extra=log_context)
    else:
        logger.info(f"Request succeeded: {code}", extra=log_context)

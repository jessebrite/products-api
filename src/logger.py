import logging
import sys
from contextvars import ContextVar
from unittest.mock import Mock
from uuid import uuid4

from fastapi import Request
from pythonjsonlogger import jsonlogger

logger = logging.getLogger("api")
_request_id: ContextVar[str] = ContextVar("request_id", default=None)


def setup_logger():
    """Set up the logger for the application."""
    if not logger.handlers:  # prevent double-init in reload
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(method)s\n"
            " %(path)s %(status_code)s %(user_id)s %(ip)s %(user_agent)s %(detail)s",
            static_fields={"service": "products-api"},
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def _get_log_context(
    request: Request,
    status_code: int,
    detail: str = None,
    response_body: dict | None = None,
):
    """Helper function to build log context."""
    request_id = _request_id.get() or str(uuid4())
    _request_id.set(request_id)

    user_id = None
    if (
        request.state
        and hasattr(request.state, "user")
        and request.state.user is not None
    ):
        user_id_candidate = getattr(request.state.user, "id", None)
        if not isinstance(user_id_candidate, Mock):
            user_id = user_id_candidate

    return {
        "request_id": (
            getattr(request.state, "request_id", request_id)
            if request.state
            else request_id
        ),
        "method": getattr(request, "method", None),
        "path": (
            request.url.path if request.url and hasattr(request.url, "path") else None
        ),
        "status_code": status_code,
        "user_id": user_id,
        "ip": (
            request.client.host
            if request.client and hasattr(request.client, "host")
            else None
        ),
        "user_agent": request.headers.get("user-agent") if request.headers else None,
        "detail": detail,
        "response_body": response_body,
    }


def log_exception(request: Request, exc, response_body: dict | None = None):
    """Log an exception with full context."""
    log_context = _get_log_context(request, exc.status_code, exc.detail, response_body)

    if exc.status_code >= 500:
        logger.error(
            f"Server error: {exc.status_code}", extra=log_context, exc_info=True
        )
    elif exc.status_code >= 400:
        if exc.status_code == 400:
            logger.error("Bad Request", extra=log_context)
        elif exc.status_code in (401, 403, 422, 429):
            logger.warning(f"Client error: {exc.status_code}", extra=log_context)
        else:
            logger.info(f"Client error: {exc.status_code}", extra=log_context)
    else:
        logger.info("Request succeeded", extra=log_context)


def log_success(request: Request, status_code: int, response_body: dict | None = None):
    """Log a successful response with full context."""
    log_context = _get_log_context(request, status_code, response_body=response_body)
    logger.info("Request succeeded", extra=log_context)

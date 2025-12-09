from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from exceptions.enums import ErrorCode
from logger import log_response


class AuthException(HTTPException):
    status_code: int = HTTP_500_INTERNAL_SERVER_ERROR
    code: ErrorCode = ErrorCode.INTERNAL_ERROR
    detail: str = "An unexpected error occurred"

    def __init__(
        self,
        *,
        detail: str | None = None,
        code: ErrorCode | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers={
                "X-Error-Code": (code or self.code).value,
                **(headers or {}),
            },
        )


class BadRequestException(AuthException):
    status_code = HTTP_400_BAD_REQUEST
    code = ErrorCode.BAD_REQUEST
    detail = "Bad request"


class ValidationException(AuthException):
    status_code = HTTP_422_UNPROCESSABLE_ENTITY
    code = ErrorCode.VALIDATION_ERROR
    detail = "Validation error"


class UnauthorizedException(AuthException):
    status_code = HTTP_401_UNAUTHORIZED
    code = ErrorCode.UNAUTHORIZED
    detail = "Authentication required"
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenException(AuthException):
    status_code = HTTP_403_FORBIDDEN
    code = ErrorCode.FORBIDDEN
    detail = "Permission denied"


class NotFoundException(AuthException):
    status_code = HTTP_404_NOT_FOUND
    code = ErrorCode.NOT_FOUND
    detail = "Resource not found"


class ConflictException(AuthException):
    status_code = HTTP_409_CONFLICT
    code = ErrorCode.CONFLICT
    detail = "Resource conflict"


class RateLimitException(AuthException):
    status_code = HTTP_429_TOO_MANY_REQUESTS
    code = ErrorCode.RATE_LIMITED
    detail = "Too many requests"


# Domain-specific
class UserNotFoundException(NotFoundException):
    code = ErrorCode.USER_NOT_FOUND
    detail = "User not found"


class UsernameAlreadyExistsException(ConflictException):
    code = ErrorCode.USER_EXISTS
    detail = "User with this email already exists"


class EmailAlreadyExistsException(ConflictException):
    code = ErrorCode.USER_EXISTS
    detail = "User with this email already exists"


class InvalidCredentialsException(UnauthorizedException):
    code = ErrorCode.INVALID_CREDENTIALS
    detail = "Invalid email or password"


class InactiveUserException(ForbiddenException):
    code = ErrorCode.INACTIVE_USER
    detail = "User account is inactive"


async def app_exception_handler(request: Request, exc: AuthException) -> JSONResponse:
    response_body: dict[str, str] = {
        "detail": exc.detail,
        "code": exc.headers["X-Error-Code"],
        "path": request.url.path,
        "method": request.method,
        "timestamp": __import__("datetime")
        .datetime.utcnow()
        .isoformat(timespec="seconds")
        + "Z",
    }

    log_response(request, exc, response_body)

    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=exc.headers,
    )

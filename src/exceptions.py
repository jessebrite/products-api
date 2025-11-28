from fastapi import HTTPException, status


class AuthException(HTTPException):
    """Centralized auth exception – one place to customize headers/logic."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

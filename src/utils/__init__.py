"""Utility functions."""

import logging
from logging import Logger

from fastapi.responses import JSONResponse
from sqlalchemy.sql import text

from database import SessionLocal

logger: Logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


def liveness() -> JSONResponse:
    return JSONResponse(status_code=200, content={"status": "ok"})


async def _check_database() -> bool:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def health_check():
    checks = {
        "database": await _check_database(),
    }
    return checks


__all__ = ["liveness", "health_check"]

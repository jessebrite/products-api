"""Database connection and session management."""

import os
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

DATABASE_URL = os.getenv("DATABASE_URL", settings.database_url)

engine: Engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

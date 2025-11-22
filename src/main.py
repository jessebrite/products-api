"""
FastAPI CRUD application with security and Swagger documentation.
"""

from fastapi import FastAPI
from sqlalchemy import create_engine

from config import settings
from models import Base
from routers import auth, users, items
from utils import health_check

# Create database engine and tables
engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
)

# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(items.router, prefix=settings.api_prefix)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def get_health():
    """Health check endpoint."""
    return health_check()

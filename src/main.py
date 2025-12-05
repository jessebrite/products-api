"""
FastAPI CRUD application with security and Swagger documentation.
"""

from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine

from config.settings import settings
from exceptions.exceptions import AuthException, app_exception_handler
from logger import LoggingMiddleware, setup_logger
from models import Base
from routers import auth, items, users
from utils import health_check

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)

setup_logger()

# Initialize FastAPI app
app: FastAPI = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_exception_handler(AuthException, app_exception_handler)
app.add_middleware(LoggingMiddleware)


# Root path redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def get_health() -> Response:
    """Health check endpoint."""
    return health_check()


# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(items.router, prefix=settings.api_prefix)

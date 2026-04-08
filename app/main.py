import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.middleware.error_handler import register_exception_handlers
from app.api.middleware.rate_limiter import limiter
from app.api.middleware.security_headers import SecurityHeadersMiddleware
from app.api.v1.routes import api_router
from app.core.config import settings
from app.core.logger import setup_logging
from app.database import close_db, engine, init_db

logger = logging.getLogger(__name__)


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=redefined-outer-name,unused-argument
    """Startup and shutdown events."""
    # Configure logging
    setup_logging()

    # Log security warnings
    if settings.DEBUG:
        logger.warning("DEBUG mode is ON - do not use in production")
    if settings.ALLOWED_ORIGINS == ["*"]:
        logger.warning("CORS allows all origins - not recommended for production")
    if settings.ALLOWED_HOSTS == ["*"]:
        logger.warning("TrustedHost allows all hosts - not recommended for production")

    # Startup
    logger.info("Starting %s v%s", settings.PROJECT_NAME, settings.APP_VERSION)
    logger.info("Connecting to database...")
    try:
        with engine.connect():
            logger.info("Database connection successful")
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Database connection failed: %s", e)
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")
    close_db()
    logger.info("Database connections closed")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="A comprehensive RESTful API for managing blog posts, comments, users, and categories",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
    swagger_ui_parameters={
        "filter": True,
    }
)

# Rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register exception handlers before middleware
register_exception_handlers(app)

# Middleware (added in reverse order of execution)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

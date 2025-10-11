from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routes import api_router
from app.core.config import settings

# from app.core.exceptions import ApplicationException


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=redefined-outer-name
    """Startup and shutdown events."""
    # Startup
    print(f"Starting {settings.PROJECT_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="A comprehensive RESTful API for managing blog posts, comments, users, and categories",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    swagger_ui_parameters={
        "filter": True,
    }
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_ORIGINS
)

# Exception handlers
# @app.exception_handler(ApplicationException)
# async def application_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content={"detail": str(exc)}
#     )

# Include API router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

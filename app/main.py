# app/main.py
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from core.config import settings
# from core.exceptions import ApplicationException
from api.v1.routes import auth, posts, comments, users, categories, health

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup y shutdown events"""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
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

# Routers
# app.include_router(health.router)
# app.include_router(auth.router)
# app.include_router(users.router)
# app.include_router(posts.router)
# app.include_router(comments.router)
# app.include_router(categories.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
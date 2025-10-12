from fastapi import APIRouter

from app.api.v1.routes import health

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(health.router, tags=["Health"])
# api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
# api_router.include_router(comments.router, prefix="/comments", tags=["Comments"])
# api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
# api_router.include_router(likes.router, prefix="/likes", tags=["Likes"])
# api_router.include_router(follow.router, prefix="/follow", tags=["Follow"])

__all__ = ["api_router"]

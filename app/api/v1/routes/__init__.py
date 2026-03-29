from fastapi import APIRouter

from app.api.v1.routes import auth, categories, comments, follow, health, likes, posts, users

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(categories.router, tags=["Categories"])
api_router.include_router(posts.router, tags=["Posts"])
api_router.include_router(comments.router, tags=["Comments"])
api_router.include_router(follow.router, tags=["Follow"])
api_router.include_router(likes.router, tags=["Likes"])

__all__ = ["api_router"]

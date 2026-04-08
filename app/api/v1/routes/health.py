from fastapi import APIRouter, status

from app.core.config import settings
from app.utils.dates import utc_now

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint
    Returns the API status and basic information
    """
    return {
        "status": "healthy",
        "message": "API is running successfully",
        "timestamp": utc_now().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """
    Simple ping endpoint
    """
    return {"ping": "pong"}

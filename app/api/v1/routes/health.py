from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.schemas.base import StatusSchema
from app.utils.dates import utc_now

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check(db: Session = Depends(get_db)) -> StatusSchema:
    """
    Health check endpoint.

    Returns the API status including database connectivity.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    overall = "healthy" if db_status == "connected" else "degraded"

    return StatusSchema(
        status=overall,
        message=f"{settings.PROJECT_NAME} v{settings.APP_VERSION}",
        timestamp=utc_now(),
        details={"database": db_status},
    )


@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """Simple ping endpoint."""
    return {"ping": "pong"}

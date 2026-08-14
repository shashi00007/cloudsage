"""
Health check endpoints for CloudSage application monitoring.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    app: str
    version: str
    environment: str
    timestamp: str
    message: str


@router.get("/health", response_model=HealthResponse)
async def get_health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Returns system health status and application metadata.
    """
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        message="CloudSage API is active and operational."
    )

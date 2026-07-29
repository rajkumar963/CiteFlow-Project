"""Health-check route.

This is the project's first API endpoint, used to confirm the FastAPI
service is running and correctly configured before later modules add the
search / summary / chat / history routes.
"""

import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check() -> HealthResponse:
    """Return service status, name, and version.

    Returns:
        HealthResponse: Basic liveness information for the API.
    """
    settings = get_settings()
    logger.debug("Health check requested")
    return HealthResponse(status="ok", app_name=settings.app_name, version="0.1.0")

"""Health / readiness endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings, get_settings
from app.schemas.common import HealthResponse

health_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.api_version,
        env=settings.app_env,
    )

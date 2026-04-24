"""Health check endpoints for InfraVersionHub."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from src.config import Settings, get_settings
from src.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str
    service: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    status: str
    timestamp: str
    version: str
    service: str
    checks: dict[str, Any]


class StorageHealthChecker:
    """Check storage backend health."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def check(self) -> dict[str, Any]:
        """Check storage backend connectivity."""
        from src.config import StorageBackend

        result = {"backend": self.settings.storage_backend.value, "status": "unknown"}

        try:
            if self.settings.storage_backend == StorageBackend.FILESYSTEM:
                import os

                data_path = self.settings.filesystem_data_path
                if os.path.exists(data_path) or os.access(
                    os.path.dirname(data_path) or ".", os.W_OK
                ):
                    result["status"] = "healthy"
                else:
                    result["status"] = "unhealthy"
                    result["error"] = "Data path not accessible"

            elif self.settings.storage_backend == StorageBackend.MONGODB:
                from motor.motor_asyncio import AsyncIOMotorClient

                client = AsyncIOMotorClient(
                    self.settings.mongodb_url, serverSelectionTimeoutMS=2000
                )
                await client.admin.command("ping")
                result["status"] = "healthy"
                client.close()

            else:
                result["status"] = "not_configured"

        except Exception as e:
            result["status"] = "unhealthy"
            result["error"] = str(e)
            logger.error(f"Storage health check failed: {e}")

        return result


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Basic health check to verify the service is running",
)
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """
    Liveness probe endpoint.

    Returns basic health status indicating the service is running.
    Used by Kubernetes liveness probes.
    """
    logger.debug("Health check requested")
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.app_version,
        service=settings.app_name,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Readiness check to verify the service can handle requests",
    responses={
        503: {
            "description": "Service not ready",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2026-01-13T10:00:00Z",
                        "version": "1.0.0",
                        "service": "InfraVersionHub",
                        "checks": {"storage": {"status": "unhealthy"}},
                    }
                }
            },
        }
    },
)
async def readiness_check(
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """
    Readiness probe endpoint.

    Checks connectivity to storage backend and other dependencies.
    Used by Kubernetes readiness probes.
    """
    logger.debug("Readiness check requested")

    # Check storage health
    storage_checker = StorageHealthChecker(settings)
    storage_health = await storage_checker.check()

    checks = {
        "storage": storage_health,
    }

    # Determine overall status
    all_healthy = all(
        check.get("status") == "healthy" for check in checks.values()
    )

    return ReadinessResponse(
        status="healthy" if all_healthy else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.app_version,
        service=settings.app_name,
        checks=checks,
    )

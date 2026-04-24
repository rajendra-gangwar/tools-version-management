"""Environment CRUD endpoints for InfraVersionHub."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.logging_config import get_logger
from src.schemas.common import PaginatedResponse, Pagination
from src.schemas.environment import (
    Environment,
    EnvironmentCreate,
    EnvironmentType,
    EnvironmentUpdate,
)
from src.storage import get_storage_connector
from src.storage.base import StorageConnector

logger = get_logger(__name__)

router = APIRouter(prefix="/environments", tags=["Environments"])

COLLECTION = "environments"


def get_storage() -> StorageConnector:
    """Dependency to get storage connector."""
    return get_storage_connector()


def _to_camel_case(data: dict) -> dict:
    """Convert snake_case keys to camelCase for storage."""
    result = {}
    for key, value in data.items():
        parts = key.split("_")
        camel_key = parts[0] + "".join(word.capitalize() for word in parts[1:])
        if isinstance(value, dict):
            result[camel_key] = _to_camel_case(value)
        elif isinstance(value, list):
            result[camel_key] = [
                _to_camel_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[camel_key] = value
    return result


def _to_snake_case(data: dict) -> dict:
    """Convert camelCase keys to snake_case for API response."""
    import re

    result = {}
    for key, value in data.items():
        snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
        if isinstance(value, dict):
            result[snake_key] = _to_snake_case(value)
        elif isinstance(value, list):
            result[snake_key] = [
                _to_snake_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[snake_key] = value
    return result


@router.get(
    "",
    response_model=PaginatedResponse[Environment],
    summary="List all environments",
)
async def list_environments(
    environment_type: Optional[EnvironmentType] = Query(None, description="Filter by type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    storage: StorageConnector = Depends(get_storage),
) -> PaginatedResponse[Environment]:
    """List all environments with optional filtering."""
    logger.info(
        "Listing environments",
        extra={"environment_type": environment_type, "is_active": is_active},
    )

    filters = {}
    if environment_type:
        filters["environmentType"] = environment_type.value
    if is_active is not None:
        filters["isActive"] = is_active

    if search:
        result = await storage.search(COLLECTION, search)
    else:
        result = await storage.list(
            COLLECTION,
            filters=filters if filters else None,
            sort_by="name",
            sort_order="asc",
            limit=limit,
            offset=offset,
        )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    environments = [
        Environment(**_to_snake_case(item)) for item in (result.data or [])
    ]

    total = result.metadata.get("total", len(environments))

    return PaginatedResponse(
        data=environments,
        pagination=Pagination.from_params(total=total, limit=limit, offset=offset),
    )


@router.post(
    "",
    response_model=Environment,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new environment",
)
async def create_environment(
    environment: EnvironmentCreate,
    storage: StorageConnector = Depends(get_storage),
) -> Environment:
    """Create a new environment."""
    logger.info(
        "Creating environment",
        extra={"environment_name": environment.name, "type": environment.environment_type},
    )

    # Check if environment with same name already exists
    existing = await storage.search(COLLECTION, environment.name, fields=["name"])
    if existing.success and existing.data:
        for item in existing.data:
            if item.get("name") == environment.name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Environment with name '{environment.name}' already exists",
                )

    data = _to_camel_case(environment.model_dump(exclude_none=True))
    result = await storage.save(COLLECTION, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return Environment(**_to_snake_case(result.data))


@router.get(
    "/{environment_id}",
    response_model=Environment,
    summary="Get a specific environment",
)
async def get_environment(
    environment_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> Environment:
    """Get a specific environment by ID."""
    result = await storage.load(COLLECTION, environment_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment {environment_id} not found",
        )

    return Environment(**_to_snake_case(result.data))


@router.put(
    "/{environment_id}",
    response_model=Environment,
    summary="Update an environment",
)
async def update_environment(
    environment_id: str,
    environment: EnvironmentUpdate,
    storage: StorageConnector = Depends(get_storage),
) -> Environment:
    """Update an existing environment."""
    logger.info(f"Updating environment {environment_id}")

    existing = await storage.load(COLLECTION, environment_id)
    if not existing.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment {environment_id} not found",
        )

    data = _to_camel_case(environment.model_dump(exclude_none=True))
    result = await storage.update(COLLECTION, environment_id, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return Environment(**_to_snake_case(result.data))


@router.delete(
    "/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an environment",
)
async def delete_environment(
    environment_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> None:
    """Delete an environment."""
    logger.info(f"Deleting environment {environment_id}")

    result = await storage.delete(COLLECTION, environment_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment {environment_id} not found",
        )

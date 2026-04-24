"""Component CRUD endpoints for InfraVersionHub."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.logging_config import get_logger
from src.schemas.common import PaginatedResponse, Pagination
from src.schemas.component import (
    Component,
    ComponentCreate,
    ComponentUpdate,
)
from src.storage import get_storage_connector
from src.storage.base import StorageConnector

logger = get_logger(__name__)

router = APIRouter(prefix="/components", tags=["Components"])

COLLECTION = "components"


def get_storage() -> StorageConnector:
    """Dependency to get storage connector."""
    return get_storage_connector()


def _to_camel_case(data: dict) -> dict:
    """Convert snake_case keys to camelCase for storage."""
    result = {}
    for key, value in data.items():
        # Convert snake_case to camelCase
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
        # Convert camelCase to snake_case
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
    response_model=PaginatedResponse[Component],
    summary="List all infrastructure components",
)
async def list_components(
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[list[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Full-text search query"),
    sort_by: str = Query("name", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    storage: StorageConnector = Depends(get_storage),
) -> PaginatedResponse[Component]:
    """
    List all infrastructure components with optional filtering and pagination.
    """
    logger.info(
        "Listing components",
        extra={"category": category, "search": search, "limit": limit, "offset": offset},
    )

    # Build filters
    filters = {}
    if category:
        filters["category"] = category
    if tags:
        # For tags, we need to match any of the provided tags
        # This is handled differently by each storage backend
        filters["tags"] = tags

    # Handle search vs list
    if search:
        result = await storage.search(COLLECTION, search)
    else:
        result = await storage.list(
            COLLECTION,
            filters=filters if filters else None,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    # Convert data to Component models
    components = [
        Component(**_to_snake_case(item)) for item in (result.data or [])
    ]

    total = result.metadata.get("total", len(components))

    return PaginatedResponse(
        data=components,
        pagination=Pagination.from_params(total=total, limit=limit, offset=offset),
    )


@router.post(
    "",
    response_model=Component,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new infrastructure component",
)
async def create_component(
    component: ComponentCreate,
    storage: StorageConnector = Depends(get_storage),
) -> Component:
    """
    Create a new infrastructure component in the registry.
    """
    logger.info(
        "Creating component",
        extra={"component_name": component.name, "category": component.category},
    )

    # Check if component with same name already exists
    existing = await storage.search(COLLECTION, component.name, fields=["name"])
    if existing.success and existing.data:
        for item in existing.data:
            if item.get("name") == component.name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Component with name '{component.name}' already exists",
                )

    # Convert to storage format (camelCase)
    data = _to_camel_case(component.model_dump(exclude_none=True))

    result = await storage.save(COLLECTION, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return Component(**_to_snake_case(result.data))


@router.get(
    "/{component_id}",
    response_model=Component,
    summary="Get a specific component",
)
async def get_component(
    component_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> Component:
    """
    Get a specific infrastructure component by ID.
    """
    logger.debug(f"Getting component {component_id}")

    result = await storage.load(COLLECTION, component_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found",
        )

    return Component(**_to_snake_case(result.data))


@router.put(
    "/{component_id}",
    response_model=Component,
    summary="Update a component",
)
async def update_component(
    component_id: str,
    component: ComponentUpdate,
    storage: StorageConnector = Depends(get_storage),
) -> Component:
    """
    Update an existing infrastructure component.
    """
    logger.info(f"Updating component {component_id}")

    # Check if component exists
    existing = await storage.load(COLLECTION, component_id)
    if not existing.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found",
        )

    # Convert to storage format, excluding None values
    data = _to_camel_case(component.model_dump(exclude_none=True))

    result = await storage.update(COLLECTION, component_id, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return Component(**_to_snake_case(result.data))


@router.delete(
    "/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a component",
)
async def delete_component(
    component_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> None:
    """
    Delete an infrastructure component.
    """
    logger.info(f"Deleting component {component_id}")

    result = await storage.delete(COLLECTION, component_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found",
        )


@router.get(
    "/{component_id}/versions",
    summary="Get version history for a component",
)
async def get_component_versions(
    component_id: str,
    limit: int = Query(20, ge=1, le=100),
    storage: StorageConnector = Depends(get_storage),
) -> list[dict]:
    """
    Get the version history for a specific component.
    """
    logger.debug(f"Getting version history for component {component_id}")

    # Check if component exists
    existing = await storage.load(COLLECTION, component_id)
    if not existing.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found",
        )

    # Get changelog from component
    component_data = existing.data
    changelog = component_data.get("changelog", [])

    # Return limited changelog entries
    return changelog[:limit]

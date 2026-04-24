"""Category CRUD endpoints for InfraVersionHub."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.logging_config import get_logger
from src.schemas.common import PaginatedResponse, Pagination
from src.schemas.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
)
from src.schemas.component import DEFAULT_CATEGORIES
from src.storage import get_storage_connector
from src.storage.base import StorageConnector

logger = get_logger(__name__)

router = APIRouter(prefix="/categories", tags=["Categories"])

COLLECTION = "categories"


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
    response_model=PaginatedResponse[Category],
    summary="List all categories",
)
async def list_categories(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    storage: StorageConnector = Depends(get_storage),
) -> PaginatedResponse[Category]:
    """List all categories with optional filtering."""
    logger.info(
        "Listing categories",
        extra={"is_active": is_active},
    )

    filters = {}
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

    categories = [
        Category(**_to_snake_case(item)) for item in (result.data or [])
    ]

    total = result.metadata.get("total", len(categories))

    return PaginatedResponse(
        data=categories,
        pagination=Pagination.from_params(total=total, limit=limit, offset=offset),
    )


@router.get(
    "/defaults",
    response_model=list[str],
    summary="Get default category names",
)
async def get_default_categories() -> list[str]:
    """Get the list of default category names."""
    return DEFAULT_CATEGORIES


@router.post(
    "",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
)
async def create_category(
    category: CategoryCreate,
    storage: StorageConnector = Depends(get_storage),
) -> Category:
    """Create a new category."""
    logger.info(
        "Creating category",
        extra={"category_name": category.name},
    )

    # Check if category with same name already exists
    existing = await storage.search(COLLECTION, category.name, fields=["name"])
    if existing.success and existing.data:
        for item in existing.data:
            if item.get("name") == category.name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Category with name '{category.name}' already exists",
                )

    data = _to_camel_case(category.model_dump(exclude_none=True))
    result = await storage.save(COLLECTION, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return Category(**_to_snake_case(result.data))


@router.get(
    "/{category_id}",
    response_model=Category,
    summary="Get a specific category",
)
async def get_category(
    category_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> Category:
    """Get a specific category by ID."""
    result = await storage.load(COLLECTION, category_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    return Category(**_to_snake_case(result.data))


@router.put(
    "/{category_id}",
    response_model=Category,
    summary="Update a category",
)
async def update_category(
    category_id: str,
    category: CategoryUpdate,
    storage: StorageConnector = Depends(get_storage),
) -> Category:
    """Update an existing category."""
    logger.info(f"Updating category {category_id}")

    existing = await storage.load(COLLECTION, category_id)
    if not existing.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )

    data = _to_camel_case(category.model_dump(exclude_none=True))
    result = await storage.update(COLLECTION, category_id, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return Category(**_to_snake_case(result.data))


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
)
async def delete_category(
    category_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> None:
    """Delete a category."""
    logger.info(f"Deleting category {category_id}")

    result = await storage.delete(COLLECTION, category_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )


@router.post(
    "/seed-defaults",
    response_model=list[Category],
    status_code=status.HTTP_201_CREATED,
    summary="Seed default categories",
)
async def seed_default_categories(
    storage: StorageConnector = Depends(get_storage),
) -> list[Category]:
    """Seed the database with default categories if they don't exist."""
    logger.info("Seeding default categories")

    created_categories = []

    for cat_name in DEFAULT_CATEGORIES:
        # Check if already exists
        existing = await storage.search(COLLECTION, cat_name, fields=["name"])
        if existing.success and existing.data:
            exists = any(item.get("name") == cat_name for item in existing.data)
            if exists:
                continue

        # Create the category
        display_name = cat_name.replace("-", " ").title()
        data = {
            "name": cat_name,
            "displayName": display_name,
            "description": f"Components in the {display_name} category",
            "isActive": True,
        }

        result = await storage.save(COLLECTION, data)
        if result.success:
            created_categories.append(Category(**_to_snake_case(result.data)))

    logger.info(f"Seeded {len(created_categories)} default categories")
    return created_categories

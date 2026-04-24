"""Pydantic schemas for InfraVersionHub."""

from src.schemas.common import Pagination, PaginatedResponse
from src.schemas.component import (
    Component,
    ComponentCreate,
    ComponentUpdate,
    OwnerTeam,
    VersionThresholds,
    DEFAULT_CATEGORIES,
)
from src.schemas.mapping import (
    EnvironmentMapping,
    MappingCreate,
    MappingUpdate,
    BulkMappingCreate,
    HealthStatus,
    UpgradeStatus,
    EnvironmentMatrix,
)
from src.schemas.environment import (
    Environment,
    EnvironmentCreate,
    EnvironmentUpdate,
    EnvironmentType,
    CloudProvider,
)
from src.schemas.category import (
    Category,
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
)

__all__ = [
    # Common
    "Pagination",
    "PaginatedResponse",
    # Component
    "Component",
    "ComponentCreate",
    "ComponentUpdate",
    "OwnerTeam",
    "VersionThresholds",
    "DEFAULT_CATEGORIES",
    # Mapping
    "EnvironmentMapping",
    "MappingCreate",
    "MappingUpdate",
    "BulkMappingCreate",
    "HealthStatus",
    "UpgradeStatus",
    "EnvironmentMatrix",
    # Environment
    "Environment",
    "EnvironmentCreate",
    "EnvironmentUpdate",
    "EnvironmentType",
    "CloudProvider",
    # Category
    "Category",
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
]

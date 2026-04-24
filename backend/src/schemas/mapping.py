"""Pydantic schemas for environment mappings."""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthStatus(str, Enum):
    """Health status states."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MappingBase(BaseModel):
    """Base schema for mapping fields."""

    component_id: str = Field(..., description="Reference to the infrastructure component")
    component_version: str = Field(..., description="Deployed version (semver)")
    environment_id: str = Field(..., description="Reference to the environment")
    namespace: Optional[str] = Field(
        None, max_length=100, description="Kubernetes namespace"
    )
    health_status: HealthStatus = Field(
        default=HealthStatus.HEALTHY, description="Current health status"
    )
    notes: Optional[str] = Field(
        None, max_length=5000, description="Additional notes"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("component_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format (semver-like)."""
        pattern = r"^v?\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid version format: {v}. Expected semver format."
            )
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class MappingCreate(MappingBase):
    """Schema for creating a new environment mapping."""
    pass


class BulkMappingCreate(BaseModel):
    """Schema for creating mappings for multiple environments at once."""

    component_id: str = Field(..., description="Reference to the infrastructure component")
    component_version: str = Field(..., description="Deployed version (semver)")
    environment_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of environment IDs to create mappings for"
    )
    namespace: Optional[str] = Field(
        None, max_length=100, description="Kubernetes namespace"
    )
    health_status: HealthStatus = Field(
        default=HealthStatus.HEALTHY, description="Current health status"
    )
    notes: Optional[str] = Field(
        None, max_length=5000, description="Additional notes"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("component_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format (semver-like)."""
        pattern = r"^v?\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid version format: {v}. Expected semver format."
            )
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class MappingUpdate(BaseModel):
    """Schema for updating an existing mapping."""

    component_version: Optional[str] = None
    environment_id: Optional[str] = None
    namespace: Optional[str] = Field(None, max_length=100)
    health_status: Optional[HealthStatus] = None
    notes: Optional[str] = Field(None, max_length=5000)
    metadata: Optional[dict[str, Any]] = None

    @field_validator("component_version")
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate version format if provided."""
        if v is None:
            return v
        pattern = r"^v?\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid version format: {v}")
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class EnvironmentMapping(MappingBase):
    """Full environment mapping schema including system-generated fields."""

    id: str = Field(..., description="Unique mapping identifier")
    component_name: Optional[str] = Field(
        None, description="Denormalized component name"
    )
    environment_name: Optional[str] = Field(
        None, description="Denormalized environment name"
    )
    cluster_name: Optional[str] = Field(
        None, description="Denormalized cluster name from environment"
    )
    region: Optional[str] = Field(
        None, description="Denormalized region from environment"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
    )


class UpgradeStatus(str, Enum):
    """Upgrade status based on version comparison."""

    UP_TO_DATE = "up_to_date"  # Green - current or within acceptable range
    UPGRADE_RECOMMENDED = "upgrade_recommended"  # Yellow - behind but not critical
    CRITICAL_UPGRADE = "critical_upgrade"  # Red - significantly behind
    UNKNOWN = "unknown"  # No latest version defined


class EnvironmentMatrixCell(BaseModel):
    """A single cell in the environment matrix view."""

    component_id: str
    component_name: str
    version: Optional[str] = None
    health: Optional[HealthStatus] = None


class EnvironmentMatrix(BaseModel):
    """Matrix view of components across environments."""

    environments: list[str] = Field(..., description="List of environment names")
    components: list[dict[str, Any]] = Field(
        ..., description="Components with versions per environment including latest_version and upgrade_status"
    )

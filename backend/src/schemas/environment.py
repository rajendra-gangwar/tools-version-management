"""Pydantic schemas for environments."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentType(str, Enum):
    """Types of environments."""

    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"
    SANDBOX = "sandbox"


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ON_PREMISE = "on-premise"
    OTHER = "other"


class EnvironmentBase(BaseModel):
    """Base schema for environment fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Environment name (e.g., dev-eks-1, prod-us-east-1)",
    )
    display_name: Optional[str] = Field(
        None, max_length=200, description="Human-readable display name"
    )
    environment_type: EnvironmentType = Field(
        ..., description="Type of environment"
    )
    cloud_provider: CloudProvider = Field(
        CloudProvider.AWS, description="Cloud provider"
    )
    region: str = Field(
        ..., min_length=1, max_length=50, description="Region (e.g., us-east-1)"
    )
    cluster_name: Optional[str] = Field(
        None, max_length=100, description="Kubernetes cluster name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Environment description"
    )
    is_active: bool = Field(True, description="Whether environment is active")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class EnvironmentCreate(EnvironmentBase):
    """Schema for creating a new environment."""
    pass


class EnvironmentUpdate(BaseModel):
    """Schema for updating an existing environment."""

    display_name: Optional[str] = Field(None, max_length=200)
    environment_type: Optional[EnvironmentType] = None
    cloud_provider: Optional[CloudProvider] = None
    region: Optional[str] = Field(None, max_length=50)
    cluster_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )


class Environment(EnvironmentBase):
    """Full environment schema including system-generated fields."""

    id: str = Field(..., description="Unique environment identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
    )

"""Pydantic schemas for infrastructure components."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class OwnerTeam(BaseModel):
    """Team ownership information."""

    name: str = Field(..., min_length=1, max_length=100, description="Team name")
    email: Optional[str] = Field(None, description="Team email address")
    slack_channel: Optional[str] = Field(None, description="Slack channel")


class Repository(BaseModel):
    """Repository information."""

    url: Optional[str] = Field(None, description="Repository URL")
    type: Optional[str] = Field(None, description="Repository type (github, gitlab, etc.)")


class Documentation(BaseModel):
    """Documentation links."""

    url: Optional[str] = Field(None, description="Documentation URL")
    changelog_url: Optional[str] = Field(None, description="Changelog URL")


class CompatibilityNotes(BaseModel):
    """Compatibility information for a component."""

    min_kubernetes_version: Optional[str] = Field(None, description="Minimum K8s version")
    max_kubernetes_version: Optional[str] = Field(None, description="Maximum K8s version")
    dependencies: list[dict[str, Any]] = Field(
        default_factory=list, description="Component dependencies"
    )
    breaking_changes: list[str] = Field(
        default_factory=list, description="Breaking changes"
    )


class VersionThresholds(BaseModel):
    """Thresholds for version upgrade recommendations in major.minor.patch format.

    Example: 1.2.5 means allow 1 major, 2 minor, 5 patch versions behind before warning.
    """

    major_versions_behind: int = Field(
        default=1,
        ge=0,
        description="Number of major versions behind allowed before critical status"
    )
    minor_versions_behind: int = Field(
        default=2,
        ge=0,
        description="Number of minor versions behind allowed before warning status"
    )
    patch_versions_behind: int = Field(
        default=5,
        ge=0,
        description="Number of patch versions behind allowed (informational)"
    )


# Default categories - can be extended dynamically
DEFAULT_CATEGORIES = [
    "orchestration",
    "monitoring",
    "logging",
    "networking",
    "security",
    "storage",
    "ci-cd",
    "service-mesh",
    "other",
]


class ComponentBase(BaseModel):
    """Base schema for component fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z0-9-_]+$",
        description="Component name (alphanumeric, hyphens, underscores)",
    )
    display_name: Optional[str] = Field(
        None, max_length=200, description="Human-readable display name"
    )
    category: str = Field(..., description="Component category")
    description: Optional[str] = Field(
        None, max_length=2000, description="Component description"
    )
    latest_version: Optional[str] = Field(
        None,
        description="Latest available version of the component (semver format)"
    )
    version_thresholds: Optional[VersionThresholds] = Field(
        None,
        description="Thresholds for upgrade recommendations (major.minor.patch format)"
    )
    compatibility_notes: Optional[CompatibilityNotes] = Field(
        None, description="Compatibility information"
    )
    owner_team: Optional[OwnerTeam] = Field(None, description="Owning team information (optional)")
    repository: Optional[Repository] = Field(None, description="Repository info")
    documentation: Optional[Documentation] = Field(None, description="Documentation links")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class ComponentCreate(ComponentBase):
    """Schema for creating a new component."""
    pass


class ComponentUpdate(BaseModel):
    """Schema for updating an existing component."""

    display_name: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    latest_version: Optional[str] = Field(None, description="Latest available version")
    version_thresholds: Optional[VersionThresholds] = None
    compatibility_notes: Optional[CompatibilityNotes] = None
    owner_team: Optional[OwnerTeam] = None
    repository: Optional[Repository] = None
    documentation: Optional[Documentation] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class Component(ComponentBase):
    """Full component schema including system-generated fields."""

    id: str = Field(..., description="Unique component identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Creator user ID")
    updated_by: Optional[str] = Field(None, description="Last updater user ID")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

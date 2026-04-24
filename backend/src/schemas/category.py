"""Pydantic schemas for component categories."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base schema for category fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-zA-Z0-9-]+$",
        description="Category identifier (lowercase, hyphens allowed)",
    )
    display_name: Optional[str] = Field(
        None, max_length=100, description="Human-readable display name"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Category description"
    )
    color: Optional[str] = Field(
        None,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Hex color code for UI display"
    )
    is_active: bool = Field(default=True, description="Whether category is active")

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""

    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class Category(CategoryBase):
    """Full category schema including system-generated fields."""

    id: str = Field(..., description="Unique category identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        populate_by_name=True,
    )

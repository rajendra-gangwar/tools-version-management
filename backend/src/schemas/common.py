"""Common Pydantic schemas used across the application."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    """Pagination information for list responses."""

    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Maximum records per page")
    offset: int = Field(..., description="Number of records skipped")
    has_more: bool = Field(..., description="Whether more records exist")

    @classmethod
    def from_params(cls, total: int, limit: int, offset: int) -> "Pagination":
        """Create pagination from parameters."""
        return cls(
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + limit < total,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    data: list[T] = Field(..., description="List of items")
    pagination: Pagination = Field(..., description="Pagination information")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = Field(True, description="Operation success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Any] = Field(None, description="Response data")

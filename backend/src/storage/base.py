"""Abstract base class for storage connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StorageResult:
    """Result wrapper for storage operations."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, **metadata: Any) -> "StorageResult":
        """Create a successful result."""
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, **metadata: Any) -> "StorageResult":
        """Create a failed result."""
        return cls(success=False, error=error, metadata=metadata)


class StorageConnector(ABC):
    """
    Abstract base class for all storage connectors.

    All storage backends must implement these methods to provide
    a consistent interface for data operations.
    """

    @abstractmethod
    async def initialize(self) -> StorageResult:
        """
        Initialize the storage connection and create necessary structures.

        Returns:
            StorageResult indicating success or failure
        """
        pass

    @abstractmethod
    async def save(self, collection: str, data: dict[str, Any]) -> StorageResult:
        """
        Save a new record to the specified collection.

        Args:
            collection: Name of the collection (e.g., 'components', 'mappings')
            data: Dictionary containing the record data

        Returns:
            StorageResult with the saved record including generated ID
        """
        pass

    @abstractmethod
    async def load(self, collection: str, id: str) -> StorageResult:
        """
        Load a single record by ID.

        Args:
            collection: Name of the collection
            id: Unique identifier of the record

        Returns:
            StorageResult with the record data or error if not found
        """
        pass

    @abstractmethod
    async def update(
        self, collection: str, id: str, data: dict[str, Any]
    ) -> StorageResult:
        """
        Update an existing record.

        Args:
            collection: Name of the collection
            id: Unique identifier of the record to update
            data: Dictionary containing the fields to update

        Returns:
            StorageResult with the updated record
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, id: str) -> StorageResult:
        """
        Delete a record by ID.

        Args:
            collection: Name of the collection
            id: Unique identifier of the record to delete

        Returns:
            StorageResult indicating success or failure
        """
        pass

    @abstractmethod
    async def list(
        self,
        collection: str,
        filters: Optional[dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> StorageResult:
        """
        List records with optional filtering and pagination.

        Args:
            collection: Name of the collection
            filters: Dictionary of field-value pairs to filter by
            sort_by: Field name to sort by
            sort_order: 'asc' or 'desc'
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            StorageResult with list of records and total count in metadata
        """
        pass

    @abstractmethod
    async def search(
        self,
        collection: str,
        query: str,
        fields: Optional[list[str]] = None,
    ) -> StorageResult:
        """
        Full-text search across records.

        Args:
            collection: Name of the collection
            query: Search query string
            fields: Optional list of fields to search in

        Returns:
            StorageResult with matching records
        """
        pass

    @abstractmethod
    async def health_check(self) -> StorageResult:
        """
        Check the health/connectivity of the storage backend.

        Returns:
            StorageResult indicating health status
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up and close connections."""
        pass

    async def count(
        self, collection: str, filters: Optional[dict[str, Any]] = None
    ) -> StorageResult:
        """
        Count records in a collection with optional filters.

        Default implementation uses list() - can be overridden for efficiency.

        Args:
            collection: Name of the collection
            filters: Optional filters to apply

        Returns:
            StorageResult with count in data
        """
        result = await self.list(collection, filters=filters, limit=0)
        if result.success:
            return StorageResult.ok(
                data=result.metadata.get("total", 0),
                collection=collection,
            )
        return result

    async def exists(self, collection: str, id: str) -> StorageResult:
        """
        Check if a record exists.

        Default implementation uses load() - can be overridden for efficiency.

        Args:
            collection: Name of the collection
            id: Record ID to check

        Returns:
            StorageResult with boolean in data
        """
        result = await self.load(collection, id)
        return StorageResult.ok(data=result.success)

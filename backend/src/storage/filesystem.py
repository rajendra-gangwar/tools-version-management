"""Filesystem storage connector using JSON files."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

import aiofiles
import aiofiles.os

from src.logging_config import get_logger
from src.storage.base import StorageConnector, StorageResult

logger = get_logger(__name__)


class FilesystemConnector(StorageConnector):
    """
    Storage connector that persists data as JSON files on the filesystem.

    Directory Structure:
        {data_path}/
        ├── components/
        │   ├── index.json          # Index of all components
        │   └── by-id/
        │       ├── {uuid}.json     # Individual component files
        │       └── ...
        ├── mappings/
        │   ├── index.json
        │   └── by-id/
        │       └── {uuid}.json
        ├── audit/
        │   └── audit.jsonl         # Append-only audit log
        └── history/
            └── {collection}/
                └── {id}/
                    └── v{n}.json   # Version history
    """

    def __init__(self, data_path: str = "./data"):
        self.data_path = Path(data_path)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a given key."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def _get_collection_path(self, collection: str) -> Path:
        """Get the path for a collection directory."""
        return self.data_path / collection

    def _get_index_path(self, collection: str) -> Path:
        """Get the path for a collection's index file."""
        return self._get_collection_path(collection) / "index.json"

    def _get_record_path(self, collection: str, id: str) -> Path:
        """Get the path for an individual record file."""
        return self._get_collection_path(collection) / "by-id" / f"{id}.json"

    async def _ensure_directory(self, path: Path) -> None:
        """Ensure a directory exists."""
        await aiofiles.os.makedirs(path, exist_ok=True)

    async def _read_json(self, path: Path) -> Optional[Any]:
        """Read and parse a JSON file."""
        try:
            if not await aiofiles.os.path.exists(path):
                return None
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
                return json.loads(content) if content else None
        except Exception as e:
            logger.error(f"Error reading JSON file {path}: {e}")
            return None

    async def _write_json(self, path: Path, data: Any) -> bool:
        """Write data to a JSON file."""
        try:
            await self._ensure_directory(path.parent)
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2, default=str))
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file {path}: {e}")
            return False

    async def _load_index(self, collection: str) -> dict[str, Any]:
        """Load the index for a collection."""
        index_path = self._get_index_path(collection)
        index = await self._read_json(index_path)
        return index if index else {"items": {}, "updated_at": None}

    async def _save_index(self, collection: str, index: dict[str, Any]) -> bool:
        """Save the index for a collection."""
        index["updated_at"] = datetime.now(timezone.utc).isoformat()
        return await self._write_json(self._get_index_path(collection), index)

    async def initialize(self) -> StorageResult:
        """Initialize the filesystem storage structure."""
        try:
            # Create base directories
            for collection in ["components", "mappings", "audit", "history"]:
                await self._ensure_directory(self._get_collection_path(collection))
                if collection in ["components", "mappings"]:
                    await self._ensure_directory(
                        self._get_collection_path(collection) / "by-id"
                    )
                    # Initialize index if it doesn't exist
                    index_path = self._get_index_path(collection)
                    if not await aiofiles.os.path.exists(index_path):
                        await self._save_index(collection, {"items": {}})

            logger.info(f"Filesystem storage initialized at {self.data_path}")
            return StorageResult.ok(data_path=str(self.data_path))

        except Exception as e:
            logger.error(f"Failed to initialize filesystem storage: {e}")
            return StorageResult.fail(str(e))

    async def save(self, collection: str, data: dict[str, Any]) -> StorageResult:
        """Save a new record to the collection."""
        lock = self._get_lock(f"{collection}:write")
        async with lock:
            try:
                # Generate ID if not provided
                record_id = data.get("id") or str(uuid4())
                data["id"] = record_id

                # Add timestamps
                now = datetime.now(timezone.utc).isoformat()
                data["createdAt"] = data.get("createdAt") or now
                data["updatedAt"] = now

                # Save the record file
                record_path = self._get_record_path(collection, record_id)
                if not await self._write_json(record_path, data):
                    return StorageResult.fail("Failed to write record file")

                # Update the index
                index = await self._load_index(collection)
                index["items"][record_id] = {
                    "id": record_id,
                    "name": data.get("name"),
                    "updatedAt": now,
                }
                if not await self._save_index(collection, index):
                    return StorageResult.fail("Failed to update index")

                logger.info(f"Saved record {record_id} to {collection}")
                return StorageResult.ok(data=data, id=record_id)

            except Exception as e:
                logger.error(f"Error saving record to {collection}: {e}")
                return StorageResult.fail(str(e))

    async def load(self, collection: str, id: str) -> StorageResult:
        """Load a single record by ID."""
        try:
            record_path = self._get_record_path(collection, id)
            data = await self._read_json(record_path)

            if data is None:
                return StorageResult.fail(f"Record {id} not found in {collection}")

            return StorageResult.ok(data=data)

        except Exception as e:
            logger.error(f"Error loading record {id} from {collection}: {e}")
            return StorageResult.fail(str(e))

    async def update(
        self, collection: str, id: str, data: dict[str, Any]
    ) -> StorageResult:
        """Update an existing record."""
        lock = self._get_lock(f"{collection}:write")
        async with lock:
            try:
                # Load existing record
                existing_result = await self.load(collection, id)
                if not existing_result.success:
                    return existing_result

                existing_data = existing_result.data

                # Save version history before update
                await self._save_history(collection, id, existing_data)

                # Merge data
                updated_data = {**existing_data, **data}
                updated_data["id"] = id  # Ensure ID doesn't change
                updated_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

                # Save updated record
                record_path = self._get_record_path(collection, id)
                if not await self._write_json(record_path, updated_data):
                    return StorageResult.fail("Failed to write updated record")

                # Update index
                index = await self._load_index(collection)
                if id in index["items"]:
                    index["items"][id]["updatedAt"] = updated_data["updatedAt"]
                    index["items"][id]["name"] = updated_data.get("name")
                    await self._save_index(collection, index)

                logger.info(f"Updated record {id} in {collection}")
                return StorageResult.ok(data=updated_data)

            except Exception as e:
                logger.error(f"Error updating record {id} in {collection}: {e}")
                return StorageResult.fail(str(e))

    async def _save_history(
        self, collection: str, id: str, data: dict[str, Any]
    ) -> None:
        """Save a version to history."""
        try:
            history_dir = self.data_path / "history" / collection / id
            await self._ensure_directory(history_dir)

            # Find next version number
            version = 1
            async for entry in aiofiles.os.scandir(history_dir):
                if entry.name.startswith("v") and entry.name.endswith(".json"):
                    try:
                        v = int(entry.name[1:-5])
                        version = max(version, v + 1)
                    except ValueError:
                        pass

            # Save version
            version_path = history_dir / f"v{version}.json"
            version_data = {
                "version": version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": data,
            }
            await self._write_json(version_path, version_data)

        except Exception as e:
            logger.warning(f"Failed to save history for {collection}/{id}: {e}")

    async def delete(self, collection: str, id: str) -> StorageResult:
        """Delete a record by ID."""
        lock = self._get_lock(f"{collection}:write")
        async with lock:
            try:
                record_path = self._get_record_path(collection, id)

                if not await aiofiles.os.path.exists(record_path):
                    return StorageResult.fail(f"Record {id} not found in {collection}")

                # Remove the record file
                await aiofiles.os.remove(record_path)

                # Update the index
                index = await self._load_index(collection)
                if id in index["items"]:
                    del index["items"][id]
                    await self._save_index(collection, index)

                logger.info(f"Deleted record {id} from {collection}")
                return StorageResult.ok(id=id)

            except Exception as e:
                logger.error(f"Error deleting record {id} from {collection}: {e}")
                return StorageResult.fail(str(e))

    async def list(
        self,
        collection: str,
        filters: Optional[dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> StorageResult:
        """List records with optional filtering and pagination."""
        try:
            # Load all records from the by-id directory
            by_id_path = self._get_collection_path(collection) / "by-id"

            if not await aiofiles.os.path.exists(by_id_path):
                return StorageResult.ok(data=[], total=0)

            records = []
            async for entry in aiofiles.os.scandir(by_id_path):
                if entry.name.endswith(".json"):
                    record = await self._read_json(Path(entry.path))
                    if record:
                        records.append(record)

            # Apply filters
            if filters:
                records = self._apply_filters(records, filters)

            total = len(records)

            # Apply sorting
            if sort_by:
                reverse = sort_order.lower() == "desc"
                records.sort(
                    key=lambda x: x.get(sort_by, "") or "",
                    reverse=reverse,
                )

            # Apply pagination
            records = records[offset : offset + limit] if limit > 0 else records[offset:]

            return StorageResult.ok(data=records, total=total, limit=limit, offset=offset)

        except Exception as e:
            logger.error(f"Error listing records from {collection}: {e}")
            return StorageResult.fail(str(e))

    def _apply_filters(
        self, records: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply filters to a list of records."""
        filtered = []
        for record in records:
            match = True
            for key, value in filters.items():
                record_value = record.get(key)
                if isinstance(value, list):
                    # Check if record value is in the filter list
                    if record_value not in value:
                        match = False
                        break
                elif record_value != value:
                    match = False
                    break
            if match:
                filtered.append(record)
        return filtered

    async def search(
        self,
        collection: str,
        query: str,
        fields: Optional[list[str]] = None,
    ) -> StorageResult:
        """Full-text search across records."""
        try:
            # Get all records
            result = await self.list(collection, limit=0)
            if not result.success:
                return result

            records = result.data or []
            query_lower = query.lower()
            search_fields = fields or ["name", "displayName", "description", "tags"]

            matches = []
            for record in records:
                for field in search_fields:
                    value = record.get(field)
                    if value is None:
                        continue

                    # Handle different value types
                    if isinstance(value, str):
                        if query_lower in value.lower():
                            matches.append(record)
                            break
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and query_lower in item.lower():
                                matches.append(record)
                                break

            return StorageResult.ok(data=matches, total=len(matches), query=query)

        except Exception as e:
            logger.error(f"Error searching in {collection}: {e}")
            return StorageResult.fail(str(e))

    async def health_check(self) -> StorageResult:
        """Check filesystem storage health."""
        try:
            # Check if data path exists and is writable
            if not await aiofiles.os.path.exists(self.data_path):
                return StorageResult.fail("Data path does not exist")

            # Try to write a test file
            test_path = self.data_path / ".health_check"
            async with aiofiles.open(test_path, "w") as f:
                await f.write(datetime.now(timezone.utc).isoformat())
            await aiofiles.os.remove(test_path)

            return StorageResult.ok(
                status="healthy",
                data_path=str(self.data_path),
            )

        except Exception as e:
            logger.error(f"Filesystem health check failed: {e}")
            return StorageResult.fail(str(e))

    async def close(self) -> None:
        """Clean up resources."""
        self._locks.clear()
        logger.info("Filesystem connector closed")

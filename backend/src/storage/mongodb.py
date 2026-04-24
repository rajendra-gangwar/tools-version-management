"""MongoDB storage connector."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.logging_config import get_logger
from src.storage.base import StorageConnector, StorageResult

logger = get_logger(__name__)


class MongoDBConnector(StorageConnector):
    """
    Storage connector using MongoDB as the backend.

    Collections:
        - components: Infrastructure component registry
        - mappings: Environment mappings
        - version_history: Version history for all entities
        - audit_logs: Audit log entries
    """

    def __init__(self, connection_url: str, database_name: str = "infraversionhub"):
        self.connection_url = connection_url
        self.database_name = database_name
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get the MongoDB client."""
        if self._client is None:
            raise RuntimeError("MongoDB client not initialized. Call initialize() first.")
        return self._client

    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get the database instance."""
        if self._db is None:
            raise RuntimeError("MongoDB database not initialized. Call initialize() first.")
        return self._db

    async def initialize(self) -> StorageResult:
        """Initialize MongoDB connection and create indexes."""
        try:
            self._client = AsyncIOMotorClient(self.connection_url)
            self._db = self._client[self.database_name]

            # Verify connection
            await self._client.admin.command("ping")

            # Create indexes for components collection
            components = self.db["components"]
            await components.create_index("name", unique=True)
            await components.create_index("category")
            await components.create_index("tags")
            await components.create_index(
                [("name", "text"), ("displayName", "text"), ("description", "text")]
            )

            # Create indexes for mappings collection
            mappings = self.db["mappings"]
            await mappings.create_index("componentId")
            await mappings.create_index("environmentName")
            await mappings.create_index("clusterName")
            await mappings.create_index(
                [("componentId", 1), ("clusterName", 1), ("namespace", 1)],
                unique=True,
            )

            # Create indexes for version_history collection
            history = self.db["version_history"]
            await history.create_index(
                [("entityType", 1), ("entityId", 1), ("versionNumber", -1)]
            )

            # Create indexes for audit_logs collection
            audit = self.db["audit_logs"]
            await audit.create_index([("timestamp", -1)])
            await audit.create_index("userId")
            await audit.create_index([("resourceType", 1), ("resourceId", 1)])

            logger.info(
                f"MongoDB initialized: {self.database_name}",
                extra={"database": self.database_name},
            )
            return StorageResult.ok(database=self.database_name)

        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            return StorageResult.fail(str(e))

    async def save(self, collection: str, data: dict[str, Any]) -> StorageResult:
        """Save a new record to the collection."""
        try:
            # Generate ID if not provided
            record_id = data.get("id") or str(uuid4())
            data["id"] = record_id

            # Add timestamps
            now = datetime.now(timezone.utc)
            data["createdAt"] = data.get("createdAt") or now
            data["updatedAt"] = now

            # Use id as _id for MongoDB
            mongo_doc = {**data, "_id": record_id}

            coll = self.db[collection]
            await coll.insert_one(mongo_doc)

            # Remove MongoDB _id from response
            del mongo_doc["_id"]

            logger.info(
                f"Saved record to MongoDB",
                extra={"collection": collection, "id": record_id},
            )
            return StorageResult.ok(data=mongo_doc, id=record_id)

        except Exception as e:
            logger.error(f"Error saving to MongoDB {collection}: {e}")
            return StorageResult.fail(str(e))

    async def load(self, collection: str, id: str) -> StorageResult:
        """Load a single record by ID."""
        try:
            coll = self.db[collection]
            doc = await coll.find_one({"_id": id})

            if doc is None:
                return StorageResult.fail(f"Record {id} not found in {collection}")

            # Remove MongoDB _id
            del doc["_id"]

            return StorageResult.ok(data=doc)

        except Exception as e:
            logger.error(f"Error loading from MongoDB {collection}/{id}: {e}")
            return StorageResult.fail(str(e))

    async def update(
        self, collection: str, id: str, data: dict[str, Any]
    ) -> StorageResult:
        """Update an existing record."""
        try:
            coll = self.db[collection]

            # Get existing document for history
            existing = await coll.find_one({"_id": id})
            if existing is None:
                return StorageResult.fail(f"Record {id} not found in {collection}")

            # Save to history
            await self._save_history(collection, id, existing)

            # Prepare update
            data["updatedAt"] = datetime.now(timezone.utc)

            # Don't allow changing the ID
            if "id" in data:
                del data["id"]

            # Update document
            result = await coll.update_one({"_id": id}, {"$set": data})

            if result.modified_count == 0:
                return StorageResult.fail("No changes made")

            # Get updated document
            updated = await coll.find_one({"_id": id})
            del updated["_id"]

            logger.info(
                f"Updated record in MongoDB",
                extra={"collection": collection, "id": id},
            )
            return StorageResult.ok(data=updated)

        except Exception as e:
            logger.error(f"Error updating MongoDB {collection}/{id}: {e}")
            return StorageResult.fail(str(e))

    async def _save_history(
        self, collection: str, id: str, data: dict[str, Any]
    ) -> None:
        """Save a version to history."""
        try:
            history_coll = self.db["version_history"]

            # Get the latest version number
            latest = await history_coll.find_one(
                {"entityType": collection, "entityId": id},
                sort=[("versionNumber", -1)],
            )
            version = (latest.get("versionNumber", 0) if latest else 0) + 1

            # Remove MongoDB _id from data copy
            data_copy = {k: v for k, v in data.items() if k != "_id"}

            history_entry = {
                "_id": f"{collection}:{id}:v{version}",
                "entityType": collection,
                "entityId": id,
                "versionNumber": version,
                "timestamp": datetime.now(timezone.utc),
                "data": data_copy,
            }

            await history_coll.insert_one(history_entry)

        except Exception as e:
            logger.warning(f"Failed to save history for {collection}/{id}: {e}")

    async def delete(self, collection: str, id: str) -> StorageResult:
        """Delete a record by ID."""
        try:
            coll = self.db[collection]
            result = await coll.delete_one({"_id": id})

            if result.deleted_count == 0:
                return StorageResult.fail(f"Record {id} not found in {collection}")

            logger.info(
                f"Deleted record from MongoDB",
                extra={"collection": collection, "id": id},
            )
            return StorageResult.ok(id=id)

        except Exception as e:
            logger.error(f"Error deleting from MongoDB {collection}/{id}: {e}")
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
            coll = self.db[collection]

            # Build query
            query = filters or {}

            # Get total count
            total = await coll.count_documents(query)

            # Build cursor
            cursor = coll.find(query)

            # Apply sorting
            if sort_by:
                direction = 1 if sort_order.lower() == "asc" else -1
                cursor = cursor.sort(sort_by, direction)

            # Apply pagination
            if offset > 0:
                cursor = cursor.skip(offset)
            if limit > 0:
                cursor = cursor.limit(limit)

            # Execute query
            docs = []
            async for doc in cursor:
                del doc["_id"]
                docs.append(doc)

            return StorageResult.ok(
                data=docs, total=total, limit=limit, offset=offset
            )

        except Exception as e:
            logger.error(f"Error listing from MongoDB {collection}: {e}")
            return StorageResult.fail(str(e))

    async def search(
        self,
        collection: str,
        query: str,
        fields: Optional[list[str]] = None,
    ) -> StorageResult:
        """Full-text search across records."""
        try:
            coll = self.db[collection]

            # Use MongoDB text search
            cursor = coll.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}},
            ).sort([("score", {"$meta": "textScore"})])

            docs = []
            async for doc in cursor:
                del doc["_id"]
                if "score" in doc:
                    del doc["score"]
                docs.append(doc)

            return StorageResult.ok(data=docs, total=len(docs), query=query)

        except Exception as e:
            # Fallback to regex search if text search fails
            logger.warning(f"Text search failed, falling back to regex: {e}")
            return await self._regex_search(collection, query, fields)

    async def _regex_search(
        self,
        collection: str,
        query: str,
        fields: Optional[list[str]] = None,
    ) -> StorageResult:
        """Fallback regex-based search."""
        try:
            coll = self.db[collection]
            search_fields = fields or ["name", "displayName", "description"]

            # Build $or query with regex
            or_conditions = [
                {field: {"$regex": query, "$options": "i"}} for field in search_fields
            ]

            cursor = coll.find({"$or": or_conditions})

            docs = []
            async for doc in cursor:
                del doc["_id"]
                docs.append(doc)

            return StorageResult.ok(data=docs, total=len(docs), query=query)

        except Exception as e:
            logger.error(f"Error in regex search: {e}")
            return StorageResult.fail(str(e))

    async def health_check(self) -> StorageResult:
        """Check MongoDB connection health."""
        try:
            await self.client.admin.command("ping")
            return StorageResult.ok(
                status="healthy",
                database=self.database_name,
            )

        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return StorageResult.fail(str(e))

    async def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")

"""Storage module for InfraVersionHub."""

from typing import Optional

from src.config import StorageBackend, get_settings
from src.storage.base import StorageConnector

_storage_instance: Optional[StorageConnector] = None


def get_storage_connector() -> StorageConnector:
    """
    Get the configured storage connector instance.

    Returns:
        StorageConnector instance based on configuration
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    settings = get_settings()

    if settings.storage_backend == StorageBackend.FILESYSTEM:
        from src.storage.filesystem import FilesystemConnector

        _storage_instance = FilesystemConnector(settings.filesystem_data_path)

    elif settings.storage_backend == StorageBackend.MONGODB:
        from src.storage.mongodb import MongoDBConnector

        _storage_instance = MongoDBConnector(
            settings.mongodb_url or "mongodb://localhost:27017",
            settings.mongodb_database,
        )

    elif settings.storage_backend == StorageBackend.POSTGRESQL:
        raise NotImplementedError("PostgreSQL connector not yet implemented")

    elif settings.storage_backend == StorageBackend.GITHUB:
        raise NotImplementedError("GitHub connector not yet implemented")

    else:
        raise ValueError(f"Unknown storage backend: {settings.storage_backend}")

    return _storage_instance


async def reset_storage_connector() -> None:
    """Reset the storage connector instance (useful for testing)."""
    global _storage_instance
    if _storage_instance is not None:
        await _storage_instance.close()
        _storage_instance = None

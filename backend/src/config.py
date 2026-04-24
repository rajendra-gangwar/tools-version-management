"""Configuration management for InfraVersionHub."""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageBackend(str, Enum):
    """Supported storage backends."""

    FILESYSTEM = "filesystem"
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    GITHUB = "github"


class Environment(str, Enum):
    """Application environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_parse_none_str="null",
    )

    # Application settings
    app_name: str = "InfraVersionHub"
    app_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: str = "INFO"

    # API settings
    api_prefix: str = "/v1"
    cors_origins: str = Field(default="http://localhost:3000")

    # Storage settings
    storage_backend: StorageBackend = StorageBackend.FILESYSTEM

    # Filesystem storage settings
    filesystem_data_path: str = "./data"

    # MongoDB settings
    mongodb_url: Optional[str] = "mongodb://localhost:27017"
    mongodb_database: str = "infraversionhub"

    # PostgreSQL settings (for future use)
    database_url: Optional[str] = None

    # GitHub storage settings (for future use)
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    github_branch: str = "main"

    # JWT settings
    jwt_secret: str = Field(
        default="development-secret-change-in-production",
        description="Secret key for JWT encoding/decoding",
    )
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Redis settings (for caching)
    redis_url: Optional[str] = "redis://localhost:6379/0"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Cached Settings instance
    """
    return Settings()

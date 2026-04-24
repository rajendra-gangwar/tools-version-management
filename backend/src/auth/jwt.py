"""JWT authentication for InfraVersionHub."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.auth.rbac import RBACService, Role
from src.config import Settings, get_settings
from src.logging_config import get_logger

logger = get_logger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # User ID
    email: str
    name: str
    role: str
    permissions: list[str]
    exp: datetime
    iat: datetime
    iss: str = "infraversionhub"
    aud: str = "infraversionhub-api"


class AuthService:
    """Service for JWT authentication operations."""

    def __init__(self, settings: Settings):
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours

    def create_access_token(
        self,
        user_id: str,
        email: str,
        name: str,
        role: Role,
        additional_permissions: Optional[list[str]] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        Args:
            user_id: Unique user identifier
            email: User email address
            name: User display name
            role: User role
            additional_permissions: Any extra permissions beyond role
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token string
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=self.expiration_hours)

        # Get effective permissions from role and additional permissions
        permissions = RBACService.get_effective_permissions(
            role, additional_permissions
        )

        payload = {
            "sub": user_id,
            "email": email,
            "name": name,
            "role": role.value,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "iss": "infraversionhub",
            "aud": "infraversionhub-api",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode a JWT token.

        Args:
            token: The JWT token string

        Returns:
            Decoded TokenPayload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience="infraversionhub-api",
            )
            return TokenPayload(**payload)
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Could not validate credentials: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    """Dependency to get the auth service."""
    return AuthService(settings)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[TokenPayload]:
    """
    Dependency to get the current authenticated user.

    Returns None if no credentials provided (for optional auth).
    """
    if credentials is None:
        return None

    return auth_service.verify_token(credentials.credentials)


async def get_required_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenPayload:
    """
    Dependency to require an authenticated user.

    Raises 401 if not authenticated.
    """
    return auth_service.verify_token(credentials.credentials)


def require_permission(required_permission: str):
    """
    Dependency factory to require a specific permission.

    Args:
        required_permission: The permission string required (e.g., "components:read")

    Returns:
        Dependency function that checks for the permission
    """

    async def permission_checker(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> TokenPayload:
        """Check if user has the required permission."""
        token_payload = auth_service.verify_token(credentials.credentials)

        if not RBACService.has_permission(
            token_payload.permissions, required_permission
        ):
            logger.warning(
                f"Permission denied",
                extra={
                    "user_id": token_payload.sub,
                    "required": required_permission,
                    "user_permissions": token_payload.permissions,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {required_permission}",
            )

        return token_payload

    return permission_checker


# Convenience dependencies for common permissions
require_components_read = require_permission("components:read")
require_components_write = require_permission("components:write")
require_components_delete = require_permission("components:delete")
require_mappings_read = require_permission("mappings:read")
require_mappings_write = require_permission("mappings:write")
require_admin = require_permission("*:*")

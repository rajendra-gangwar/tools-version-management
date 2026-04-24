"""Role-Based Access Control (RBAC) for InfraVersionHub."""

from enum import Enum
from typing import Optional


class Permission(str, Enum):
    """Available permissions in the system."""

    # Component permissions
    COMPONENTS_CREATE = "components:create"
    COMPONENTS_READ = "components:read"
    COMPONENTS_UPDATE = "components:update"
    COMPONENTS_DELETE = "components:delete"
    COMPONENTS_ALL = "components:*"

    # Mapping permissions
    MAPPINGS_CREATE = "mappings:create"
    MAPPINGS_READ = "mappings:read"
    MAPPINGS_UPDATE = "mappings:update"
    MAPPINGS_DELETE = "mappings:delete"
    MAPPINGS_ALL = "mappings:*"

    # Audit permissions
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    AUDIT_ALL = "audit:*"

    # Import/Export permissions
    IMPORT_EXECUTE = "import:execute"
    EXPORT_EXECUTE = "export:execute"
    EXPORT_READ = "export:read"

    # User management permissions
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    USERS_ALL = "users:*"

    # System settings permissions
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"

    # Wildcard permission (admin)
    ALL = "*:*"


class Role(str, Enum):
    """Predefined user roles."""

    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    AUDITOR = "auditor"


# Role to permissions mapping
ROLE_PERMISSIONS: dict[Role, list[Permission]] = {
    Role.ADMIN: [Permission.ALL],
    Role.EDITOR: [
        Permission.COMPONENTS_ALL,
        Permission.MAPPINGS_ALL,
        Permission.AUDIT_READ,
        Permission.IMPORT_EXECUTE,
        Permission.EXPORT_EXECUTE,
        Permission.EXPORT_READ,
    ],
    Role.VIEWER: [
        Permission.COMPONENTS_READ,
        Permission.MAPPINGS_READ,
        Permission.AUDIT_READ,
        Permission.EXPORT_READ,
    ],
    Role.AUDITOR: [
        Permission.COMPONENTS_READ,
        Permission.MAPPINGS_READ,
        Permission.AUDIT_ALL,
        Permission.EXPORT_READ,
    ],
}


class RBACService:
    """Service for role-based access control operations."""

    @staticmethod
    def get_role_permissions(role: Role) -> list[Permission]:
        """Get permissions for a specific role."""
        return ROLE_PERMISSIONS.get(role, [])

    @staticmethod
    def has_permission(
        user_permissions: list[str], required_permission: str
    ) -> bool:
        """
        Check if user has the required permission.

        Args:
            user_permissions: List of permission strings the user has
            required_permission: The permission to check for

        Returns:
            True if user has the permission, False otherwise
        """
        # Check for wildcard admin permission
        if "*:*" in user_permissions:
            return True

        # Check for exact match
        if required_permission in user_permissions:
            return True

        # Check for resource-level wildcard
        # e.g., if user has "components:*", they have "components:read"
        resource, action = required_permission.split(":")
        resource_wildcard = f"{resource}:*"
        if resource_wildcard in user_permissions:
            return True

        return False

    @staticmethod
    def expand_role_to_permissions(role: Role) -> list[str]:
        """
        Expand a role into its list of permission strings.

        Args:
            role: The role to expand

        Returns:
            List of permission strings
        """
        permissions = ROLE_PERMISSIONS.get(role, [])
        return [p.value for p in permissions]

    @staticmethod
    def get_effective_permissions(
        role: Optional[Role], additional_permissions: Optional[list[str]] = None
    ) -> list[str]:
        """
        Get the effective permissions for a user.

        Combines role-based permissions with any additional explicit permissions.

        Args:
            role: User's role
            additional_permissions: Any additional permissions granted to the user

        Returns:
            Combined list of permission strings
        """
        permissions = set()

        if role:
            permissions.update(RBACService.expand_role_to_permissions(role))

        if additional_permissions:
            permissions.update(additional_permissions)

        return list(permissions)

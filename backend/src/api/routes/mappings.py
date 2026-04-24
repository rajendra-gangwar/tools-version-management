"""Environment mapping CRUD endpoints for InfraVersionHub."""

import re
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.logging_config import get_logger
from src.schemas.common import PaginatedResponse, Pagination
from src.schemas.mapping import (
    EnvironmentMapping,
    EnvironmentMatrix,
    HealthStatus,
    MappingCreate,
    MappingUpdate,
    BulkMappingCreate,
)
from src.storage import get_storage_connector
from src.storage.base import StorageConnector

logger = get_logger(__name__)

router = APIRouter(prefix="/mappings", tags=["Mappings"])

COLLECTION = "mappings"
COMPONENTS_COLLECTION = "components"
ENVIRONMENTS_COLLECTION = "environments"


def get_storage() -> StorageConnector:
    """Dependency to get storage connector."""
    return get_storage_connector()


def _to_camel_case(data: dict) -> dict:
    """Convert snake_case keys to camelCase for storage."""
    result = {}
    for key, value in data.items():
        parts = key.split("_")
        camel_key = parts[0] + "".join(word.capitalize() for word in parts[1:])
        if isinstance(value, dict):
            result[camel_key] = _to_camel_case(value)
        elif isinstance(value, list):
            result[camel_key] = [
                _to_camel_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[camel_key] = value
    return result


def _to_snake_case(data: dict) -> dict:
    """Convert camelCase keys to snake_case for API response."""
    result = {}
    for key, value in data.items():
        snake_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
        if isinstance(value, dict):
            result[snake_key] = _to_snake_case(value)
        elif isinstance(value, list):
            result[snake_key] = [
                _to_snake_case(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[snake_key] = value
    return result


@router.get(
    "",
    response_model=PaginatedResponse[EnvironmentMapping],
    summary="List environment mappings",
)
async def list_mappings(
    component_id: Optional[str] = Query(None, description="Filter by component ID"),
    environment_id: Optional[str] = Query(None, description="Filter by environment ID"),
    health_status: Optional[HealthStatus] = Query(None, description="Filter by health status"),
    sort_by: str = Query("updatedAt", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    storage: StorageConnector = Depends(get_storage),
) -> PaginatedResponse[EnvironmentMapping]:
    """List environment mappings with optional filtering and pagination."""
    logger.info(
        "Listing mappings",
        extra={"component_id": component_id, "environment_id": environment_id},
    )

    # Build filters
    filters = {}
    if component_id:
        filters["componentId"] = component_id
    if environment_id:
        filters["environmentId"] = environment_id
    if health_status:
        filters["healthStatus"] = health_status.value

    result = await storage.list(
        COLLECTION,
        filters=filters if filters else None,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    # Convert data to EnvironmentMapping models
    mappings = [
        EnvironmentMapping(**_to_snake_case(item)) for item in (result.data or [])
    ]

    total = result.metadata.get("total", len(mappings))

    return PaginatedResponse(
        data=mappings,
        pagination=Pagination.from_params(total=total, limit=limit, offset=offset),
    )


@router.post(
    "",
    response_model=EnvironmentMapping,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new environment mapping",
)
async def create_mapping(
    mapping: MappingCreate,
    storage: StorageConnector = Depends(get_storage),
) -> EnvironmentMapping:
    """Create a new environment mapping for a component."""
    logger.info(
        "Creating mapping",
        extra={
            "component_id": mapping.component_id,
            "environment_id": mapping.environment_id,
        },
    )

    # Verify component exists and get its name
    component_result = await storage.load(COMPONENTS_COLLECTION, mapping.component_id)
    if not component_result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {mapping.component_id} not found",
        )
    component_data = component_result.data
    component_name = component_data.get("name") or component_data.get("displayName")

    # Verify environment exists and get its details
    env_result = await storage.load(ENVIRONMENTS_COLLECTION, mapping.environment_id)
    if not env_result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment {mapping.environment_id} not found",
        )
    env_data = env_result.data
    environment_name = env_data.get("name")
    cluster_name = env_data.get("clusterName")
    region = env_data.get("region")

    # Check for duplicate mapping (same component and environment)
    existing_result = await storage.list(
        COLLECTION,
        filters={
            "componentId": mapping.component_id,
            "environmentId": mapping.environment_id,
        },
    )
    if existing_result.success and existing_result.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mapping already exists for component '{component_name}' in environment '{environment_name}'",
        )

    # Convert to storage format
    data = _to_camel_case(mapping.model_dump(exclude_none=True))
    # Add denormalized fields
    data["componentName"] = component_name
    data["environmentName"] = environment_name
    data["clusterName"] = cluster_name
    data["region"] = region
    data["createdAt"] = datetime.now(timezone.utc).isoformat()
    data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    result = await storage.save(COLLECTION, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return EnvironmentMapping(**_to_snake_case(result.data))


@router.post(
    "/bulk",
    response_model=list[EnvironmentMapping],
    status_code=status.HTTP_201_CREATED,
    summary="Create mappings for multiple environments",
)
async def create_bulk_mappings(
    mapping: BulkMappingCreate,
    storage: StorageConnector = Depends(get_storage),
) -> list[EnvironmentMapping]:
    """Create mappings for the same component version across multiple environments."""
    logger.info(
        "Creating bulk mappings",
        extra={
            "component_id": mapping.component_id,
            "environment_count": len(mapping.environment_ids),
        },
    )

    # Verify component exists and get its name
    component_result = await storage.load(COMPONENTS_COLLECTION, mapping.component_id)
    if not component_result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {mapping.component_id} not found",
        )
    component_data = component_result.data
    component_name = component_data.get("name") or component_data.get("displayName")

    created_mappings = []
    errors = []

    for env_id in mapping.environment_ids:
        # Verify environment exists and get its details
        env_result = await storage.load(ENVIRONMENTS_COLLECTION, env_id)
        if not env_result.success:
            errors.append(f"Environment {env_id} not found")
            continue
        env_data = env_result.data
        environment_name = env_data.get("name")
        cluster_name = env_data.get("clusterName")
        region = env_data.get("region")

        # Check for duplicate mapping (same component and environment)
        existing_result = await storage.list(
            COLLECTION,
            filters={
                "componentId": mapping.component_id,
                "environmentId": env_id,
            },
        )
        if existing_result.success and existing_result.data:
            errors.append(f"Mapping already exists for '{component_name}' in '{environment_name}'")
            continue

        # Convert to storage format
        data = {
            "componentId": mapping.component_id,
            "componentVersion": mapping.component_version,
            "environmentId": env_id,
            "namespace": mapping.namespace,
            "healthStatus": mapping.health_status,
            "notes": mapping.notes,
            "metadata": mapping.metadata or {},
            "componentName": component_name,
            "environmentName": environment_name,
            "clusterName": cluster_name,
            "region": region,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        result = await storage.save(COLLECTION, data)

        if result.success:
            created_mappings.append(EnvironmentMapping(**_to_snake_case(result.data)))
        else:
            errors.append(f"Failed to create mapping for environment {env_id}: {result.error}")

    if errors and not created_mappings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "message": "No mappings were created"},
        )

    if errors:
        logger.warning(f"Bulk mapping completed with errors: {errors}")

    return created_mappings


def _parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semver string into (major, minor, patch) tuple."""
    if not version:
        return (0, 0, 0)
    # Remove leading 'v' if present
    version = version.lstrip("v")
    # Remove any suffix after the patch number
    base_version = version.split("-")[0]
    parts = base_version.split(".")
    try:
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except ValueError:
        return (0, 0, 0)


def _calculate_upgrade_status(
    deployed_version: str,
    latest_version: Optional[str],
    major_threshold: int = 1,
    minor_threshold: int = 2,
    patch_threshold: int = 5,
) -> str:
    """Calculate upgrade status based on version comparison with hierarchical thresholds.

    Hierarchical logic:
    - If major_threshold > 0: Only check major versions (ignore minor/patch thresholds)
    - If major_threshold == 0 and minor_threshold > 0: Only check minor versions (ignore patch)
    - If major_threshold == 0 and minor_threshold == 0: Only check patch versions

    Args:
        deployed_version: Currently deployed version string
        latest_version: Latest available version string
        major_threshold: Major versions behind threshold (0 means don't use major for comparison)
        minor_threshold: Minor versions behind threshold (0 means don't use minor for comparison)
        patch_threshold: Patch versions behind threshold

    Returns:
        Upgrade status: 'up_to_date', 'upgrade_recommended', 'critical_upgrade', or 'unknown'
    """
    if not latest_version:
        return "unknown"

    deployed = _parse_semver(deployed_version)
    latest = _parse_semver(latest_version)

    major_diff = latest[0] - deployed[0]
    minor_diff = latest[1] - deployed[1]
    patch_diff = latest[2] - deployed[2]

    # If deployed is ahead or same overall, it's up to date
    if major_diff < 0 or (major_diff == 0 and minor_diff < 0) or (major_diff == 0 and minor_diff == 0 and patch_diff <= 0):
        return "up_to_date"

    # Hierarchical threshold checking
    if major_threshold > 0:
        # Only check major version difference
        if major_diff >= major_threshold:
            return "critical_upgrade"
        elif major_diff > 0:
            return "upgrade_recommended"
        # major_diff == 0 means same major version, so up to date for major-only check
        return "up_to_date"

    elif minor_threshold > 0:
        # Major threshold is 0, so only check minor version difference
        if minor_diff >= minor_threshold:
            return "critical_upgrade"
        elif minor_diff > 0:
            return "upgrade_recommended"
        # minor_diff == 0 means same minor version, so up to date for minor-only check
        return "up_to_date"

    else:
        # Both major and minor thresholds are 0, only check patch
        if patch_diff >= patch_threshold:
            return "critical_upgrade"
        elif patch_diff > 0:
            return "upgrade_recommended"
        return "up_to_date"


@router.get(
    "/matrix",
    response_model=EnvironmentMatrix,
    summary="Get environment matrix view",
)
async def get_environment_matrix(
    storage: StorageConnector = Depends(get_storage),
) -> EnvironmentMatrix:
    """Get a matrix view of all components across all environments."""
    logger.info("Generating environment matrix")

    # Get all components
    components_result = await storage.list(COMPONENTS_COLLECTION, limit=500)
    if not components_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch components",
        )

    # Get all environments
    environments_result = await storage.list(ENVIRONMENTS_COLLECTION, limit=500)
    if not environments_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch environments",
        )

    # Get all mappings
    mappings_result = await storage.list(COLLECTION, limit=1000)
    if not mappings_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch mappings",
        )

    components = components_result.data or []
    environments = environments_result.data or []
    mappings = mappings_result.data or []

    # Get environment names
    env_names = [env.get("name", "unknown") for env in environments]

    # Build component matrix
    component_matrix: list[dict[str, Any]] = []
    for component in components:
        component_id = component.get("id")
        component_name = component.get("name") or component.get("displayName")
        latest_version = component.get("latestVersion")

        # Get version thresholds (with defaults) - supports new major.minor.patch format
        thresholds = component.get("versionThresholds") or {}
        major_threshold = thresholds.get("majorVersionsBehind", 1)
        minor_threshold = thresholds.get("minorVersionsBehind", 2)
        patch_threshold = thresholds.get("patchVersionsBehind", 5)

        # Get all mappings for this component
        component_mappings = [
            m for m in mappings if m.get("componentId") == component_id
        ]

        # Build versions by environment
        versions: dict[str, dict[str, Any]] = {}
        for mapping in component_mappings:
            env_name = mapping.get("environmentName", "unknown")
            deployed_version = mapping.get("componentVersion")
            upgrade_status = _calculate_upgrade_status(
                deployed_version,
                latest_version,
                major_threshold,
                minor_threshold,
                patch_threshold,
            )
            versions[env_name] = {
                "version": deployed_version,
                "health": mapping.get("healthStatus"),
                "upgradeStatus": upgrade_status,
            }

        component_matrix.append(
            {
                "componentId": component_id,
                "componentName": component_name,
                "latestVersion": latest_version,
                "versionThresholds": {
                    "majorVersionsBehind": major_threshold,
                    "minorVersionsBehind": minor_threshold,
                    "patchVersionsBehind": patch_threshold,
                },
                "versions": versions,
            }
        )

    return EnvironmentMatrix(
        environments=sorted(env_names),
        components=component_matrix,
    )


@router.get(
    "/{mapping_id}",
    response_model=EnvironmentMapping,
    summary="Get a specific mapping",
)
async def get_mapping(
    mapping_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> EnvironmentMapping:
    """Get a specific environment mapping by ID."""
    logger.debug(f"Getting mapping {mapping_id}")

    result = await storage.load(COLLECTION, mapping_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping {mapping_id} not found",
        )

    return EnvironmentMapping(**_to_snake_case(result.data))


@router.put(
    "/{mapping_id}",
    response_model=EnvironmentMapping,
    summary="Update a mapping",
)
async def update_mapping(
    mapping_id: str,
    mapping: MappingUpdate,
    storage: StorageConnector = Depends(get_storage),
) -> EnvironmentMapping:
    """Update an existing environment mapping."""
    logger.info(f"Updating mapping {mapping_id}")

    # Check if mapping exists
    existing = await storage.load(COLLECTION, mapping_id)
    if not existing.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping {mapping_id} not found",
        )

    # If environment_id is being updated, look up the new environment
    update_data = mapping.model_dump(exclude_none=True)
    if mapping.environment_id:
        env_result = await storage.load(ENVIRONMENTS_COLLECTION, mapping.environment_id)
        if not env_result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Environment {mapping.environment_id} not found",
            )
        env_data = env_result.data
        update_data["environment_name"] = env_data.get("name")
        update_data["cluster_name"] = env_data.get("clusterName")
        update_data["region"] = env_data.get("region")

    # Convert to storage format
    data = _to_camel_case(update_data)
    data["updatedAt"] = datetime.now(timezone.utc).isoformat()

    result = await storage.update(COLLECTION, mapping_id, data)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error,
        )

    return EnvironmentMapping(**_to_snake_case(result.data))


@router.delete(
    "/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a mapping",
)
async def delete_mapping(
    mapping_id: str,
    storage: StorageConnector = Depends(get_storage),
) -> None:
    """Delete an environment mapping."""
    logger.info(f"Deleting mapping {mapping_id}")

    result = await storage.delete(COLLECTION, mapping_id)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping {mapping_id} not found",
        )

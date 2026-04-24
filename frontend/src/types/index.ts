// Component types (no version - version is tracked in mappings)
export interface Component {
  id: string;
  name: string;
  display_name?: string;
  category: string; // Dynamic category - fetched from API
  description?: string;
  latest_version?: string;
  version_thresholds?: VersionThresholds;
  owner_team?: OwnerTeam; // Made optional
  tags: string[];
  created_at: string;
  updated_at: string;
}

// Version thresholds in major.minor.patch format
export interface VersionThresholds {
  major_versions_behind: number;
  minor_versions_behind: number;
  patch_versions_behind: number;
}

export interface OwnerTeam {
  name: string;
  email?: string;
  slack_channel?: string;
}

// Category type for dynamic categories
export interface Category {
  id: string;
  name: string;
  display_name?: string;
  description?: string;
  color?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Environment types
export interface Environment {
  id: string;
  name: string;
  display_name?: string;
  environment_type: EnvironmentType;
  cloud_provider: CloudProvider;
  region: string;
  cluster_name?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type EnvironmentType =
  | 'production'
  | 'staging'
  | 'development'
  | 'testing'
  | 'sandbox';

export type CloudProvider = 'aws' | 'gcp' | 'azure' | 'on-premise' | 'other';

// Mapping types (simplified - no deployment status)
export interface EnvironmentMapping {
  id: string;
  component_id: string;
  component_name?: string;
  component_version: string;
  environment_id: string;
  environment_name?: string;
  cluster_name?: string;
  region?: string;
  namespace?: string;
  health_status: HealthStatus;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
export type UpgradeStatus = 'up_to_date' | 'upgrade_recommended' | 'critical_upgrade' | 'unknown';

// Pagination types
export interface Pagination {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}

// Environment Matrix types
export interface EnvironmentMatrix {
  environments: string[];
  components: MatrixComponent[];
}

export interface MatrixComponent {
  componentId: string;
  componentName: string;
  latestVersion?: string;
  versionThresholds?: {
    majorVersionsBehind: number;
    minorVersionsBehind: number;
    patchVersionsBehind: number;
  };
  versions: Record<string, MatrixVersion>;
}

export interface MatrixVersion {
  version: string;
  health: HealthStatus;
  upgradeStatus?: UpgradeStatus;
}

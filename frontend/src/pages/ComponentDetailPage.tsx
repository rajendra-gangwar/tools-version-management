import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { componentApi, mappingApi } from '../services/api';

export default function ComponentDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: componentData, isLoading } = useQuery({
    queryKey: ['component', id],
    queryFn: () => componentApi.get(id!),
    enabled: !!id,
  });

  const { data: mappingsData } = useQuery({
    queryKey: ['mappings', { componentId: id }],
    queryFn: () => mappingApi.list({ componentId: id }),
    enabled: !!id,
  });

  const component = componentData?.data;
  const mappings = mappingsData?.data?.data || [];

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!component) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Component not found</p>
        <Link to="/components" className="text-primary-600 hover:text-primary-700">
          Back to components
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-sm text-gray-500">
        <Link to="/components" className="hover:text-gray-700">
          Components
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{component.name}</span>
      </nav>

      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {component.display_name || component.name}
          </h1>
          <p className="mt-1 text-gray-500 font-mono">{component.name}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/components/${id}/edit`} className="btn btn-secondary">Edit</Link>
          <button className="btn btn-danger">Delete</button>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Details</h2>
            <dl className="grid grid-cols-2 gap-4">
              <div>
                <dt className="text-sm text-gray-500">Category</dt>
                <dd className="mt-1">
                  <span className="badge badge-info">{component.category}</span>
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Latest Version</dt>
                <dd className="mt-1 font-mono text-lg font-semibold text-primary-600">
                  {component.latest_version || 'Not set'}
                </dd>
              </div>
              {component.owner_team?.name && (
                <div>
                  <dt className="text-sm text-gray-500">Owner Team</dt>
                  <dd className="mt-1">{component.owner_team.name}</dd>
                </div>
              )}
              <div>
                <dt className="text-sm text-gray-500">Last Updated</dt>
                <dd className="mt-1">
                  {new Date(component.updated_at).toLocaleString()}
                </dd>
              </div>
              {component.version_thresholds && (
                <div>
                  <dt className="text-sm text-gray-500">Version Thresholds</dt>
                  <dd className="mt-1 font-mono text-sm">
                    {component.version_thresholds.major_versions_behind || 0}.
                    {component.version_thresholds.minor_versions_behind || 0}.
                    {component.version_thresholds.patch_versions_behind || 0}
                  </dd>
                </div>
              )}
            </dl>

            {component.description && (
              <div className="mt-6">
                <dt className="text-sm text-gray-500">Description</dt>
                <dd className="mt-1 text-gray-700">{component.description}</dd>
              </div>
            )}

            {component.tags?.length > 0 && (
              <div className="mt-6">
                <dt className="text-sm text-gray-500 mb-2">Tags</dt>
                <dd className="flex flex-wrap gap-2">
                  {component.tags.map((tag: string) => (
                    <span key={tag} className="badge badge-gray">
                      {tag}
                    </span>
                  ))}
                </dd>
              </div>
            )}
          </div>

          {/* Deployments */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Deployments</h2>
              <button className="btn btn-primary text-sm">Add Deployment</button>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Environment
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Cluster
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Version
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {mappings.map((mapping: { id: string; environment_name: string; cluster_name: string; component_version: string; health_status: string }) => (
                  <tr key={mapping.id}>
                    <td className="px-4 py-3">
                      <span
                        className={`badge ${
                          mapping.environment_name?.toLowerCase().includes('prod')
                            ? 'badge-danger'
                            : mapping.environment_name?.toLowerCase().includes('staging')
                            ? 'badge-warning'
                            : 'badge-info'
                        }`}
                      >
                        {mapping.environment_name}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {mapping.cluster_name}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">
                      {mapping.component_version}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`badge ${
                          mapping.health_status === 'healthy'
                            ? 'badge-success'
                            : mapping.health_status === 'unhealthy'
                            ? 'badge-danger'
                            : mapping.health_status === 'degraded'
                            ? 'badge-warning'
                            : 'badge-gray'
                        }`}
                      >
                        {mapping.health_status}
                      </span>
                    </td>
                  </tr>
                ))}
                {mappings.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                      No deployments for this component
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Quick Stats
            </h2>
            <dl className="space-y-4">
              <div>
                <dt className="text-sm text-gray-500">Total Deployments</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {mappings.length}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Production</dt>
                <dd className="text-2xl font-semibold text-gray-900">
                  {mappings.filter((m: { environment_name: string }) => m.environment_name === 'production').length}
                </dd>
              </div>
            </dl>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact</h2>
            <div className="space-y-2 text-sm">
              <p>
                <span className="text-gray-500">Team:</span>{' '}
                {component.owner_team?.name}
              </p>
              {component.owner_team?.email && (
                <p>
                  <span className="text-gray-500">Email:</span>{' '}
                  <a
                    href={`mailto:${component.owner_team.email}`}
                    className="text-primary-600"
                  >
                    {component.owner_team.email}
                  </a>
                </p>
              )}
              {component.owner_team?.slack_channel && (
                <p>
                  <span className="text-gray-500">Slack:</span>{' '}
                  {component.owner_team.slack_channel}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

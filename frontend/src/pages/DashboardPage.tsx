import { useQuery } from '@tanstack/react-query';
import { componentApi, mappingApi, healthApi } from '../services/api';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.ready(),
    refetchInterval: 30000,
  });

  const { data: componentsData } = useQuery({
    queryKey: ['components', { limit: 5 }],
    queryFn: () => componentApi.list({ limit: 5 }),
  });

  const { data: mappingsData } = useQuery({
    queryKey: ['mappings', { limit: 10 }],
    queryFn: () => mappingApi.list({ limit: 10 }),
  });

  const health = healthData?.data;
  const components = componentsData?.data?.data || [];
  const mappings = mappingsData?.data?.data || [];

  const stats = [
    {
      name: 'Total Components',
      value: componentsData?.data?.pagination?.total || 0,
      href: '/components',
    },
    {
      name: 'Total Mappings',
      value: mappingsData?.data?.pagination?.total || 0,
      href: '/mappings',
    },
    {
      name: 'Production Deployments',
      value: mappings.filter((m: { environment_name: string }) => m.environment_name === 'production').length,
      href: '/environments',
    },
    {
      name: 'System Status',
      value: health?.status === 'healthy' ? 'Healthy' : 'Degraded',
      status: health?.status,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-500">
          Overview of your infrastructure components and deployments
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <dt className="text-sm font-medium text-gray-500">{stat.name}</dt>
            <dd className="mt-2 flex items-baseline">
              {stat.href ? (
                <Link
                  to={stat.href}
                  className="text-3xl font-semibold text-primary-600 hover:text-primary-700"
                >
                  {stat.value}
                </Link>
              ) : (
                <span
                  className={`text-3xl font-semibold ${
                    stat.status === 'healthy'
                      ? 'text-green-600'
                      : 'text-yellow-600'
                  }`}
                >
                  {stat.value}
                </span>
              )}
            </dd>
          </div>
        ))}
      </div>

      {/* Recent Components */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Components
          </h2>
          <Link to="/components" className="text-primary-600 hover:text-primary-700 text-sm">
            View all
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Category
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Version
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Owner
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {components.map((component: { id: string; name: string; display_name?: string; category: string; current_version: string; owner_team: { name: string } }) => (
                <tr key={component.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link
                      to={`/components/${component.id}`}
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {component.display_name || component.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className="badge badge-info">{component.category}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-sm">
                    {component.current_version}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {component.owner_team?.name}
                  </td>
                </tr>
              ))}
              {components.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                    No components found. Create your first component to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Deployments */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Recent Deployments
          </h2>
          <Link to="/mappings" className="text-primary-600 hover:text-primary-700 text-sm">
            View all
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Component
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Environment
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cluster
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Version
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {mappings.map((mapping: { id: string; component_name: string; environment_name: string; cluster_name: string; component_version: string; deployment_status: string }) => (
                <tr key={mapping.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{mapping.component_name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`badge ${
                        mapping.environment_name === 'production'
                          ? 'badge-danger'
                          : mapping.environment_name === 'staging'
                          ? 'badge-warning'
                          : 'badge-info'
                      }`}
                    >
                      {mapping.environment_name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{mapping.cluster_name}</td>
                  <td className="px-4 py-3 font-mono text-sm">
                    {mapping.component_version}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`badge ${
                        mapping.deployment_status === 'deployed'
                          ? 'badge-success'
                          : mapping.deployment_status === 'failed'
                          ? 'badge-danger'
                          : 'badge-warning'
                      }`}
                    >
                      {mapping.deployment_status}
                    </span>
                  </td>
                </tr>
              ))}
              {mappings.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    No deployments found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

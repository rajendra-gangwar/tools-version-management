import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { mappingApi, environmentApi } from '../services/api';
import type { EnvironmentMapping, Environment } from '../types';

export default function MappingsPage() {
  const [environmentId, setEnvironmentId] = useState('');

  // Fetch environments for filter dropdown
  const { data: environmentsData } = useQuery({
    queryKey: ['environments'],
    queryFn: () => environmentApi.list({ limit: 200 }),
  });
  const environments: Environment[] = environmentsData?.data?.data || [];

  const { data, isLoading } = useQuery({
    queryKey: ['mappings', { environmentId }],
    queryFn: () =>
      mappingApi.list({
        environmentId: environmentId || undefined,
        limit: 100,
      }),
  });

  const mappings: EnvironmentMapping[] = data?.data?.data || [];
  const pagination = data?.data?.pagination;

  // Helper to get environment details
  const getEnvironment = (envId: string): Environment | undefined => {
    return environments.find((e) => e.id === envId);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mappings</h1>
          <p className="mt-1 text-gray-500">
            View and manage component deployments across environments
          </p>
        </div>
        <Link to="/mappings/new" className="btn btn-primary">Add Mapping</Link>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="w-full sm:w-64">
            <select
              value={environmentId}
              onChange={(e) => setEnvironmentId(e.target.value)}
              className="input"
            >
              <option value="">All Environments</option>
              {environments.map((env) => (
                <option key={env.id} value={env.id}>
                  {env.display_name || env.name} ({env.environment_type})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Mappings Table */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Component
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Environment
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Region / Cluster
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Updated
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {mappings.map((mapping) => {
                const env = getEnvironment(mapping.environment_id);
                return (
                  <tr key={mapping.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium">
                      {mapping.component_name || mapping.component_id}
                    </td>
                    <td className="px-6 py-4 font-mono text-sm">
                      {mapping.component_version}
                    </td>
                    <td className="px-6 py-4">
                      {env ? (
                        <span
                          className={`badge ${
                            env.environment_type === 'production'
                              ? 'badge-danger'
                              : env.environment_type === 'staging'
                              ? 'badge-warning'
                              : 'badge-info'
                          }`}
                        >
                          {env.display_name || env.name}
                        </span>
                      ) : (
                        <span className="text-gray-400">Unknown</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-600 text-sm">
                      {env ? (
                        <div>
                          <span className="font-mono">{env.region}</span>
                          {env.cluster_name && (
                            <span className="text-gray-400 ml-1">/ {env.cluster_name}</span>
                          )}
                        </div>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(mapping.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        to={`/mappings/${mapping.id}/edit`}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        Edit
                      </Link>
                    </td>
                  </tr>
                );
              })}
              {mappings.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No mappings found. Create your first mapping to track component deployments.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {pagination && (
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-sm text-gray-500">
            Showing {mappings.length} of {pagination.total} mappings
          </div>
        )}
      </div>
    </div>
  );
}

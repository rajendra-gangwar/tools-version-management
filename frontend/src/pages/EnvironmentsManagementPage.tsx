import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { environmentApi } from '../services/api';
import type { Environment, EnvironmentType, CloudProvider } from '../types';

const environmentTypes: EnvironmentType[] = [
  'production',
  'staging',
  'development',
  'testing',
  'sandbox',
];

const cloudProviders: CloudProvider[] = ['aws', 'gcp', 'azure', 'on-premise', 'other'];

interface FormData {
  name: string;
  display_name: string;
  environment_type: EnvironmentType;
  cloud_provider: CloudProvider;
  region: string;
  cluster_name: string;
  description: string;
}

const initialFormData: FormData = {
  name: '',
  display_name: '',
  environment_type: 'development',
  cloud_provider: 'aws',
  region: '',
  cluster_name: '',
  description: '',
};

export default function EnvironmentsManagementPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['environments'],
    queryFn: () => environmentApi.list({ limit: 100 }),
  });

  const environments: Environment[] = data?.data?.data || [];

  const createMutation = useMutation({
    mutationFn: environmentApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      resetForm();
    },
    onError: (error: any) => {
      handleError(error);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      environmentApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
      resetForm();
    },
    onError: (error: any) => {
      handleError(error);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: environmentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environments'] });
    },
  });

  const handleError = (error: any) => {
    const detail = error.response?.data?.detail;
    if (Array.isArray(detail)) {
      const newErrors: Record<string, string> = {};
      detail.forEach((err: any) => {
        const field = err.loc?.join('.') || 'general';
        newErrors[field] = err.msg;
      });
      setErrors(newErrors);
    } else {
      setErrors({ general: detail || 'An error occurred' });
    }
  };

  const resetForm = () => {
    setFormData(initialFormData);
    setEditingId(null);
    setShowForm(false);
    setErrors({});
  };

  const handleEdit = (env: Environment) => {
    setFormData({
      name: env.name,
      display_name: env.display_name || '',
      environment_type: env.environment_type,
      cloud_provider: env.cloud_provider,
      region: env.region,
      cluster_name: env.cluster_name || '',
      description: env.description || '',
    });
    setEditingId(env.id);
    setShowForm(true);
  };

  const handleDelete = (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete environment "${name}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.region.trim()) {
      newErrors.region = 'Region is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    const payload = {
      name: formData.name.trim(),
      display_name: formData.display_name.trim() || undefined,
      environment_type: formData.environment_type,
      cloud_provider: formData.cloud_provider,
      region: formData.region.trim(),
      cluster_name: formData.cluster_name.trim() || undefined,
      description: formData.description.trim() || undefined,
      is_active: true,
    };

    if (editingId) {
      updateMutation.mutate({ id: editingId, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Environments</h1>
          <p className="mt-1 text-gray-500">
            Manage your deployment environments (clusters, regions)
          </p>
        </div>
        <button
          onClick={() => {
            resetForm();
            setShowForm(true);
          }}
          className="btn btn-primary"
        >
          Add Environment
        </button>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {editingId ? 'Edit Environment' : 'Add New Environment'}
          </h2>

          {errors.general && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={!!editingId}
                  className={`input ${errors.name ? 'border-red-500' : ''} ${editingId ? 'bg-gray-100' : ''}`}
                  placeholder="e.g., dev-eks-1"
                />
                {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  name="display_name"
                  value={formData.display_name}
                  onChange={handleChange}
                  className="input"
                  placeholder="e.g., Development EKS Cluster 1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type <span className="text-red-500">*</span>
                </label>
                <select
                  name="environment_type"
                  value={formData.environment_type}
                  onChange={handleChange}
                  className="input"
                >
                  {environmentTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cloud Provider
                </label>
                <select
                  name="cloud_provider"
                  value={formData.cloud_provider}
                  onChange={handleChange}
                  className="input"
                >
                  {cloudProviders.map((provider) => (
                    <option key={provider} value={provider}>
                      {provider.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Region <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="region"
                  value={formData.region}
                  onChange={handleChange}
                  className={`input ${errors.region ? 'border-red-500' : ''}`}
                  placeholder="e.g., us-east-1"
                />
                {errors.region && <p className="mt-1 text-sm text-red-500">{errors.region}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cluster Name
                </label>
                <input
                  type="text"
                  name="cluster_name"
                  value={formData.cluster_name}
                  onChange={handleChange}
                  className="input"
                  placeholder="e.g., my-eks-cluster"
                />
              </div>

              <div className="md:col-span-2 lg:col-span-3">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  className="input"
                  placeholder="Optional description..."
                />
              </div>
            </div>

            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={resetForm}
                className="btn btn-secondary"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Saving...' : editingId ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Environments Table */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Region
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Cluster
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {environments.map((env) => (
                <tr key={env.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">
                      {env.display_name || env.name}
                    </div>
                    {env.display_name && (
                      <div className="text-sm text-gray-500 font-mono">{env.name}</div>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`badge ${
                        env.environment_type === 'production'
                          ? 'badge-danger'
                          : env.environment_type === 'staging'
                          ? 'badge-warning'
                          : 'badge-info'
                      }`}
                    >
                      {env.environment_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-600 uppercase text-sm">
                    {env.cloud_provider}
                  </td>
                  <td className="px-6 py-4 text-gray-600 font-mono text-sm">{env.region}</td>
                  <td className="px-6 py-4 text-gray-600">{env.cluster_name || '-'}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`badge ${env.is_active ? 'badge-success' : 'badge-gray'}`}
                    >
                      {env.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleEdit(env)}
                      className="text-primary-600 hover:text-primary-700 mr-3"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(env.id, env.name)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {environments.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                    No environments found. Create your first environment to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

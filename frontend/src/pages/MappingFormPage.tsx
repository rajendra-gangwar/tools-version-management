import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { mappingApi, componentApi, environmentApi } from '../services/api';
import type { Component, Environment } from '../types';

type HealthStatus = 'healthy' | 'unhealthy' | 'degraded' | 'unknown';

const healthStatuses: HealthStatus[] = ['healthy', 'unhealthy', 'degraded', 'unknown'];

interface FormData {
  component_id: string;
  component_version: string;
  environment_ids: string[];
  namespace: string;
  health_status: HealthStatus;
  notes: string;
}

const initialFormData: FormData = {
  component_id: '',
  component_version: '',
  environment_ids: [],
  namespace: '',
  health_status: 'healthy',
  notes: '',
};

export default function MappingFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const isEditMode = Boolean(id) && id !== 'new';

  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch components for dropdown
  const { data: componentsData } = useQuery({
    queryKey: ['components'],
    queryFn: () => componentApi.list({ limit: 200 }),
  });
  const components: Component[] = componentsData?.data?.data || [];

  // Fetch environments for dropdown
  const { data: environmentsData } = useQuery({
    queryKey: ['environments'],
    queryFn: () => environmentApi.list({ limit: 200 }),
  });
  const environments: Environment[] = (environmentsData?.data?.data || []).filter(
    (env: Environment) => env.is_active
  );

  // Fetch existing mapping for edit mode
  const { data: existingMapping } = useQuery({
    queryKey: ['mapping', id],
    queryFn: () => mappingApi.get(id!),
    enabled: isEditMode,
  });

  // Populate form when editing
  useEffect(() => {
    if (existingMapping?.data) {
      const m = existingMapping.data;
      setFormData({
        component_id: m.component_id || '',
        component_version: m.component_version || '',
        environment_ids: m.environment_id ? [m.environment_id] : [],
        namespace: m.namespace || '',
        health_status: m.health_status || 'healthy',
        notes: m.notes || '',
      });
    }
  }, [existingMapping]);

  // Create mutation (single)
  const createMutation = useMutation({
    mutationFn: mappingApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mappings'] });
      queryClient.invalidateQueries({ queryKey: ['environmentMatrix'] });
      navigate('/mappings');
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      if (Array.isArray(detail)) {
        const newErrors: Record<string, string> = {};
        detail.forEach((err: any) => {
          const field = err.loc?.join('.') || 'general';
          newErrors[field] = err.msg;
        });
        setErrors(newErrors);
      } else {
        setErrors({ general: detail || 'Failed to create mapping' });
      }
    },
  });

  // Create bulk mutation
  const createBulkMutation = useMutation({
    mutationFn: mappingApi.createBulk,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mappings'] });
      queryClient.invalidateQueries({ queryKey: ['environmentMatrix'] });
      navigate('/mappings');
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'object' && detail.errors) {
        setErrors({ general: detail.errors.join('\n') });
      } else if (Array.isArray(detail)) {
        const newErrors: Record<string, string> = {};
        detail.forEach((err: any) => {
          const field = err.loc?.join('.') || 'general';
          newErrors[field] = err.msg;
        });
        setErrors(newErrors);
      } else {
        setErrors({ general: detail || 'Failed to create mappings' });
      }
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: any) => mappingApi.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mappings'] });
      queryClient.invalidateQueries({ queryKey: ['mapping', id] });
      queryClient.invalidateQueries({ queryKey: ['environmentMatrix'] });
      navigate('/mappings');
    },
    onError: (error: any) => {
      const detail = error.response?.data?.detail;
      if (Array.isArray(detail)) {
        const newErrors: Record<string, string> = {};
        detail.forEach((err: any) => {
          const field = err.loc?.join('.') || 'general';
          newErrors[field] = err.msg;
        });
        setErrors(newErrors);
      } else {
        setErrors({ general: detail || 'Failed to update mapping' });
      }
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.component_id) {
      newErrors.component_id = 'Component is required';
    }

    if (!formData.component_version.trim()) {
      newErrors.component_version = 'Version is required';
    }

    if (formData.environment_ids.length === 0) {
      newErrors.environment_ids = 'At least one environment is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    if (isEditMode) {
      // Update single mapping
      const payload = {
        component_version: formData.component_version.trim(),
        environment_id: formData.environment_ids[0],
        namespace: formData.namespace.trim() || undefined,
        health_status: formData.health_status,
        notes: formData.notes.trim() || undefined,
      };
      updateMutation.mutate(payload);
    } else if (formData.environment_ids.length === 1) {
      // Create single mapping
      const payload = {
        component_id: formData.component_id,
        component_version: formData.component_version.trim(),
        environment_id: formData.environment_ids[0],
        namespace: formData.namespace.trim() || undefined,
        health_status: formData.health_status,
        notes: formData.notes.trim() || undefined,
      };
      createMutation.mutate(payload);
    } else {
      // Create bulk mappings
      const payload = {
        component_id: formData.component_id,
        component_version: formData.component_version.trim(),
        environment_ids: formData.environment_ids,
        namespace: formData.namespace.trim() || undefined,
        health_status: formData.health_status,
        notes: formData.notes.trim() || undefined,
      };
      createBulkMutation.mutate(payload);
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

  const handleEnvironmentToggle = (envId: string) => {
    setFormData((prev) => {
      const newIds = prev.environment_ids.includes(envId)
        ? prev.environment_ids.filter((id) => id !== envId)
        : [...prev.environment_ids, envId];
      return { ...prev, environment_ids: newIds };
    });

    if (errors.environment_ids) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.environment_ids;
        return newErrors;
      });
    }
  };

  const isLoading = createMutation.isPending || createBulkMutation.isPending || updateMutation.isPending;

  // Get selected component for showing latest version hint
  const selectedComponent = components.find((c) => c.id === formData.component_id);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditMode ? 'Edit Mapping' : 'Add New Mapping'}
        </h1>
        <p className="mt-1 text-gray-500">
          {isEditMode
            ? 'Update the deployment mapping information'
            : 'Map a component version to one or more environments'}
        </p>
      </div>

      {errors.general && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 whitespace-pre-wrap">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Component Selection */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Component</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="component_id" className="block text-sm font-medium text-gray-700 mb-1">
                Component <span className="text-red-500">*</span>
              </label>
              <select
                id="component_id"
                name="component_id"
                value={formData.component_id}
                onChange={handleChange}
                disabled={isEditMode}
                className={`input ${errors.component_id ? 'border-red-500' : ''} ${isEditMode ? 'bg-gray-100' : ''}`}
              >
                <option value="">Select a component...</option>
                {components.map((comp) => (
                  <option key={comp.id} value={comp.id}>
                    {comp.display_name || comp.name}
                  </option>
                ))}
              </select>
              {errors.component_id && (
                <p className="mt-1 text-sm text-red-500">{errors.component_id}</p>
              )}
              {components.length === 0 && (
                <p className="mt-1 text-sm text-yellow-600">
                  No components found. Please create a component first.
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="component_version"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Version <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="component_version"
                name="component_version"
                value={formData.component_version}
                onChange={handleChange}
                className={`input ${errors.component_version ? 'border-red-500' : ''}`}
                placeholder="e.g., 2.9.3"
              />
              {errors.component_version && (
                <p className="mt-1 text-sm text-red-500">{errors.component_version}</p>
              )}
              {selectedComponent?.latest_version && (
                <p className="mt-1 text-sm text-gray-500">
                  Latest version: <span className="font-mono font-medium">{selectedComponent.latest_version}</span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Environment Selection */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Environment{!isEditMode && 's'}
            {!isEditMode && (
              <span className="ml-2 text-sm font-normal text-gray-500">
                (Select one or more environments)
              </span>
            )}
          </h2>

          {isEditMode ? (
            // Single environment dropdown for edit mode
            <div>
              <label
                htmlFor="environment_id"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Environment <span className="text-red-500">*</span>
              </label>
              <select
                id="environment_id"
                name="environment_id"
                value={formData.environment_ids[0] || ''}
                onChange={(e) => setFormData((prev) => ({ ...prev, environment_ids: e.target.value ? [e.target.value] : [] }))}
                disabled={isEditMode}
                className={`input ${errors.environment_ids ? 'border-red-500' : ''} bg-gray-100`}
              >
                <option value="">Select an environment...</option>
                {environments.map((env) => (
                  <option key={env.id} value={env.id}>
                    {env.display_name || env.name} ({env.environment_type} - {env.cloud_provider.toUpperCase()} {env.region})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            // Multi-select checkboxes for create mode
            <div>
              {errors.environment_ids && (
                <p className="mb-2 text-sm text-red-500">{errors.environment_ids}</p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-64 overflow-y-auto">
                {environments.map((env) => (
                  <label
                    key={env.id}
                    className={`flex items-start p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                      formData.environment_ids.includes(env.id)
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.environment_ids.includes(env.id)}
                      onChange={() => handleEnvironmentToggle(env.id)}
                      className="mt-1 h-4 w-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
                    />
                    <div className="ml-3">
                      <div className="font-medium text-gray-900">
                        {env.display_name || env.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {env.environment_type} - {env.cloud_provider.toUpperCase()} {env.region}
                        {env.cluster_name && ` (${env.cluster_name})`}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
              {environments.length === 0 && (
                <p className="text-sm text-yellow-600">
                  No active environments found. Please create an environment first.
                </p>
              )}
              {formData.environment_ids.length > 0 && (
                <p className="mt-3 text-sm text-gray-600">
                  {formData.environment_ids.length} environment{formData.environment_ids.length > 1 ? 's' : ''} selected
                </p>
              )}
            </div>
          )}

          <div className="mt-4">
            <label htmlFor="namespace" className="block text-sm font-medium text-gray-700 mb-1">
              Namespace
            </label>
            <input
              type="text"
              id="namespace"
              name="namespace"
              value={formData.namespace}
              onChange={handleChange}
              className="input"
              placeholder="e.g., argocd (optional)"
            />
          </div>
        </div>

        {/* Health Status & Notes */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Additional Info</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="health_status" className="block text-sm font-medium text-gray-700 mb-1">
                Health Status
              </label>
              <select
                id="health_status"
                name="health_status"
                value={formData.health_status}
                onChange={handleChange}
                className="input"
              >
                {healthStatuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              rows={2}
              className="input"
              placeholder="Optional deployment notes..."
            />
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/mappings')}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading
              ? 'Saving...'
              : isEditMode
              ? 'Update Mapping'
              : formData.environment_ids.length > 1
              ? `Create ${formData.environment_ids.length} Mappings`
              : 'Create Mapping'}
          </button>
        </div>
      </form>
    </div>
  );
}

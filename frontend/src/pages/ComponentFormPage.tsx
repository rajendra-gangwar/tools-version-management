import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { componentApi, categoryApi } from '../services/api';
import type { Category } from '../types';

// Default categories as fallback
const DEFAULT_CATEGORIES = [
  'orchestration',
  'monitoring',
  'logging',
  'networking',
  'security',
  'storage',
  'ci-cd',
  'service-mesh',
  'other',
];

interface FormData {
  name: string;
  display_name: string;
  category: string;
  description: string;
  latest_version: string;
  version_thresholds: {
    major_versions_behind: string;
    minor_versions_behind: string;
    patch_versions_behind: string;
  };
  owner_team: {
    name: string;
    email: string;
    slack_channel: string;
  };
  repository: {
    url: string;
    type: string;
  };
  documentation: {
    url: string;
    changelog_url: string;
  };
  tags: string;
}

const initialFormData: FormData = {
  name: '',
  display_name: '',
  category: 'other',
  description: '',
  latest_version: '',
  version_thresholds: {
    major_versions_behind: '1',
    minor_versions_behind: '2',
    patch_versions_behind: '5',
  },
  owner_team: {
    name: '',
    email: '',
    slack_channel: '',
  },
  repository: {
    url: '',
    type: 'github',
  },
  documentation: {
    url: '',
    changelog_url: '',
  },
  tags: '',
};

export default function ComponentFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const isEditMode = Boolean(id) && id !== 'new';

  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch categories from API
  const { data: categoriesData } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoryApi.list({ is_active: true, limit: 100 }),
  });

  // Get category list - use API data or fall back to defaults
  const apiCategories = categoriesData?.data?.data;
  const categories: string[] = Array.isArray(apiCategories) && apiCategories.length > 0
    ? apiCategories.map((cat: Category) => cat.name)
    : DEFAULT_CATEGORIES;

  // Fetch existing component for edit mode
  const { data: existingComponent } = useQuery({
    queryKey: ['component', id],
    queryFn: () => componentApi.get(id!),
    enabled: isEditMode,
  });

  // Populate form when editing
  useEffect(() => {
    if (existingComponent?.data) {
      const comp = existingComponent.data;
      setFormData({
        name: comp.name || '',
        display_name: comp.display_name || '',
        category: comp.category || 'other',
        description: comp.description || '',
        latest_version: comp.latest_version || '',
        version_thresholds: {
          major_versions_behind: String(comp.version_thresholds?.major_versions_behind || 1),
          minor_versions_behind: String(comp.version_thresholds?.minor_versions_behind || 2),
          patch_versions_behind: String(comp.version_thresholds?.patch_versions_behind || 5),
        },
        owner_team: {
          name: comp.owner_team?.name || '',
          email: comp.owner_team?.email || '',
          slack_channel: comp.owner_team?.slack_channel || '',
        },
        repository: {
          url: comp.repository?.url || '',
          type: comp.repository?.type || 'github',
        },
        documentation: {
          url: comp.documentation?.url || '',
          changelog_url: comp.documentation?.changelog_url || '',
        },
        tags: comp.tags?.join(', ') || '',
      });
    }
  }, [existingComponent]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: componentApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
      navigate('/components');
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
        setErrors({ general: 'Failed to create component' });
      }
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: any) => componentApi.update(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
      queryClient.invalidateQueries({ queryKey: ['component', id] });
      navigate('/components');
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
        setErrors({ general: 'Failed to update component' });
      }
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (!/^[a-zA-Z0-9-_]+$/.test(formData.name)) {
      newErrors.name = 'Name can only contain alphanumeric characters, hyphens, and underscores';
    }

    // Owner team is optional now - no validation required

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    // Only include owner_team if at least name is provided
    const ownerTeam = formData.owner_team.name.trim()
      ? {
          name: formData.owner_team.name.trim(),
          email: formData.owner_team.email.trim() || undefined,
          slack_channel: formData.owner_team.slack_channel.trim() || undefined,
        }
      : undefined;

    const payload = {
      name: formData.name.trim(),
      display_name: formData.display_name.trim() || undefined,
      category: formData.category,
      description: formData.description.trim() || undefined,
      latest_version: formData.latest_version.trim() || undefined,
      version_thresholds: {
        major_versions_behind: parseInt(formData.version_thresholds.major_versions_behind) || 1,
        minor_versions_behind: parseInt(formData.version_thresholds.minor_versions_behind) || 2,
        patch_versions_behind: parseInt(formData.version_thresholds.patch_versions_behind) || 5,
      },
      owner_team: ownerTeam,
      repository: formData.repository.url.trim()
        ? {
            url: formData.repository.url.trim(),
            type: formData.repository.type || 'github',
          }
        : undefined,
      documentation: formData.documentation.url.trim()
        ? {
            url: formData.documentation.url.trim(),
            changelog_url: formData.documentation.changelog_url.trim() || undefined,
          }
        : undefined,
      tags: formData.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    };

    if (isEditMode) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    if (name.includes('.')) {
      const [parent, child] = name.split('.');
      setFormData((prev) => ({
        ...prev,
        [parent]: {
          ...(prev[parent as keyof FormData] as Record<string, string>),
          [child]: value,
        },
      }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }

    // Clear error when field changes
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditMode ? 'Edit Component' : 'Add New Component'}
        </h1>
        <p className="mt-1 text-gray-500">
          {isEditMode
            ? 'Update the component information below'
            : 'Register a new infrastructure component'}
        </p>
      </div>

      {errors.general && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                disabled={isEditMode}
                className={`input ${errors.name ? 'border-red-500' : ''} ${isEditMode ? 'bg-gray-100' : ''}`}
                placeholder="e.g., argocd"
              />
              {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-1">
                Display Name
              </label>
              <input
                type="text"
                id="display_name"
                name="display_name"
                value={formData.display_name}
                onChange={handleChange}
                className="input"
                placeholder="e.g., Argo CD"
              />
            </div>

            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                Category <span className="text-red-500">*</span>
              </label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="input"
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              className="input"
              placeholder="Brief description of the component..."
            />
          </div>

          <div className="mt-4">
            <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
              Tags
            </label>
            <input
              type="text"
              id="tags"
              name="tags"
              value={formData.tags}
              onChange={handleChange}
              className="input"
              placeholder="e.g., gitops, kubernetes, cd (comma-separated)"
            />
          </div>
        </div>

        {/* Version Management */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Version Management</h2>
          <p className="text-sm text-gray-500 mb-4">
            Configure version tracking and upgrade thresholds for this component.
            Thresholds define how many versions behind triggers warnings (yellow) or critical (red) alerts.
          </p>

          <div className="mb-4">
            <label htmlFor="latest_version" className="block text-sm font-medium text-gray-700 mb-1">
              Latest Available Version
            </label>
            <input
              type="text"
              id="latest_version"
              name="latest_version"
              value={formData.latest_version}
              onChange={handleChange}
              className="input max-w-xs"
              placeholder="e.g., 2.9.3"
            />
            <p className="mt-1 text-xs text-gray-500">
              The latest released version of this component (semantic versioning)
            </p>
          </div>

          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Version Thresholds (Major.Minor.Patch)
          </h3>
          <p className="text-xs text-gray-500 mb-3">
            Example: Setting 1.2.5 means 1 major, 2 minor, or 5 patch versions behind will trigger an alert.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label
                htmlFor="version_thresholds.major_versions_behind"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Major Versions Behind
              </label>
              <input
                type="number"
                id="version_thresholds.major_versions_behind"
                name="version_thresholds.major_versions_behind"
                value={formData.version_thresholds.major_versions_behind}
                onChange={handleChange}
                min="0"
                className="input"
              />
              <p className="mt-1 text-xs text-gray-500">
                Major version difference threshold
              </p>
            </div>

            <div>
              <label
                htmlFor="version_thresholds.minor_versions_behind"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Minor Versions Behind
              </label>
              <input
                type="number"
                id="version_thresholds.minor_versions_behind"
                name="version_thresholds.minor_versions_behind"
                value={formData.version_thresholds.minor_versions_behind}
                onChange={handleChange}
                min="0"
                className="input"
              />
              <p className="mt-1 text-xs text-gray-500">
                Minor version difference threshold
              </p>
            </div>

            <div>
              <label
                htmlFor="version_thresholds.patch_versions_behind"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Patch Versions Behind
              </label>
              <input
                type="number"
                id="version_thresholds.patch_versions_behind"
                name="version_thresholds.patch_versions_behind"
                value={formData.version_thresholds.patch_versions_behind}
                onChange={handleChange}
                min="0"
                className="input"
              />
              <p className="mt-1 text-xs text-gray-500">
                Patch version difference threshold
              </p>
            </div>
          </div>
        </div>

        {/* Owner Team */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Owner Team</h2>
          <p className="text-sm text-gray-500 mb-4">
            Optionally specify the team responsible for this component.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label
                htmlFor="owner_team.name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Team Name
              </label>
              <input
                type="text"
                id="owner_team.name"
                name="owner_team.name"
                value={formData.owner_team.name}
                onChange={handleChange}
                className="input"
                placeholder="e.g., Platform Team"
              />
            </div>

            <div>
              <label
                htmlFor="owner_team.email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email
              </label>
              <input
                type="email"
                id="owner_team.email"
                name="owner_team.email"
                value={formData.owner_team.email}
                onChange={handleChange}
                className="input"
                placeholder="e.g., platform@example.com"
              />
            </div>

            <div>
              <label
                htmlFor="owner_team.slack_channel"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Slack Channel
              </label>
              <input
                type="text"
                id="owner_team.slack_channel"
                name="owner_team.slack_channel"
                value={formData.owner_team.slack_channel}
                onChange={handleChange}
                className="input"
                placeholder="e.g., #platform-team"
              />
            </div>
          </div>
        </div>

        {/* Repository & Documentation */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Repository & Documentation</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="repository.url"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Repository URL
              </label>
              <input
                type="url"
                id="repository.url"
                name="repository.url"
                value={formData.repository.url}
                onChange={handleChange}
                className="input"
                placeholder="e.g., https://github.com/argoproj/argo-cd"
              />
            </div>

            <div>
              <label
                htmlFor="repository.type"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Repository Type
              </label>
              <select
                id="repository.type"
                name="repository.type"
                value={formData.repository.type}
                onChange={handleChange}
                className="input"
              >
                <option value="github">GitHub</option>
                <option value="gitlab">GitLab</option>
                <option value="bitbucket">Bitbucket</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="documentation.url"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Documentation URL
              </label>
              <input
                type="url"
                id="documentation.url"
                name="documentation.url"
                value={formData.documentation.url}
                onChange={handleChange}
                className="input"
                placeholder="e.g., https://argo-cd.readthedocs.io"
              />
            </div>

            <div>
              <label
                htmlFor="documentation.changelog_url"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Changelog URL
              </label>
              <input
                type="url"
                id="documentation.changelog_url"
                name="documentation.changelog_url"
                value={formData.documentation.changelog_url}
                onChange={handleChange}
                className="input"
                placeholder="e.g., https://github.com/.../releases"
              />
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/components')}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? 'Saving...' : isEditMode ? 'Update Component' : 'Create Component'}
          </button>
        </div>
      </form>
    </div>
  );
}

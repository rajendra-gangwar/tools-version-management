import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { categoryApi } from '../services/api';
import type { Category } from '../types';

interface FormData {
  name: string;
  display_name: string;
  description: string;
  color: string;
}

const initialFormData: FormData = {
  name: '',
  display_name: '',
  description: '',
  color: '#3B82F6',
};

// Predefined color options for categories
const colorOptions = [
  { label: 'Blue', value: '#3B82F6' },
  { label: 'Green', value: '#10B981' },
  { label: 'Purple', value: '#8B5CF6' },
  { label: 'Orange', value: '#F97316' },
  { label: 'Red', value: '#EF4444' },
  { label: 'Teal', value: '#14B8A6' },
  { label: 'Pink', value: '#EC4899' },
  { label: 'Indigo', value: '#6366F1' },
  { label: 'Yellow', value: '#EAB308' },
  { label: 'Gray', value: '#6B7280' },
];

export default function CategoriesManagementPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoryApi.list({ limit: 100 }),
  });

  const categories: Category[] = data?.data?.data || [];

  const createMutation = useMutation({
    mutationFn: categoryApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      resetForm();
    },
    onError: (error: any) => {
      handleError(error);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      categoryApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      resetForm();
    },
    onError: (error: any) => {
      handleError(error);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: categoryApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
  });

  const seedMutation = useMutation({
    mutationFn: categoryApi.seedDefaults,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    },
    onError: (error: any) => {
      handleError(error);
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

  const handleEdit = (cat: Category) => {
    setFormData({
      name: cat.name,
      display_name: cat.display_name || '',
      description: cat.description || '',
      color: cat.color || '#3B82F6',
    });
    setEditingId(cat.id);
    setShowForm(true);
  };

  const handleDelete = (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete category "${name}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (!/^[a-zA-Z0-9-]+$/.test(formData.name)) {
      newErrors.name = 'Name can only contain letters, numbers, and hyphens';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    const payload = {
      name: formData.name.trim().toLowerCase(),
      display_name: formData.display_name.trim() || undefined,
      description: formData.description.trim() || undefined,
      color: formData.color || undefined,
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
          <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
          <p className="mt-1 text-gray-500">
            Manage component categories for organizing infrastructure components
          </p>
        </div>
        <div className="flex gap-3">
          {categories.length === 0 && (
            <button
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
              className="btn btn-secondary"
            >
              {seedMutation.isPending ? 'Seeding...' : 'Seed Defaults'}
            </button>
          )}
          <button
            onClick={() => {
              resetForm();
              setShowForm(true);
            }}
            className="btn btn-primary"
          >
            Add Category
          </button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            {editingId ? 'Edit Category' : 'Add New Category'}
          </h2>

          {errors.general && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  placeholder="e.g., monitoring"
                />
                {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name}</p>}
                <p className="mt-1 text-xs text-gray-500">
                  Lowercase, hyphens allowed (e.g., ci-cd, service-mesh)
                </p>
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
                  placeholder="e.g., Monitoring & Observability"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Color
                </label>
                <div className="flex gap-2 items-center">
                  <select
                    name="color"
                    value={formData.color}
                    onChange={handleChange}
                    className="input flex-1"
                  >
                    {colorOptions.map((color) => (
                      <option key={color.value} value={color.value}>
                        {color.label}
                      </option>
                    ))}
                  </select>
                  <div
                    className="w-10 h-10 rounded border border-gray-300"
                    style={{ backgroundColor: formData.color }}
                  />
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={2}
                  className="input"
                  placeholder="Optional description for this category..."
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

      {/* Categories Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <div className="col-span-full p-8 text-center text-gray-500">Loading...</div>
        ) : categories.length === 0 ? (
          <div className="col-span-full card text-center py-12">
            <p className="text-gray-500 mb-4">
              No categories found. Create your first category or seed the default categories.
            </p>
            <button
              onClick={() => seedMutation.mutate()}
              disabled={seedMutation.isPending}
              className="btn btn-primary"
            >
              {seedMutation.isPending ? 'Seeding...' : 'Seed Default Categories'}
            </button>
          </div>
        ) : (
          categories.map((cat) => (
            <div key={cat.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: cat.color || '#6B7280' }}
                  />
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {cat.display_name || cat.name}
                    </h3>
                    {cat.display_name && (
                      <p className="text-sm text-gray-500 font-mono">{cat.name}</p>
                    )}
                  </div>
                </div>
                <span
                  className={`badge ${cat.is_active ? 'badge-success' : 'badge-gray'}`}
                >
                  {cat.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              {cat.description && (
                <p className="mt-2 text-sm text-gray-600">{cat.description}</p>
              )}
              <div className="mt-4 flex justify-end gap-2">
                <button
                  onClick={() => handleEdit(cat)}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(cat.id, cat.name)}
                  className="text-sm text-red-600 hover:text-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

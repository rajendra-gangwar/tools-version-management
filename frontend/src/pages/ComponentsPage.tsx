import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { componentApi, categoryApi } from '../services/api';
import type { Component, Category } from '../types';

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

export default function ComponentsPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('');

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

  const { data, isLoading } = useQuery({
    queryKey: ['components', { search, category }],
    queryFn: () =>
      componentApi.list({
        search: search || undefined,
        category: category || undefined,
        limit: 50,
      }),
  });

  const components: Component[] = data?.data?.data || [];
  const pagination = data?.data?.pagination;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Components</h1>
          <p className="mt-1 text-gray-500">
            Manage your infrastructure component registry
          </p>
        </div>
        <Link to="/components/new" className="btn btn-primary">
          Add Component
        </Link>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search components..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input"
            />
          </div>
          <div className="w-full sm:w-48">
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="input"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Components Table */}
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
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Owner
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Tags
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Updated
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {components.map((component) => (
                <tr key={component.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link
                      to={`/components/${component.id}`}
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {component.display_name || component.name}
                    </Link>
                    <p className="text-sm text-gray-500 font-mono">
                      {component.name}
                    </p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="badge badge-info">{component.category}</span>
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {component.owner_team?.name}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {component.tags?.slice(0, 3).map((tag) => (
                        <span key={tag} className="badge badge-gray">
                          {tag}
                        </span>
                      ))}
                      {component.tags?.length > 3 && (
                        <span className="badge badge-gray">
                          +{component.tags.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(component.updated_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
              {components.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    No components found. Create your first component to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {/* Pagination info */}
        {pagination && (
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-sm text-gray-500">
            Showing {components.length} of {pagination.total} components
          </div>
        )}
      </div>
    </div>
  );
}

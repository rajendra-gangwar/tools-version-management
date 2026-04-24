import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { mappingApi } from '../services/api';
import type { EnvironmentMatrix, UpgradeStatus } from '../types';

const rowsPerPageOptions = [10, 25, 50, 100];

export default function EnvironmentMatrixPage() {
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [currentPage, setCurrentPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ['environmentMatrix'],
    queryFn: () => mappingApi.getMatrix(),
  });

  const matrix: EnvironmentMatrix | undefined = data?.data;

  // Export to JSON
  const handleExportJSON = () => {
    if (!matrix) return;
    const blob = new Blob([JSON.stringify(matrix, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `environment-matrix-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Export to Excel (CSV format that Excel can open)
  const handleExportExcel = () => {
    if (!matrix) return;

    // Build CSV content
    const headers = ['Component', 'Latest Version', ...columns];
    const rows = paginatedComponents.map((component) => {
      const row = [
        component.componentName,
        component.latestVersion || '-',
        ...columns.map((col) => {
          const versionInfo = component.versions[col];
          if (!versionInfo) return '-';
          return `${versionInfo.version} (${versionInfo.upgradeStatus || 'unknown'})`;
        }),
      ];
      return row.map((cell) => `"${cell}"`).join(',');
    });

    const csvContent = [headers.map((h) => `"${h}"`).join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `environment-matrix-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Get upgrade status color
  const getUpgradeStatusColor = (status?: UpgradeStatus) => {
    switch (status) {
      case 'up_to_date':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'upgrade_recommended':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'critical_upgrade':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };


  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  if (!matrix || matrix.components.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Environment Matrix</h1>
          <p className="mt-1 text-gray-500">
            View component versions across all environments
          </p>
        </div>
        <div className="card text-center py-12 text-gray-500">
          No data available. Add components and mappings to see the matrix.
        </div>
      </div>
    );
  }

  // Get unique environment keys
  const envKeys = new Set<string>();
  matrix.components.forEach((comp) => {
    Object.keys(comp.versions).forEach((key) => envKeys.add(key));
  });
  const columns = Array.from(envKeys).sort();

  // Pagination
  const totalComponents = matrix.components.length;
  const totalPages = Math.ceil(totalComponents / rowsPerPage);
  const startIndex = currentPage * rowsPerPage;
  const paginatedComponents = matrix.components.slice(startIndex, startIndex + rowsPerPage);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Environment Matrix</h1>
          <p className="mt-1 text-gray-500">
            View component versions across all environments
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportJSON}
            className="btn btn-secondary text-sm"
          >
            Export JSON
          </button>
          <button
            onClick={handleExportExcel}
            className="btn btn-secondary text-sm"
          >
            Export Excel
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="flex items-center gap-2">
            <label htmlFor="rowsPerPage" className="text-sm text-gray-600">
              Rows per page:
            </label>
            <select
              id="rowsPerPage"
              value={rowsPerPage}
              onChange={(e) => {
                setRowsPerPage(Number(e.target.value));
                setCurrentPage(0);
              }}
              className="input w-20"
            >
              {rowsPerPageOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
          <div className="text-sm text-gray-600">
            Showing {startIndex + 1}-{Math.min(startIndex + rowsPerPage, totalComponents)} of {totalComponents} components
          </div>
        </div>
      </div>

      {/* Matrix Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto overflow-y-auto max-h-[600px]">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase sticky left-0 bg-gray-50 z-20 min-w-[200px]">
                  Component
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase min-w-[100px]">
                  Latest
                </th>
                {columns.map((col) => {
                  const parts = col.split(':');
                  const envName = parts[0];
                  const cluster = parts.length > 1 ? parts[1] : null;
                  return (
                    <th
                      key={col}
                      className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase min-w-[120px]"
                    >
                      <div>{envName}</div>
                      {cluster && <div className="text-gray-400 font-normal">{cluster}</div>}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedComponents.map((component) => (
                <tr key={component.componentId} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium sticky left-0 bg-white z-10">
                    <div className="flex flex-col">
                      <span>{component.componentName}</span>
                      {component.versionThresholds && (
                        <span className="text-xs text-gray-400">
                          Thresholds: {component.versionThresholds.majorVersionsBehind}.{component.versionThresholds.minorVersionsBehind}.{component.versionThresholds.patchVersionsBehind}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {component.latestVersion ? (
                      <span className="font-mono text-sm text-primary-600 font-medium">
                        {component.latestVersion}
                      </span>
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </td>
                  {columns.map((col) => {
                    const versionInfo = component.versions[col];

                    return (
                      <td key={col} className="px-4 py-3 text-center">
                        {versionInfo ? (
                          <span
                            className={`inline-block px-2 py-1 rounded text-xs font-mono border ${getUpgradeStatusColor(versionInfo.upgradeStatus)}`}
                          >
                            {versionInfo.version}
                          </span>
                        ) : (
                          <span className="text-gray-300">-</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex justify-between items-center">
            <button
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
              className="btn btn-secondary text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              Page {currentPage + 1} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage === totalPages - 1}
              className="btn btn-secondary text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="card">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Upgrade Status Legend</h3>
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-xs bg-green-100 text-green-800 border border-green-200">
              Up to date
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-xs bg-yellow-100 text-yellow-800 border border-yellow-200">
              Upgrade recommended
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-xs bg-red-100 text-red-800 border border-red-200">
              Critical upgrade
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

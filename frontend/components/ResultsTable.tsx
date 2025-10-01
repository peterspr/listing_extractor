/**
 * Results table component with sorting, filtering, and selection
 */
'use client';

import { useState, useMemo } from 'react';
import { ExtractionResultData } from '@/types';

interface ResultsTableProps {
  results: ExtractionResultData[];
  onDownloadSelected: (selectedIds: string[]) => void;
  onDownloadAll: () => void;
}

export default function ResultsTable({
  results,
  onDownloadSelected,
  onDownloadAll,
}: ResultsTableProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [sortKey, setSortKey] = useState<string>('filename');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  // Get successful results
  const successfulResults = useMemo(
    () => results.filter((r) => r.success),
    [results]
  );

  // Sort results
  const sortedResults = useMemo(() => {
    return [...successfulResults].sort((a, b) => {
      const aVal = sortKey === 'filename' ? a.filename : '';
      const bVal = sortKey === 'filename' ? b.filename : '';

      if (sortOrder === 'asc') {
        return aVal.localeCompare(bVal);
      } else {
        return bVal.localeCompare(aVal);
      }
    });
  }, [successfulResults, sortKey, sortOrder]);

  const handleSelectAll = () => {
    if (selectedIds.size === successfulResults.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(successfulResults.map((r) => r.file_id)));
    }
  };

  const handleSelectRow = (fileId: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(fileId)) {
      newSelected.delete(fileId);
    } else {
      newSelected.add(fileId);
    }
    setSelectedIds(newSelected);
  };

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const toggleExpandRow = (fileId: string) => {
    setExpandedRow(expandedRow === fileId ? null : fileId);
  };

  const exportToCSV = (data: ExtractionResultData[]) => {
    if (!data.length || !data[0].data) return;

    const headers = Object.keys(data[0].data);
    const csvRows = [
      headers.join(','),
      ...data.map((result) =>
        headers.map((header) => result.data?.[header] || 'N/A').join(',')
      ),
    ];

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `extraction_results_${new Date().toISOString()}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
  };

  if (successfulResults.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <p className="text-gray-500">No successful extractions to display</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Header with actions */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">Extraction Results</h3>
          <p className="text-sm text-gray-600">
            {successfulResults.length} successful extractions
            {selectedIds.size > 0 && ` · ${selectedIds.size} selected`}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => exportToCSV(sortedResults)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Download All
          </button>
          {selectedIds.size > 0 && (
            <button
              onClick={() => {
                const selected = sortedResults.filter((r) => selectedIds.has(r.file_id));
                exportToCSV(selected);
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              Download Selected ({selectedIds.size})
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  checked={selectedIds.size === successfulResults.length}
                  onChange={handleSelectAll}
                  className="rounded border-gray-300"
                />
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('filename')}
              >
                <div className="flex items-center">
                  Filename
                  {sortKey === 'filename' && (
                    <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Address
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Shell SF
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Shell Rate
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedResults.map((result) => (
              <>
                <tr key={result.file_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(result.file_id)}
                      onChange={() => handleSelectRow(result.file_id)}
                      className="rounded border-gray-300"
                    />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">{result.filename}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {result.data?.Address || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {result.data?.['Shell SF'] || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {result.data?.['Shell Rate'] || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      onClick={() => toggleExpandRow(result.file_id)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      {expandedRow === result.file_id ? 'Collapse' : 'View Details'}
                    </button>
                  </td>
                </tr>
                {expandedRow === result.file_id && result.data && (
                  <tr key={`${result.file_id}-expanded`}>
                    <td colSpan={6} className="px-6 py-4 bg-gray-50">
                      <div className="grid grid-cols-2 gap-4">
                        {Object.entries(result.data).map(([key, value]) => (
                          <div key={key}>
                            <span className="text-xs font-medium text-gray-500">{key}:</span>
                            <span className="ml-2 text-sm text-gray-900">{value}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

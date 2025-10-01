/**
 * Progress indicator component showing extraction progress
 */
'use client';

import { ProgressUpdate } from '@/types';

interface ProgressIndicatorProps {
  progress: ProgressUpdate;
}

export default function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  return (
    <div className="w-full bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-semibold">Processing PDFs</h3>
          <span className="text-sm text-gray-600">
            {progress.completed_files + progress.failed_files} / {progress.total_files}
          </span>
        </div>

        {/* Overall progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progress.overall_progress}%` }}
          />
        </div>

        <div className="mt-2 text-sm text-gray-600">
          {progress.overall_progress}% complete
        </div>
      </div>

      {/* Current file being processed */}
      {progress.current_file && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Current: {progress.current_file.filename}
            </span>
            <span className="text-xs text-gray-500 capitalize">
              {progress.current_file.status}
            </span>
          </div>

          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                progress.current_file.status === 'failed' ? 'bg-red-500' : 'bg-green-500'
              }`}
              style={{ width: `${progress.current_file.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="flex justify-between text-sm">
        <div>
          <span className="text-green-600 font-medium">{progress.completed_files} successful</span>
        </div>
        {progress.failed_files > 0 && (
          <div>
            <span className="text-red-600 font-medium">{progress.failed_files} failed</span>
          </div>
        )}
      </div>

      {/* Status indicator */}
      <div className="mt-4 flex items-center justify-center">
        {progress.status === 'completed' ? (
          <div className="flex items-center text-green-600">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-medium">Extraction Complete!</span>
          </div>
        ) : progress.status === 'failed' ? (
          <div className="flex items-center text-red-600">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <span className="font-medium">Extraction Failed</span>
          </div>
        ) : (
          <div className="flex items-center text-blue-600">
            <svg className="animate-spin w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="font-medium">Processing...</span>
          </div>
        )}
      </div>
    </div>
  );
}

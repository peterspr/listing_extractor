/**
 * Main page - PDF upload and extraction interface
 */
'use client';

import { useState, useCallback } from 'react';
import FileUploader from '@/components/FileUploader';
import ProgressIndicator from '@/components/ProgressIndicator';
import ResultsTable from '@/components/ResultsTable';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useExtraction } from '@/hooks/useExtraction';
import { UploadedFile } from '@/types';

export default function Home() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [sessionId, setSessionId] = useState<string>('');

  const { upload, uploading, error: uploadError, uploadResponse, reset: resetUpload } = useFileUpload();
  const {
    startExtraction,
    extracting,
    error: extractionError,
    extractionResponse,
    progress,
    reset: resetExtraction,
  } = useExtraction();

  const handleFilesSelected = useCallback((files: File[]) => {
    setSelectedFiles(files);
  }, []);

  const handleUpload = useCallback(async () => {
    try {
      const response = await upload(selectedFiles);
      setUploadedFiles(response.files);
      setSessionId(response.session_id);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  }, [selectedFiles, upload]);

  const handleAnalyze = useCallback(async () => {
    if (!sessionId || uploadedFiles.length === 0) return;

    try {
      await startExtraction(
        sessionId,
        uploadedFiles.map((f) => ({
          file_id: f.file_id,
          filename: f.filename,
          path: f.path,
        }))
      );
    } catch (err) {
      console.error('Extraction failed:', err);
    }
  }, [sessionId, uploadedFiles, startExtraction]);

  const handleReset = useCallback(() => {
    setSelectedFiles([]);
    setUploadedFiles([]);
    setSessionId('');
    resetUpload();
    resetExtraction();
  }, [resetUpload, resetExtraction]);

  const handleDownloadSelected = useCallback((selectedIds: string[]) => {
    // Download selected results
    console.log('Download selected:', selectedIds);
  }, []);

  const handleDownloadAll = useCallback(() => {
    // Download all results
    console.log('Download all');
  }, []);

  return (
    <main className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Commercial Real Estate PDF Extractor
          </h1>
          <p className="text-gray-600">
            Upload PDF listings to extract structured data automatically
          </p>
        </div>

        {/* Error messages */}
        {(uploadError || extractionError) && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-red-600 mr-2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-red-800">{uploadError || extractionError}</p>
            </div>
          </div>
        )}

        {/* Upload Section */}
        {!uploadedFiles.length && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Upload PDFs</h2>
            <FileUploader onFilesSelected={handleFilesSelected} disabled={uploading} />

            {selectedFiles.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">
                  Selected Files ({selectedFiles.length})
                </h3>
                <ul className="space-y-2">
                  {selectedFiles.map((file, index) => (
                    <li
                      key={index}
                      className="flex items-center justify-between bg-gray-50 rounded p-2"
                    >
                      <span className="text-sm text-gray-700">{file.name}</span>
                      <span className="text-xs text-gray-500">
                        {(file.size / (1024 * 1024)).toFixed(2)} MB
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className={`
                    mt-4 w-full px-6 py-3 rounded-md font-medium
                    transition-colors duration-200
                    ${
                      uploading
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }
                  `}
                >
                  {uploading ? 'Uploading...' : 'Upload Files'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Uploaded Files - Ready to Analyze */}
        {uploadedFiles.length > 0 && !extracting && !extractionResponse && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Ready to Analyze</h2>
            <p className="text-gray-600 mb-4">
              {uploadedFiles.length} file{uploadedFiles.length !== 1 ? 's' : ''} uploaded successfully
            </p>

            <button
              onClick={handleAnalyze}
              className="w-full px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-md font-medium transition-colors"
            >
              Analyze Files
            </button>
          </div>
        )}

        {/* Progress Indicator */}
        {extracting && progress && (
          <div className="mb-6">
            <ProgressIndicator progress={progress} />
          </div>
        )}

        {/* Results Table */}
        {extractionResponse && (
          <>
            <div className="mb-6">
              <ResultsTable
                results={extractionResponse.results}
                onDownloadSelected={handleDownloadSelected}
                onDownloadAll={handleDownloadAll}
              />
            </div>

            {/* Failed extractions */}
            {extractionResponse.failed > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-red-800 mb-2">
                  Failed Extractions ({extractionResponse.failed})
                </h3>
                <ul className="space-y-2">
                  {extractionResponse.errors.map((error, index) => (
                    <li key={index} className="text-sm text-red-700">
                      <span className="font-medium">{error.filename}:</span> {error.error}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Start Over */}
            <button
              onClick={handleReset}
              className="w-full px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-md font-medium transition-colors"
            >
              Start Over
            </button>
          </>
        )}
      </div>
    </main>
  );
}

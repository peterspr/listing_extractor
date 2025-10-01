/**
 * Hook for file upload functionality
 */
import { useState, useCallback } from 'react';
import { uploadFiles } from '@/lib/api';
import { UploadResponse } from '@/types';

export function useFileUpload() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);

  const upload = useCallback(async (files: File[]) => {
    setUploading(true);
    setError(null);

    try {
      const response = await uploadFiles(files);
      setUploadResponse(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      throw err;
    } finally {
      setUploading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setUploadResponse(null);
    setError(null);
    setUploading(false);
  }, []);

  return {
    upload,
    uploading,
    error,
    uploadResponse,
    reset,
  };
}

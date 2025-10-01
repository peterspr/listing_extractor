/**
 * API client for backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

export interface ApiError {
  error: string;
  message?: string;
}

/**
 * Upload files to the backend
 */
export async function uploadFiles(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Upload failed');
  }

  return response.json();
}

/**
 * Start extraction process
 */
export async function extractPDFs(sessionId: string, files: Array<{ file_id: string; filename: string; path: string }>) {
  const response = await fetch(`${API_BASE_URL}/extract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      files: files,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Extraction failed');
  }

  return response.json();
}

/**
 * Create SSE connection for progress updates
 */
export function createProgressStream(sessionId: string) {
  return new EventSource(`${API_BASE_URL}/progress/${sessionId}`);
}

/**
 * Download results as CSV
 */
export async function downloadResults(
  sessionId: string,
  fileIds?: string[],
  combine: boolean = true
) {
  const params = new URLSearchParams();
  if (fileIds && fileIds.length > 0) {
    params.append('file_ids', fileIds.join(','));
  }
  params.append('combine', combine.toString());

  const response = await fetch(`${API_BASE_URL}/download/${sessionId}?${params.toString()}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Download failed');
  }

  return response.blob();
}

/**
 * Delete session
 */
export async function deleteSession(sessionId: string) {
  const response = await fetch(`${API_BASE_URL}/session/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Delete failed');
  }

  return response.json();
}

/**
 * Health check
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return response.json();
}

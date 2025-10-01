/**
 * Hook for PDF extraction with progress tracking
 */
import { useState, useCallback, useEffect, useRef } from 'react';
import { extractPDFs, createProgressStream } from '@/lib/api';
import { ExtractionResponse, ProgressUpdate } from '@/types';

export function useExtraction() {
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractionResponse, setExtractionResponse] = useState<ExtractionResponse | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startExtraction = useCallback(
    async (
      sessionId: string,
      files: Array<{ file_id: string; filename: string; path: string }>
    ) => {
      setExtracting(true);
      setError(null);
      setProgress(null);

      try {
        // Start SSE connection for progress updates
        const eventSource = createProgressStream(sessionId);
        eventSourceRef.current = eventSource;

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setProgress(data);
          } catch (err) {
            console.error('Error parsing progress update:', err);
          }
        };

        eventSource.onerror = (err) => {
          console.error('SSE error:', err);
          eventSource.close();
        };

        // Start extraction
        const response = await extractPDFs(sessionId, files);
        setExtractionResponse(response);

        return response;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Extraction failed';
        setError(errorMessage);
        throw err;
      } finally {
        setExtracting(false);
        // Close SSE connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }
      }
    },
    []
  );

  const reset = useCallback(() => {
    setExtractionResponse(null);
    setError(null);
    setExtracting(false);
    setProgress(null);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    startExtraction,
    extracting,
    error,
    extractionResponse,
    progress,
    reset,
  };
}

/**
 * Type definitions for the application
 */

export interface UploadedFile {
  file_id: string;
  filename: string;
  size: number;
  upload_time: string;
  path: string;
}

export interface UploadResponse {
  session_id: string;
  files: UploadedFile[];
  total_files: number;
  errors?: Array<{ filename: string; error: string }>;
}

export interface ExtractionResultData {
  file_id: string;
  filename: string;
  success: boolean;
  csv_row?: string;
  data?: Record<string, string>;
  error_message?: string;
}

export interface ExtractionResponse {
  session_id: string;
  total_files: number;
  successful: number;
  failed: number;
  results: ExtractionResultData[];
  errors: Array<{ file_id: string; filename: string; error: string }>;
}

export interface ProgressUpdate {
  session_id: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  overall_progress: number;
  status: string;
  current_file?: {
    file_id: string;
    filename: string;
    status: string;
    progress: number;
    error_message?: string;
  };
  files: Record<string, {
    file_id: string;
    filename: string;
    status: string;
    progress: number;
    error_message?: string;
  }>;
}

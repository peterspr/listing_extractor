"""
Data schemas and validation models
"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class UploadedFile:
    """Metadata for an uploaded file"""
    file_id: str
    filename: str
    size: int
    upload_time: str
    path: str


@dataclass
class UploadResponse:
    """Response for file upload"""
    session_id: str
    files: List[UploadedFile]
    total_files: int


@dataclass
class ExtractionRequest:
    """Request to extract PDFs"""
    session_id: str
    file_ids: Optional[List[str]] = None  # If None, extract all files in session


@dataclass
class ExtractionResultData:
    """Extraction result for a single file"""
    file_id: str
    filename: str
    success: bool
    csv_row: Optional[str] = None
    data: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None


@dataclass
class ExtractionResponse:
    """Response for extraction request"""
    session_id: str
    total_files: int
    successful: int
    failed: int
    results: List[ExtractionResultData]
    errors: List[Dict[str, str]]


@dataclass
class DownloadRequest:
    """Request to download results"""
    session_id: str
    file_ids: Optional[List[str]] = None  # If None, download all
    format: str = 'csv'  # csv, json
    combine: bool = False  # Combine into single file or individual files


@dataclass
class ErrorResponse:
    """Error response"""
    error: str
    message: str
    status_code: int = 400


def validate_file_extension(filename: str, allowed_extensions: set) -> bool:
    """Validate file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_file_size(size: int, max_size: int) -> bool:
    """Validate file size"""
    return 0 < size <= max_size


def parse_csv_row_to_dict(csv_row: str, headers: List[str]) -> Dict[str, str]:
    """Parse CSV row into dictionary"""
    values = [v.strip() for v in csv_row.split(',')]

    # Ensure we have the right number of values
    while len(values) < len(headers):
        values.append("N/A")

    # Truncate if too many values
    values = values[:len(headers)]

    return dict(zip(headers, values))

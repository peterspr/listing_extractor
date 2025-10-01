"""
Storage service abstraction layer
Supports local filesystem storage with future extensibility to S3/GCS
"""
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract base class for storage services"""

    @abstractmethod
    def save_file(self, file: BinaryIO, session_id: str, filename: str) -> str:
        """Save a file and return its storage path"""
        pass

    @abstractmethod
    def get_file_path(self, session_id: str, filename: str) -> str:
        """Get the path to a stored file"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Delete all files for a session"""
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """Check if session directory exists"""
        pass

    @abstractmethod
    def list_files(self, session_id: str) -> list[str]:
        """List all files in a session"""
        pass


class LocalStorageService(StorageService):
    """Local filesystem storage implementation"""

    def __init__(self, upload_folder: str, results_folder: str):
        self.upload_folder = Path(upload_folder)
        self.results_folder = Path(results_folder)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        self.results_folder.mkdir(parents=True, exist_ok=True)

    def _get_session_upload_dir(self, session_id: str) -> Path:
        """Get upload directory for session"""
        return self.upload_folder / session_id

    def _get_session_results_dir(self, session_id: str) -> Path:
        """Get results directory for session"""
        return self.results_folder / session_id

    def save_file(self, file: BinaryIO, session_id: str, filename: str) -> str:
        """
        Save uploaded file to session directory

        Args:
            file: File object to save
            session_id: Session identifier
            filename: Original filename

        Returns:
            Path to saved file
        """
        # Secure the filename
        safe_filename = secure_filename(filename)

        # Create session directory
        session_dir = self._get_session_upload_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = session_dir / safe_filename
        file.save(str(file_path))

        logger.info(f"Saved file {safe_filename} to session {session_id}")
        return str(file_path)

    def get_file_path(self, session_id: str, filename: str) -> str:
        """Get path to a file in session"""
        safe_filename = secure_filename(filename)
        file_path = self._get_session_upload_dir(session_id) / safe_filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        return str(file_path)

    def save_result(self, session_id: str, filename: str, content: str) -> str:
        """
        Save extraction result

        Args:
            session_id: Session identifier
            filename: Result filename
            content: File content

        Returns:
            Path to saved result file
        """
        session_dir = self._get_session_results_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        result_path = session_dir / filename
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Saved result {filename} for session {session_id}")
        return str(result_path)

    def get_result_path(self, session_id: str, filename: str) -> str:
        """Get path to a result file"""
        result_path = self._get_session_results_dir(session_id) / filename

        if not result_path.exists():
            raise FileNotFoundError(f"Result not found: {filename}")

        return str(result_path)

    def delete_session(self, session_id: str) -> None:
        """Delete all files for a session"""
        try:
            # Delete upload directory
            upload_dir = self._get_session_upload_dir(session_id)
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
                logger.info(f"Deleted upload directory for session {session_id}")

            # Delete results directory
            results_dir = self._get_session_results_dir(session_id)
            if results_dir.exists():
                shutil.rmtree(results_dir)
                logger.info(f"Deleted results directory for session {session_id}")

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            raise

    def session_exists(self, session_id: str) -> bool:
        """Check if session directory exists"""
        return self._get_session_upload_dir(session_id).exists()

    def list_files(self, session_id: str) -> list[str]:
        """List all files in a session"""
        session_dir = self._get_session_upload_dir(session_id)

        if not session_dir.exists():
            return []

        return [f.name for f in session_dir.iterdir() if f.is_file()]


# Future implementation placeholder
class S3StorageService(StorageService):
    """S3 storage implementation (for future use)"""

    def __init__(self, bucket_name: str, region: str):
        self.bucket_name = bucket_name
        self.region = region
        # TODO: Initialize boto3 client
        raise NotImplementedError("S3 storage not yet implemented")

    def save_file(self, file: BinaryIO, session_id: str, filename: str) -> str:
        raise NotImplementedError("S3 storage not yet implemented")

    def get_file_path(self, session_id: str, filename: str) -> str:
        raise NotImplementedError("S3 storage not yet implemented")

    def delete_session(self, session_id: str) -> None:
        raise NotImplementedError("S3 storage not yet implemented")

    def session_exists(self, session_id: str) -> bool:
        raise NotImplementedError("S3 storage not yet implemented")

    def list_files(self, session_id: str) -> list[str]:
        raise NotImplementedError("S3 storage not yet implemented")

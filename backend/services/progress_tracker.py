"""
Progress tracking service for real-time extraction progress updates via SSE
"""
import logging
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ExtractionStatus(Enum):
    """Status of extraction process"""
    PENDING = "pending"
    EXTRACTING = "extracting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileProgress:
    """Progress information for a single file"""
    file_id: str
    filename: str
    status: str
    progress: int  # 0-100
    error_message: Optional[str] = None


@dataclass
class SessionProgress:
    """Overall progress for a session"""
    session_id: str
    total_files: int
    completed_files: int
    failed_files: int
    current_file: Optional[FileProgress] = None
    overall_progress: int = 0  # 0-100
    status: str = ExtractionStatus.PENDING.value


class ProgressTracker:
    """
    Tracks extraction progress for multiple sessions
    Thread-safe implementation for concurrent extractions
    """

    def __init__(self):
        self._sessions: Dict[str, SessionProgress] = {}
        self._file_progress: Dict[str, Dict[str, FileProgress]] = {}

    def initialize_session(
        self,
        session_id: str,
        file_ids: list[str],
        filenames: list[str]
    ):
        """
        Initialize progress tracking for a session

        Args:
            session_id: Session identifier
            file_ids: List of file identifiers
            filenames: List of filenames
        """
        # Create session progress
        self._sessions[session_id] = SessionProgress(
            session_id=session_id,
            total_files=len(file_ids),
            completed_files=0,
            failed_files=0,
            overall_progress=0,
            status=ExtractionStatus.PENDING.value
        )

        # Initialize file progress
        self._file_progress[session_id] = {}
        for file_id, filename in zip(file_ids, filenames):
            self._file_progress[session_id][file_id] = FileProgress(
                file_id=file_id,
                filename=filename,
                status=ExtractionStatus.PENDING.value,
                progress=0
            )

        logger.info(f"Initialized progress tracking for session {session_id} with {len(file_ids)} files")

    def update_file_progress(
        self,
        session_id: str,
        file_id: str,
        status: str,
        progress: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Update progress for a specific file

        Args:
            session_id: Session identifier
            file_id: File identifier
            status: File status (ExtractionStatus)
            progress: Progress percentage (0-100)
            error_message: Error message if failed
        """
        if session_id not in self._file_progress:
            logger.warning(f"Session {session_id} not found in progress tracker")
            return

        if file_id not in self._file_progress[session_id]:
            logger.warning(f"File {file_id} not found in session {session_id}")
            return

        # Update file progress
        file_progress = self._file_progress[session_id][file_id]
        file_progress.status = status
        file_progress.progress = progress
        file_progress.error_message = error_message

        # Update session progress
        self._update_session_progress(session_id, file_id)

        logger.debug(f"Updated progress for {file_id} in session {session_id}: {status} ({progress}%)")

    def _update_session_progress(self, session_id: str, current_file_id: str):
        """Update overall session progress"""
        if session_id not in self._sessions:
            return

        session = self._sessions[session_id]
        files = self._file_progress[session_id]

        # Count completed and failed files
        completed = sum(1 for f in files.values() if f.status == ExtractionStatus.COMPLETED.value)
        failed = sum(1 for f in files.values() if f.status == ExtractionStatus.FAILED.value)

        session.completed_files = completed
        session.failed_files = failed

        # Set current file
        session.current_file = files.get(current_file_id)

        # Calculate overall progress
        if session.total_files > 0:
            session.overall_progress = int(((completed + failed) / session.total_files) * 100)
        else:
            session.overall_progress = 100

        # Determine overall status
        if completed + failed == session.total_files:
            if failed == session.total_files:
                session.status = ExtractionStatus.FAILED.value
            else:
                session.status = ExtractionStatus.COMPLETED.value
        elif completed + failed > 0:
            session.status = ExtractionStatus.PROCESSING.value
        else:
            session.status = ExtractionStatus.PENDING.value

    def get_session_progress(self, session_id: str) -> Optional[SessionProgress]:
        """Get current progress for a session"""
        return self._sessions.get(session_id)

    def get_file_progress(self, session_id: str, file_id: str) -> Optional[FileProgress]:
        """Get progress for a specific file"""
        if session_id in self._file_progress:
            return self._file_progress[session_id].get(file_id)
        return None

    def get_all_files_progress(self, session_id: str) -> Dict[str, FileProgress]:
        """Get progress for all files in a session"""
        return self._file_progress.get(session_id, {})

    def remove_session(self, session_id: str):
        """Remove session from tracker (cleanup)"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        if session_id in self._file_progress:
            del self._file_progress[session_id]
        logger.info(f"Removed session {session_id} from progress tracker")

    def to_dict(self, session_id: str) -> dict:
        """Convert session progress to dictionary for JSON serialization"""
        session = self.get_session_progress(session_id)
        if not session:
            return {}

        return {
            'session_id': session.session_id,
            'total_files': session.total_files,
            'completed_files': session.completed_files,
            'failed_files': session.failed_files,
            'overall_progress': session.overall_progress,
            'status': session.status,
            'current_file': asdict(session.current_file) if session.current_file else None,
            'files': {
                file_id: asdict(file_progress)
                for file_id, file_progress in self.get_all_files_progress(session_id).items()
            }
        }

    def to_sse_message(self, session_id: str) -> str:
        """Format progress as SSE message"""
        data = self.to_dict(session_id)
        return f"data: {json.dumps(data)}\n\n"


# Global progress tracker instance
progress_tracker = ProgressTracker()

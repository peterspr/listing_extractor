"""
PDF Extractor Service - Refactored from original extractor.py
"""
import sys
import os
from pathlib import Path

# Add src directory to path for importing original modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.extractor import PDFExtractor, ExtractionResult
import logging

logger = logging.getLogger(__name__)


class PDFExtractorService:
    """
    Service wrapper for PDF extraction functionality
    Maintains compatibility with original PDFExtractor
    """

    def __init__(self, config: dict):
        """
        Initialize the extractor service

        Args:
            config: Configuration dictionary (from config.yaml)
        """
        self.config = config
        self.extractor = PDFExtractor(config)

    def extract_pdf(self, pdf_path: str) -> ExtractionResult:
        """
        Extract data from a single PDF file

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractionResult object
        """
        return self.extractor.extract_pdf(pdf_path)

    def extract_multiple(self, pdf_paths: list[str]) -> list[ExtractionResult]:
        """
        Extract data from multiple PDF files

        Args:
            pdf_paths: List of PDF file paths

        Returns:
            List of ExtractionResult objects
        """
        return self.extractor.extract_multiple_pdfs(pdf_paths)

    def get_combined_content(self, result: ExtractionResult) -> str:
        """
        Combine tabular and text data into single string

        Args:
            result: ExtractionResult object

        Returns:
            Combined content string
        """
        return self.extractor.get_combined_content(result)

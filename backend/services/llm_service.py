"""
LLM Processing Service - Refactored from original llm_processor.py
"""
import sys
import os
from pathlib import Path
from typing import Optional

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.llm_processor import LLMProcessor, LLMResult
import logging

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service wrapper for LLM processing functionality
    Maintains compatibility with original LLMProcessor
    """

    def __init__(self, config: dict):
        """
        Initialize the LLM service

        Args:
            config: Configuration dictionary (from config.yaml)
        """
        self.config = config
        self.processor = LLMProcessor(config)

    def process_extraction(
        self,
        filename: str,
        raw_content: str,
        provider: Optional[str] = None
    ) -> LLMResult:
        """
        Process extracted PDF content with LLM

        Args:
            filename: Original PDF filename
            raw_content: Raw extracted text
            provider: LLM provider to use (optional)

        Returns:
            LLMResult object
        """
        return self.processor.process_extraction(filename, raw_content, provider)

    def process_batch(
        self,
        extractions: list[tuple[str, str]],
        provider: Optional[str] = None
    ) -> list[LLMResult]:
        """
        Process multiple extractions

        Args:
            extractions: List of (filename, content) tuples
            provider: LLM provider to use

        Returns:
            List of LLMResult objects
        """
        return self.processor.process_batch(extractions, provider)

    def estimate_cost(
        self,
        extractions: list[tuple[str, str]],
        provider: Optional[str] = None
    ) -> float:
        """
        Estimate processing cost

        Args:
            extractions: List of (filename, content) tuples
            provider: LLM provider to use

        Returns:
            Estimated cost in USD
        """
        return self.processor.estimate_cost(extractions, provider)

    def validate_csv_row(self, csv_row: str) -> bool:
        """
        Validate CSV row format

        Args:
            csv_row: CSV row string

        Returns:
            True if valid
        """
        return self.processor.validate_csv_row(csv_row)

    @property
    def csv_headers(self) -> list[str]:
        """Get CSV headers"""
        return self.processor.CSV_HEADERS

"""
PDF extraction module using tabula-py and pdfplumber
"""
import logging
import os
from typing import Dict, List, Optional, Tuple
import tabula
import pdfplumber
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Container for PDF extraction results"""
    filename: str
    tabular_data: List[str]
    text_data: str
    success: bool
    error_message: Optional[str] = None


class PDFExtractor:
    """Handles PDF text and table extraction using multiple methods"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.use_tabula = config.get('extraction', {}).get('use_tabula', True)
        self.use_pdfplumber = config.get('extraction', {}).get('use_pdfplumber', True)
        self.tabula_options = config.get('extraction', {}).get('tabula_options', {})
    
    def extract_pdf(self, pdf_path: str) -> ExtractionResult:
        """
        Extract data from PDF using both tabula and pdfplumber
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult with extracted data
        """
        filename = os.path.basename(pdf_path)
        logger.info(f"Extracting data from {filename}")
        
        try:
            # Verify file exists
            if not os.path.exists(pdf_path):
                return ExtractionResult(
                    filename=filename,
                    tabular_data=[],
                    text_data="",
                    success=False,
                    error_message=f"File not found: {pdf_path}"
                )
            
            tabular_data = []
            text_data = ""
            
            # Extract tabular data with tabula-py
            if self.use_tabula:
                try:
                    tabular_data = self._extract_tables(pdf_path)
                    logger.debug(f"Extracted {len(tabular_data)} tables from {filename}")
                except Exception as e:
                    logger.warning(f"Tabula extraction failed for {filename}: {str(e)}")
            
            # Extract text with pdfplumber
            if self.use_pdfplumber:
                try:
                    text_data = self._extract_text(pdf_path)
                    logger.debug(f"Extracted {len(text_data)} characters of text from {filename}")
                except Exception as e:
                    logger.warning(f"PDFplumber extraction failed for {filename}: {str(e)}")
            
            # Check if we got any data
            if not tabular_data and not text_data:
                return ExtractionResult(
                    filename=filename,
                    tabular_data=[],
                    text_data="",
                    success=False,
                    error_message="No data extracted from PDF"
                )
            
            return ExtractionResult(
                filename=filename,
                tabular_data=tabular_data,
                text_data=text_data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Unexpected error extracting {filename}: {str(e)}")
            return ExtractionResult(
                filename=filename,
                tabular_data=[],
                text_data="",
                success=False,
                error_message=str(e)
            )
    
    def _extract_tables(self, pdf_path: str) -> List[str]:
        """Extract tables using tabula-py"""
        try:
            # Set default options
            options = {
                'pages': 'all',
                'multiple_tables': True,
                'lattice': True,
                'pandas_options': {'header': None}
            }
            # Override with config options
            options.update(self.tabula_options)
            
            # Extract tables
            tables = tabula.read_pdf(pdf_path, **options)
            
            table_strings = []
            for i, table in enumerate(tables):
                if not table.empty:
                    # Convert table to string representation
                    table_str = f"TABLE {i+1}:\n{table.to_string(index=False, header=False)}"
                    table_strings.append(table_str)
            
            return table_strings
            
        except Exception as e:
            logger.warning(f"Tabula extraction error: {str(e)}")
            return []
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extract text using pdfplumber"""
        try:
            text_parts = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"PAGE {page_num}:\n{page_text}")
                    
                    # Try to extract tables if text extraction didn't work well
                    tables = page.extract_tables()
                    for table_num, table in enumerate(tables, 1):
                        if table:
                            table_str = self._format_table(table, page_num, table_num)
                            text_parts.append(table_str)
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.warning(f"PDFplumber extraction error: {str(e)}")
            return ""
    
    def _format_table(self, table: List[List[str]], page_num: int, table_num: int) -> str:
        """Format extracted table data"""
        try:
            formatted_rows = []
            for row in table:
                # Clean and join non-empty cells
                clean_row = [str(cell).strip() if cell else "" for cell in row]
                if any(clean_row):  # Only add rows with some content
                    formatted_rows.append(" | ".join(clean_row))
            
            if formatted_rows:
                return f"PAGE {page_num} TABLE {table_num}:\n" + "\n".join(formatted_rows)
            return ""
            
        except Exception as e:
            logger.warning(f"Table formatting error: {str(e)}")
            return ""
    
    def extract_multiple_pdfs(self, pdf_paths: List[str]) -> List[ExtractionResult]:
        """Extract data from multiple PDFs"""
        results = []
        
        for pdf_path in pdf_paths:
            result = self.extract_pdf(pdf_path)
            results.append(result)
        
        return results
    
    def get_combined_content(self, result: ExtractionResult) -> str:
        """Combine tabular and text data into single string for LLM processing"""
        combined_parts = []
        
        if result.tabular_data:
            combined_parts.extend(result.tabular_data)
        
        if result.text_data:
            combined_parts.append(result.text_data)
        
        return "\n\n".join(combined_parts)
"""
Utility functions for file handling, logging, and configuration
"""
import logging
import os
import csv
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv


def setup_logging(config: Dict) -> None:
    """
    Setup logging configuration
    
    Args:
        config: Configuration dictionary with logging settings
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_file = log_config.get('file', 'extractor.log')
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Suppress overly verbose third-party loggers
    logging.getLogger('tabula').setLevel(logging.WARNING)
    logging.getLogger('pdfplumber').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)


def load_config(config_path: str = "config.yaml") -> Dict:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {str(e)}")


def load_environment_variables() -> None:
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try to load from .env.example if .env doesn't exist
        example_env = Path('.env.example')
        if example_env.exists():
            logging.warning("No .env file found. Copy .env.example to .env and add your API keys.")


def find_pdf_files(input_path: Union[str, Path]) -> List[Path]:
    """
    Find PDF files in given path
    
    Args:
        input_path: File or directory path
        
    Returns:
        List of PDF file paths
    """
    input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Path does not exist: {input_path}")
    
    if input_path.is_file():
        if input_path.suffix.lower() == '.pdf':
            return [input_path]
        else:
            raise ValueError(f"File is not a PDF: {input_path}")
    
    elif input_path.is_dir():
        pdf_files = list(input_path.glob('*.pdf'))
        pdf_files.extend(input_path.glob('*.PDF'))  # Case-insensitive
        
        if not pdf_files:
            raise ValueError(f"No PDF files found in directory: {input_path}")
        
        return sorted(pdf_files)
    
    else:
        raise ValueError(f"Invalid path: {input_path}")


def create_output_directories() -> None:
    """Create necessary output directories"""
    directories = ['output', 'raw_extractions']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def save_raw_extraction(filename: str, content: str, output_dir: str = "raw_extractions") -> str:
    """
    Save raw extracted content to file for debugging
    
    Args:
        filename: Original PDF filename
        content: Raw extracted content
        output_dir: Output directory for raw extractions
        
    Returns:
        Path to saved file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create output filename
    base_name = Path(filename).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{base_name}_{timestamp}.txt"
    
    # Save content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Raw extraction from: {filename}\n")
        f.write(f"Extracted at: {datetime.now().isoformat()}\n")
        f.write("=" * 80 + "\n\n")
        f.write(content)
    
    return str(output_file)


def save_csv_results(results: List[Dict], output_file: str, append: bool = True) -> None:
    """
    Save results to CSV file
    
    Args:
        results: List of result dictionaries
        output_file: Output CSV file path
        append: Whether to append to existing file or overwrite
    """
    if not results:
        logging.warning("No results to save")
        return
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # CSV headers
    headers = [
        "File Name", "Address", "Shell SF", "Office SF", "Shell Rate", 
        "Office Rate", "OpEx", "Monthly Base Rent", "Monthly Blended Rate", 
        "Annual Blended Rate", "Gross Monthly Rent", "Gross Blended Rate", 
        "Dock/Grade", "Clear Height", "Notes"
    ]
    
    # Check if file exists and has content
    file_exists = output_path.exists() and output_path.stat().st_size > 0
    write_header = not (file_exists and append)
    
    mode = 'a' if append and file_exists else 'w'
    
    with open(output_path, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        
        if write_header:
            writer.writeheader()
        
        for result in results:
            writer.writerow(result)
    
    logging.info(f"Results saved to {output_path}")


def parse_csv_row(csv_row: str) -> Dict[str, str]:
    """
    Parse CSV row string into dictionary
    
    Args:
        csv_row: CSV row as string
        
    Returns:
        Dictionary with column headers as keys
    """
    headers = [
        "File Name", "Address", "Shell SF", "Office SF", "Shell Rate", 
        "Office Rate", "OpEx", "Monthly Base Rent", "Monthly Blended Rate", 
        "Annual Blended Rate", "Gross Monthly Rent", "Gross Blended Rate", 
        "Dock/Grade", "Clear Height", "Notes"
    ]
    
    try:
        # Simple CSV parsing - split on comma
        values = [v.strip() for v in csv_row.split(',')]
        
        # Ensure we have the right number of values
        while len(values) < len(headers):
            values.append("N/A")
        
        # Truncate if too many values
        values = values[:len(headers)]
        
        return dict(zip(headers, values))
        
    except Exception as e:
        logging.error(f"Error parsing CSV row: {str(e)}")
        # Return empty dictionary with all N/A values
        return dict(zip(headers, ["N/A"] * len(headers)))


def format_summary_stats(stats: Dict) -> str:
    """
    Format summary statistics for display
    
    Args:
        stats: Dictionary with statistics
        
    Returns:
        Formatted string
    """
    lines = [
        "EXTRACTION SUMMARY",
        "=" * 50,
        f"Total files processed: {stats.get('total_files', 0)}",
        f"Successful extractions: {stats.get('successful', 0)}",
        f"Failed extractions: {stats.get('failed', 0)}",
        f"Total cost estimate: ${stats.get('total_cost', 0.0):.4f}",
        f"Average cost per file: ${stats.get('avg_cost', 0.0):.4f}",
    ]
    
    if stats.get('warnings'):
        lines.extend([
            "",
            "WARNINGS:",
            "-" * 20
        ])
        lines.extend(stats['warnings'])
    
    if stats.get('errors'):
        lines.extend([
            "",
            "ERRORS:",
            "-" * 20
        ])
        lines.extend(stats['errors'])
    
    return "\n".join(lines)


def validate_api_keys() -> Dict[str, bool]:
    """
    Validate that required API keys are present
    
    Returns:
        Dictionary with provider names and key availability
    """
    keys = {
        'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'google': bool(os.getenv('GOOGLE_API_KEY'))
    }
    
    return keys


def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    Generate hash for file content (for caching)
    
    Args:
        file_path: Path to file
        
    Returns:
        File content hash
    """
    import hashlib
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()
    except Exception as e:
        logging.warning(f"Could not generate hash for {file_path}: {str(e)}")
        return ""


def ensure_output_directory(output_file: str) -> None:
    """Ensure output directory exists for given file path"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)


def clean_filename_for_output(filename: str) -> str:
    """
    Clean filename for use in output files
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename safe for filesystem
    """
    # Remove or replace problematic characters
    cleaned = filename.replace(' ', '_')
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c in '._-')
    return cleaned


def load_existing_csv(csv_path: str) -> List[str]:
    """
    Load existing CSV and return list of processed filenames
    
    Args:
        csv_path: Path to existing CSV file
        
    Returns:
        List of filenames already processed
    """
    processed_files = []
    
    try:
        if Path(csv_path).exists():
            df = pd.read_csv(csv_path)
            if 'File Name' in df.columns:
                processed_files = df['File Name'].tolist()
    except Exception as e:
        logging.warning(f"Could not load existing CSV {csv_path}: {str(e)}")
    
    return processed_files


def create_progress_callback(total_files: int):
    """
    Create a progress callback function for use with tqdm or similar
    
    Args:
        total_files: Total number of files to process
        
    Returns:
        Callback function
    """
    from tqdm import tqdm
    
    pbar = tqdm(total=total_files, desc="Processing PDFs")
    
    def callback(current: int, filename: str = "", status: str = ""):
        pbar.set_description(f"Processing {filename}")
        pbar.update(1)
        if current >= total_files:
            pbar.close()
    
    return callback
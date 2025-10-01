#!/usr/bin/env python3
"""
Commercial Real Estate PDF Data Extractor
CLI tool for extracting structured data from CRE listing PDFs
"""
import sys
import os
import logging
from pathlib import Path
from typing import List, Optional

import click
from tqdm import tqdm

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import (
    load_config, load_environment_variables, setup_logging,
    find_pdf_files, create_output_directories, save_csv_results,
    save_raw_extraction, parse_csv_row, format_summary_stats,
    validate_api_keys, load_existing_csv
)
from src.extractor import PDFExtractor
from src.llm_processor import LLMProcessor
from src.calculator import validate_extraction_data

logger = logging.getLogger(__name__)


@click.command()
@click.option('--input', '-i', 'input_path', type=click.Path(),
              help='Input PDF file or directory containing PDFs')
@click.option('--input-dir', type=click.Path(file_okay=False),
              help='Directory containing PDF files to process')
@click.option('--output', '-o', 'output_file', type=click.Path(),
              default='output/results.csv', help='Output CSV file path')
@click.option('--llm', type=click.Choice(['anthropic', 'openai', 'google', 'haiku', 'gpt4o-mini', 'gemini-flash']),
              help='LLM provider to use (overrides config default)')
@click.option('--dry-run', is_flag=True, help='Extract text only, skip LLM processing')
@click.option('--estimate-cost', is_flag=True, help='Estimate processing costs without running')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--save-raw', is_flag=True, help='Save raw extracted text for debugging')
@click.option('--config', type=click.Path(), default='config.yaml',
              help='Configuration file path')
@click.option('--skip-existing', is_flag=True, help='Skip files already processed in output CSV')
def main(input_path: Optional[str], input_dir: Optional[str], output_file: str, 
         llm: Optional[str], dry_run: bool, estimate_cost: bool, verbose: bool,
         save_raw: bool, config: str, skip_existing: bool):
    """
    Extract structured data from commercial real estate PDF listings.
    
    Examples:
        python main.py --input listing.pdf --output results.csv
        python main.py --input-dir ./pdfs --output batch_results.csv
        python main.py --input listing.pdf --dry-run --save-raw
        python main.py --input-dir ./pdfs --estimate-cost --llm gpt4o-mini
    """
    try:
        # Load configuration and environment
        app_config = load_config(config)
        load_environment_variables()
        
        # Override logging level if verbose
        if verbose:
            app_config['logging']['level'] = 'DEBUG'
        
        # Setup logging
        setup_logging(app_config)
        logger.info("Starting CRE PDF Extractor")
        
        # Create output directories
        create_output_directories()
        
        # Determine input files
        if input_dir:
            input_path = input_dir
        elif not input_path:
            click.echo("Error: Must specify either --input or --input-dir")
            sys.exit(1)
        
        # Find PDF files
        try:
            pdf_files = find_pdf_files(input_path)
            logger.info(f"Found {len(pdf_files)} PDF files to process")
        except (FileNotFoundError, ValueError) as e:
            click.echo(f"Error: {str(e)}")
            sys.exit(1)
        
        # Skip existing files if requested
        if skip_existing and Path(output_file).exists():
            processed_files = load_existing_csv(output_file)
            original_count = len(pdf_files)
            pdf_files = [f for f in pdf_files if f.name not in processed_files]
            skipped = original_count - len(pdf_files)
            if skipped > 0:
                logger.info(f"Skipping {skipped} already processed files")
        
        if not pdf_files:
            click.echo("No new files to process")
            sys.exit(0)
        
        # Map LLM shortcuts to providers
        llm_provider_map = {
            'haiku': 'anthropic',
            'gpt4o-mini': 'openai',
            'gemini-flash': 'google'
        }
        provider = llm_provider_map.get(llm, llm)
        
        # Initialize components
        extractor = PDFExtractor(app_config)
        
        if not dry_run:
            # Validate API keys
            api_keys = validate_api_keys()
            if provider and not api_keys.get(provider):
                click.echo(f"Error: {provider.upper()}_API_KEY not found in environment")
                click.echo("Copy .env.example to .env and add your API keys")
                sys.exit(1)
            
            processor = LLMProcessor(app_config)
        
        # Cost estimation mode
        if estimate_cost and not dry_run:
            click.echo("Estimating processing costs...")
            
            # Extract a sample to estimate content size
            sample_extractions = []
            for pdf_file in pdf_files[:3]:  # Sample first 3 files
                result = extractor.extract_pdf(str(pdf_file))
                if result.success:
                    content = extractor.get_combined_content(result)
                    sample_extractions.append((result.filename, content))
            
            if sample_extractions:
                total_cost = processor.estimate_cost(
                    [(f, c) for f, c in sample_extractions] * (len(pdf_files) // len(sample_extractions) + 1),
                    provider
                )
                # Scale to actual number of files
                estimated_cost = total_cost * len(pdf_files) / len(sample_extractions)
                
                click.echo(f"Estimated cost: ${estimated_cost:.4f}")
                click.echo(f"Average cost per file: ${estimated_cost/len(pdf_files):.4f}")
                
                if not click.confirm("Continue with processing?"):
                    sys.exit(0)
        
        # Process files
        results = []
        stats = {
            'total_files': len(pdf_files),
            'successful': 0,
            'failed': 0,
            'total_cost': 0.0,
            'warnings': [],
            'errors': []
        }
        
        with tqdm(total=len(pdf_files), desc="Processing PDFs") as pbar:
            for pdf_file in pdf_files:
                pbar.set_description(f"Processing {pdf_file.name}")
                
                try:
                    # Extract PDF content
                    extraction_result = extractor.extract_pdf(str(pdf_file))
                    
                    if not extraction_result.success:
                        stats['failed'] += 1
                        stats['errors'].append(f"{pdf_file.name}: {extraction_result.error_message}")
                        pbar.update(1)
                        continue
                    
                    # Get combined content
                    combined_content = extractor.get_combined_content(extraction_result)
                    
                    # Save raw extraction if requested
                    if save_raw:
                        save_raw_extraction(extraction_result.filename, combined_content)
                    
                    if dry_run:
                        # Dry run mode - just show extraction was successful
                        click.echo(f"✓ Extracted content from {pdf_file.name}")
                        stats['successful'] += 1
                    else:
                        # Process with LLM
                        llm_result = processor.process_extraction(
                            extraction_result.filename, combined_content, provider
                        )
                        
                        if llm_result.success:
                            # Parse CSV row
                            row_data = parse_csv_row(llm_result.csv_row)
                            
                            # Validate data
                            validation = validate_extraction_data(row_data)
                            if validation['warnings']:
                                stats['warnings'].extend([
                                    f"{pdf_file.name}: {w}" for w in validation['warnings']
                                ])
                            
                            results.append(row_data)
                            stats['successful'] += 1
                            stats['total_cost'] += llm_result.cost_estimate
                            
                        else:
                            stats['failed'] += 1
                            stats['errors'].append(f"{pdf_file.name}: {llm_result.error_message}")
                
                except Exception as e:
                    logger.error(f"Unexpected error processing {pdf_file.name}: {str(e)}")
                    stats['failed'] += 1
                    stats['errors'].append(f"{pdf_file.name}: {str(e)}")
                
                pbar.update(1)
        
        # Save results
        if results and not dry_run:
            save_csv_results(results, output_file, append=skip_existing)
            click.echo(f"\nResults saved to {output_file}")
        
        # Calculate average cost
        if stats['successful'] > 0:
            stats['avg_cost'] = stats['total_cost'] / stats['successful']
        else:
            stats['avg_cost'] = 0.0
        
        # Display summary
        click.echo("\n" + format_summary_stats(stats))
        
        # Exit with error code if any files failed
        if stats['failed'] > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo("\nProcessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
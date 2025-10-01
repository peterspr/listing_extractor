# Claude Code Configuration

This file contains configuration and context for Claude Code to better understand and work with this project.

## Project Overview
Commercial Real Estate PDF Data Extractor - A Python CLI tool that extracts structured data from commercial/industrial real estate listing PDFs and outputs clean CSV data using LLM-powered processing.

## Development Commands
- `python main.py --help` - Show CLI help
- `python main.py --input listing.pdf --output results.csv` - Basic usage
- `python main.py validate-config` - Validate configuration
- `python main.py extract-only listing.pdf` - Extract raw content only
- `pip install -r requirements.txt` - Install dependencies

## Testing Commands
- `python main.py --input examples/sample.pdf --dry-run --verbose` - Test extraction
- `python main.py --estimate-cost --input-dir examples/` - Estimate costs

## Project Structure
```
.
├── main.py                 # CLI entry point
├── config.yaml             # Configuration settings
├── requirements.txt        # Python dependencies
├── .env.example           # API key template
├── src/
│   ├── extractor.py       # PDF extraction logic
│   ├── llm_processor.py   # LLM API integration
│   ├── calculator.py      # Rent calculation helpers
│   └── utils.py           # Utilities and helpers
├── output/                # Generated CSV files
├── raw_extractions/       # Debug: raw extracted text
└── examples/              # Example PDF files
```

## Key Technologies
- **PDF Extraction**: tabula-py (tables) + pdfplumber (text)
- **LLM Processing**: Anthropic Claude, OpenAI GPT, Google Gemini
- **CLI Framework**: Click
- **Data Processing**: Pandas, PyYAML

## Notes
- Requires API keys for LLM providers (set in .env file)
- Hybrid extraction approach handles both tabular and text-based PDFs
- Built-in cost estimation and validation
- Supports batch processing with error recovery
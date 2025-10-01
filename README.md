# Commercial Real Estate PDF Data Extractor

A Python CLI tool that extracts structured data from commercial/industrial real estate listing PDFs and outputs clean CSV data using LLM-powered processing.

## Features

- **Hybrid PDF Extraction**: Uses both tabula-py and pdfplumber for comprehensive data extraction
- **LLM-Powered Cleaning**: Supports Anthropic Claude, OpenAI GPT, and Google Gemini for intelligent data structuring
- **Batch Processing**: Process multiple PDFs with cost optimization
- **Validation & Quality Assurance**: Built-in validation for suspicious data values
- **Cost Estimation**: Preview processing costs before running
- **Flexible Output**: Structured CSV with standardized commercial real estate fields

## Installation

1. Clone the repository:
```bash
git clone https://github.com/peterspr/listing_extractor.git
cd listing_extractor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up API keys:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

### API Keys Required

Add your API keys to `.env`:

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

You only need the API key for the LLM provider you plan to use.

### Configuration File

The `config.yaml` file contains settings for:
- LLM providers and models
- PDF extraction options
- Output preferences
- Cost estimates

## Usage

### Basic Usage

Extract data from a single PDF:
```bash
python main.py --input listing.pdf --output results.csv
```

Process multiple PDFs from a directory:
```bash
python main.py --input-dir ./pdfs --output batch_results.csv
```

### Advanced Options

Use a specific LLM provider:
```bash
python main.py --input listing.pdf --llm anthropic
python main.py --input listing.pdf --llm gpt4o-mini
python main.py --input listing.pdf --llm gemini-flash
```

Dry run (extraction only, no LLM processing):
```bash
python main.py --input listing.pdf --dry-run --save-raw
```

Estimate costs before processing:
```bash
python main.py --input-dir ./pdfs --estimate-cost --llm anthropic
```

Skip already processed files:
```bash
python main.py --input-dir ./pdfs --output results.csv --skip-existing
```

Verbose logging with raw text saving:
```bash
python main.py --input listing.pdf --verbose --save-raw
```

### Utility Commands

Validate configuration:
```bash
python main.py validate-config
```

Extract raw content without LLM processing:
```bash
python main.py extract-only listing.pdf
```

## Output Format

The tool outputs CSV files with these columns:

| Column | Description | Example |
|--------|-------------|---------|
| File Name | Original PDF filename | `listing.pdf` |
| Address | Full property address | `11755 SE Capps Rd, Clackamas, OR 97015` |
| Shell SF | Warehouse/shell square footage | `11500` |
| Office SF | Office square footage | `0` or `N/A` |
| Shell Rate | Lease rate for warehouse ($/SF/month) | `0.80` |
| Office Rate | Lease rate for office ($/SF/month) | `N/A` |
| OpEx | Operating expenses/NNN | `NNN` |
| Monthly Base Rent | Calculated base rent | `9200` |
| Monthly Blended Rate | Blended rate per SF per month | `0.80` |
| Annual Blended Rate | Blended rate per SF per year | `9.60` |
| Gross Monthly Rent | Total monthly rent including OpEx | `N/A` |
| Gross Blended Rate | Gross rate per SF per month | `N/A` |
| Dock/Grade | Loading door information | `8 dock, 1 grade` |
| Clear Height | Ceiling height | `28'` |
| Notes | Additional relevant information | `GI zoning; Available immediately` |

## LLM Providers

### Anthropic Claude (Default)
- **Model**: `claude-3-5-haiku-20241022`
- **Cost**: ~$0.25 per million tokens
- **Best for**: Balanced cost, speed, and accuracy

### OpenAI GPT
- **Model**: `gpt-4o-mini`
- **Cost**: ~$0.15 per million tokens  
- **Best for**: Lowest cost option

### Google Gemini
- **Model**: `gemini-1.5-flash`
- **Cost**: ~$0.075 per million tokens
- **Best for**: Highest cost efficiency

## Project Structure

```
listing_extractor/
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
├── examples/              # Example PDF files
└── README.md
```

## Error Handling & Quality Assurance

### Data Validation
- Validates square footage ranges (100 - 10M SF)
- Checks lease rates for reasonableness ($0.01 - $20/SF/month)
- Flags suspicious monthly rent values
- Warns about unusual operating expense rates

### Failure Recovery
- Retries LLM API calls with exponential backoff
- Continues batch processing even if individual files fail
- Detailed error logging and reporting
- Graceful handling of malformed PDFs

### Cost Protection
- Cost estimation before processing
- Confirmation prompts for large batches
- Rate limiting between API calls
- Caching to avoid re-processing

## Troubleshooting

### Common Issues

**"API key not found"**
- Ensure your `.env` file exists and contains the correct API key
- Check that the API key variable name matches the provider

**"No data extracted from PDF"**
- PDF may be image-based (scanned) - extraction tools work best with text-based PDFs
- Try the `--save-raw` option to see what content was extracted

**"Suspicious data values"**
- The tool flags unusual values for manual review
- Check the original PDF to verify if the extracted data is correct

**High processing costs**
- Use `--estimate-cost` to preview costs before processing
- Consider using a cheaper provider like Google Gemini for large batches

### Debug Mode

Enable verbose logging and save raw extractions:
```bash
python main.py --input problem.pdf --verbose --save-raw --dry-run
```

This will show detailed extraction logs and save the raw extracted text to `raw_extractions/` for review.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the logs in `extractor.log` for detailed error information
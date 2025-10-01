"""
LLM processor module for cleaning and structuring extracted data
"""
import logging
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json

# LLM client imports
import anthropic
import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    """Container for LLM processing results"""
    csv_row: str
    success: bool
    cost_estimate: float
    error_message: Optional[str] = None
    raw_response: Optional[str] = None


class LLMProcessor:
    """Handles LLM API calls for data cleaning and structuring"""
    
    CSV_HEADERS = [
        "File Name", "Address", "Shell SF", "Office SF", "Shell Rate", 
        "Office Rate", "OpEx", "Monthly Base Rent", "Monthly Blended Rate", 
        "Annual Blended Rate", "Gross Monthly Rent", "Gross Blended Rate", 
        "Dock/Grade", "Clear Height", "Notes"
    ]
    
    def __init__(self, config: Dict):
        self.config = config
        self.provider = config['llm']['default_provider']
        self.cache = {}  # Simple in-memory cache
        
        # Initialize clients
        self.anthropic_client = None
        self.openai_client = None
        self.google_client = None
        
        self._init_clients()
    
    def _init_clients(self):
        """Initialize LLM clients with API keys"""
        try:
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                logger.debug("Anthropic client initialized")
            
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                logger.debug("OpenAI client initialized")
            
            google_key = os.getenv('GOOGLE_API_KEY')
            if google_key:
                genai.configure(api_key=google_key)
                self.google_client = genai.GenerativeModel('gemini-1.5-flash')
                logger.debug("Google client initialized")
                
        except Exception as e:
            logger.warning(f"Error initializing LLM clients: {str(e)}")
    
    def process_extraction(self, filename: str, raw_content: str, provider: Optional[str] = None) -> LLMResult:
        """
        Process extracted content with LLM to create structured CSV row
        
        Args:
            filename: Original PDF filename
            raw_content: Raw extracted text from PDF
            provider: LLM provider to use (overrides default)
            
        Returns:
            LLMResult with structured data
        """
        provider = provider or self.provider
        
        # Check cache first
        cache_key = self._get_cache_key(filename, raw_content, provider)
        if cache_key in self.cache:
            logger.debug(f"Using cached result for {filename}")
            return self.cache[cache_key]
        
        # Create prompt
        prompt = self._create_prompt(filename, raw_content)
        
        # Process with appropriate provider
        try:
            if provider == "anthropic":
                result = self._process_anthropic(prompt)
            elif provider == "openai":
                result = self._process_openai(prompt)
            elif provider == "google":
                result = self._process_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Cache successful results
            if result.success:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"LLM processing error for {filename}: {str(e)}")
            return LLMResult(
                csv_row="",
                success=False,
                cost_estimate=0.0,
                error_message=str(e)
            )
    
    def _create_prompt(self, filename: str, raw_content: str) -> str:
        """Create prompt for LLM processing"""
        prompt = f"""You are a commercial real estate data extraction assistant. Extract and structure the following information from this property listing.

RAW EXTRACTED TEXT:
{raw_content}

OUTPUT REQUIREMENTS:
- Extract data into this exact CSV format with these column headers:
  {', '.join(self.CSV_HEADERS)}

EXTRACTION RULES:
- File Name: Use "{filename}"
- Normalize rates to $/SF format (remove "$" and "SF", keep numeric)
- Use "N/A" for missing values
- For Dock/Grade: combine all loading door info (e.g., "8 dock, 1 grade")
- For Notes: include zoning, ideal uses, availability status, buildout details
- Calculate Monthly Base Rent if Shell Rate and Shell SF are available
- If NNN/OpEx mentioned, note in OpEx field
- Return ONLY the CSV row, no explanations

EXAMPLE OUTPUT:
listing.pdf,11755 SE Capps Rd Clackamas OR 97015,11500,0,0.80,N/A,NNN,9200,0.80,9.60,N/A,N/A,8 dock 1 grade,28',GI zoning; Available immediately; Warehouse only"""
        
        return prompt
    
    def _process_anthropic(self, prompt: str) -> LLMResult:
        """Process with Anthropic Claude"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized - check API key")
        
        try:
            config = self.config['llm']['anthropic']
            
            response = self.anthropic_client.messages.create(
                model=config['model'],
                max_tokens=config['max_tokens'],
                messages=[{"role": "user", "content": prompt}]
            )
            
            csv_row = response.content[0].text.strip()
            
            # Estimate cost
            input_tokens = len(prompt.split()) * 1.3  # Rough estimate
            output_tokens = len(csv_row.split()) * 1.3
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost("anthropic", config['model'], total_tokens)
            
            return LLMResult(
                csv_row=csv_row,
                success=True,
                cost_estimate=cost,
                raw_response=csv_row
            )
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _process_openai(self, prompt: str) -> LLMResult:
        """Process with OpenAI GPT"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized - check API key")
        
        try:
            config = self.config['llm']['openai']
            
            response = self.openai_client.chat.completions.create(
                model=config['model'],
                max_tokens=config['max_tokens'],
                messages=[{"role": "user", "content": prompt}]
            )
            
            csv_row = response.choices[0].message.content.strip()
            
            # Calculate actual cost from response
            usage = response.usage
            total_tokens = usage.total_tokens if usage else len(prompt.split()) * 2
            cost = self._calculate_cost("openai", config['model'], total_tokens)
            
            return LLMResult(
                csv_row=csv_row,
                success=True,
                cost_estimate=cost,
                raw_response=csv_row
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _process_google(self, prompt: str) -> LLMResult:
        """Process with Google Gemini"""
        if not self.google_client:
            raise ValueError("Google client not initialized - check API key")
        
        try:
            config = self.config['llm']['google']
            
            response = self.google_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=config['max_tokens']
                )
            )
            
            csv_row = response.text.strip()
            
            # Estimate cost
            total_tokens = len(prompt.split()) * 2  # Rough estimate
            cost = self._calculate_cost("google", config['model'], total_tokens)
            
            return LLMResult(
                csv_row=csv_row,
                success=True,
                cost_estimate=cost,
                raw_response=csv_row
            )
            
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def _calculate_cost(self, provider: str, model: str, tokens: int) -> float:
        """Calculate estimated cost for API call"""
        try:
            costs = self.config.get('costs', {})
            provider_costs = costs.get(provider, {})
            rate_per_million = provider_costs.get(model, 0.0)
            return (tokens / 1_000_000) * rate_per_million
        except Exception:
            return 0.0
    
    def _get_cache_key(self, filename: str, content: str, provider: str) -> str:
        """Generate cache key for content"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        return f"{filename}_{provider}_{content_hash}"
    
    def process_batch(self, extractions: List[Tuple[str, str]], provider: Optional[str] = None, max_batch_size: int = 5) -> List[LLMResult]:
        """
        Process multiple extractions in batches
        
        Args:
            extractions: List of (filename, raw_content) tuples
            provider: LLM provider to use
            max_batch_size: Maximum files per batch
            
        Returns:
            List of LLMResult objects
        """
        results = []
        
        # For now, process individually with retry logic
        # Future enhancement: batch multiple PDFs into single prompt
        for filename, content in extractions:
            result = self._process_with_retry(filename, content, provider)
            results.append(result)
            
            # Small delay between requests to avoid rate limits
            time.sleep(0.1)
        
        return results
    
    def _process_with_retry(self, filename: str, content: str, provider: Optional[str] = None, max_retries: int = 3) -> LLMResult:
        """Process with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return self.process_extraction(filename, content, provider)
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt failed
                    return LLMResult(
                        csv_row="",
                        success=False,
                        cost_estimate=0.0,
                        error_message=f"Failed after {max_retries} attempts: {str(e)}"
                    )
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                logger.warning(f"Attempt {attempt + 1} failed for {filename}, retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
        
        # Should never reach here
        return LLMResult(csv_row="", success=False, cost_estimate=0.0, error_message="Unexpected error")
    
    def estimate_cost(self, extractions: List[Tuple[str, str]], provider: Optional[str] = None) -> float:
        """Estimate total cost for processing extractions"""
        provider = provider or self.provider
        total_cost = 0.0
        
        try:
            config = self.config['llm'][provider]
            model = config['model']
            
            for filename, content in extractions:
                prompt = self._create_prompt(filename, content)
                estimated_tokens = len(prompt.split()) * 2  # Rough estimate for input + output
                cost = self._calculate_cost(provider, model, estimated_tokens)
                total_cost += cost
            
            return total_cost
            
        except Exception as e:
            logger.warning(f"Cost estimation error: {str(e)}")
            return 0.0
    
    def validate_csv_row(self, csv_row: str) -> bool:
        """Validate that CSV row has correct number of columns"""
        try:
            parts = csv_row.split(',')
            return len(parts) == len(self.CSV_HEADERS)
        except Exception:
            return False
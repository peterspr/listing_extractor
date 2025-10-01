"""
Configuration settings for the backend application
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings"""

    # Server settings
    HOST = os.getenv('BACKEND_HOST', '0.0.0.0')
    PORT = int(os.getenv('BACKEND_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # File upload settings
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS = {'pdf'}
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    RESULTS_FOLDER = os.getenv('RESULTS_FOLDER', '/tmp/results')

    # Session settings
    SESSION_TIMEOUT = 24 * 60 * 60  # 24 hours in seconds

    # LLM settings
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    # Extraction timeout
    EXTRACTION_TIMEOUT = 300  # 5 minutes

    @classmethod
    def load_llm_config(cls, config_path: str = 'config.yaml'):
        """Load LLM configuration from YAML file"""
        try:
            yaml_path = Path(__file__).parent.parent.parent / config_path
            with open(yaml_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            return cls.get_default_llm_config()

    @staticmethod
    def get_default_llm_config():
        """Default LLM configuration"""
        return {
            'llm': {
                'default_provider': 'anthropic',
                'anthropic': {
                    'model': 'claude-3-5-haiku-20241022',
                    'max_tokens': 1000
                },
                'openai': {
                    'model': 'gpt-4o-mini',
                    'max_tokens': 1000
                },
                'google': {
                    'model': 'gemini-1.5-flash',
                    'max_tokens': 1000
                }
            },
            'extraction': {
                'use_tabula': True,
                'use_pdfplumber': True,
                'tabula_options': {
                    'pages': 'all',
                    'multiple_tables': True,
                    'lattice': True
                }
            },
            'costs': {
                'anthropic': {'claude-3-5-haiku-20241022': 0.25},
                'openai': {'gpt-4o-mini': 0.15},
                'google': {'gemini-1.5-flash': 0.075}
            }
        }


settings = Settings()

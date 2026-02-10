"""
Configuration management for the book generation system.
Loads environment variables and provides centralized configuration access.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """Central configuration class"""
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-flash-latest')
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    
    # Email Configuration
    SMTP_HOST: str = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME: str = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')
    NOTIFICATION_EMAIL: str = os.getenv('NOTIFICATION_EMAIL', '')
    
    # MS Teams Configuration
    TEAMS_WEBHOOK_URL: str = os.getenv('TEAMS_WEBHOOK_URL', '')
    
    # Application Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    
    # Output Settings
    OUTPUT_DIR: Path = Path(__file__).parent.parent.parent / 'output'
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required = [
            ('GEMINI_API_KEY', cls.GEMINI_API_KEY),
            ('SUPABASE_URL', cls.SUPABASE_URL),
            ('SUPABASE_KEY', cls.SUPABASE_KEY),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
    
    @classmethod
    def setup_output_dir(cls):
        """Create output directory if it doesn't exist"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


# Create singleton instance
config = Config()

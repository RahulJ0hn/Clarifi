from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os

class Settings(BaseSettings):
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "case_sensitive": True
    }
    
    # API Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./ai_browser.db"
    
    # AI Service Configuration
    AI_PROVIDER: str = "aws_bedrock"
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_MODEL_ID: str = "arn:aws:bedrock:us-east-1:215010039491:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001,https://clarifi-production-535f.up.railway.app"
    
    # Monitoring Configuration
    MONITOR_CHECK_INTERVAL: int = 60  # 1 minute in seconds for testing
    MAX_MONITORS_PER_USER: int = 50
    
    # Scraping Configuration
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    REQUEST_TIMEOUT: int = 30
    MAX_CONTENT_LENGTH: int = 1000000  # 1MB
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Clerk Configuration
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: Optional[str] = None
    CLERK_ISSUER_URL: Optional[str] = None
    CLERK_AUDIENCE: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    @property
    def get_allowed_origins(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]
    
    @property
    def get_model_id(self) -> str:
        """Get the AI model ID"""
        return self.AWS_MODEL_ID

# Create settings instance
settings = Settings()

# Validate AI credentials
if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
    print("WARNING: AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file") 
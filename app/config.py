import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Speaker Profile Automation Platform"
    API_V1_STR: str = "/api/v1"
    
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET")
    
    # Storage settings
    STORAGE_BUCKET: str = "speaker-profiles"
    
    # Authentication settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    
    # YouTube API settings
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY")
    
    # LinkedIn API settings (optional, can use Selenium instead)
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    
    # OCR settings
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")

    # Maximum token limits for OpenAI API
    MAX_TOKENS_PER_REQUEST: int = 4000  # Adjust based on the model you're using
    
    class Config:
        case_sensitive = True

# Create a settings instance
settings = Settings()
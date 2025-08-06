"""
Configuration management using Pydantic settings and python-dotenv.
Handles environment variables and application configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: Optional[str] = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "image_processor"
    db_user: str = "postgres"
    db_password: str = "password"
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_url: str = "redis://localhost:6379/0"
    
    # Application Configuration
    app_name: str = "Image Processor API"
    debug: bool = True
    log_level: str = "INFO"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    
    # File Storage
    upload_dir: str = "uploads"
    output_dir: str = "output"
    max_file_size: int = 10485760  # 10MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL from environment or construct from components."""
    # First check if DATABASE_URL is set directly in environment
    if settings.database_url:
        return settings.database_url
    
    # Construct from individual components using the loaded settings
    return f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"


def get_redis_url() -> str:
    """Get Redis URL from environment or construct from components."""
    # First check if REDIS_URL is set directly
    if settings.redis_url != "redis://localhost:6379/0":
        return settings.redis_url
    
    # Construct from individual components
    password_part = f":{settings.redis_password}@" if settings.redis_password else ""
    return f"redis://{password_part}{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def ensure_directories():
    """Ensure required directories exist."""
    directories = [settings.upload_dir, settings.output_dir]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")


def print_config():
    """Print current configuration (without sensitive data)."""
    print("🔧 Current Configuration:")
    print(f"  App Name: {settings.app_name}")
    print(f"  Debug Mode: {settings.debug}")
    print(f"  API Host: {settings.api_host}")
    print(f"  API Port: {settings.api_port}")
    print(f"  Database Host: {settings.db_host}")
    print(f"  Database Port: {settings.db_port}")
    print(f"  Database Name: {settings.db_name}")
    print(f"  Redis Host: {settings.redis_host}")
    print(f"  Redis Port: {settings.redis_port}")
    print(f"  Redis DB: {settings.redis_db}")
    print(f"  Upload Directory: {settings.upload_dir}")
    print(f"  Output Directory: {settings.output_dir}")
    print(f"  Max File Size: {settings.max_file_size} bytes") 
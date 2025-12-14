"""
Configuration Module
====================
This module manages all application configuration settings using Pydantic Settings.
It loads configuration from environment variables or uses default values.

Environment Variables:
- HOSPITAL_API_BASE_URL: Base URL of the Hospital Directory API
- DATABASE_URL: SQLite database connection string
- MAX_CSV_ROWS: Maximum number of hospitals allowed per CSV upload
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application Settings Class
    
    This class defines all configuration parameters for the application.
    Values are automatically loaded from environment variables or .env file.
    If not found, default values are used.
    """
    
    # External API Configuration
    hospital_api_base_url: str = "https://hospital-directory.onrender.com"
    """Base URL of the Hospital Directory API we integrate with"""
    
    # Database Configuration
    database_url: str = "sqlite:///./hospital_bulk.db"
    """SQLite database connection string for storing batch processing history"""
    
    # Business Rules
    max_csv_rows: int = 20
    """Maximum number of hospital records allowed in a single CSV upload"""
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"  # Load from .env file if present
        case_sensitive = False  # Environment variables are case-insensitive


@lru_cache()
def get_settings() -> Settings:
    """
    Get Cached Settings Instance
    
    This function returns a singleton instance of Settings.
    The @lru_cache decorator ensures we only create one instance,
    improving performance by avoiding repeated environment variable reads.
    
    Returns:
        Settings: Cached application settings instance
    """
    return Settings()

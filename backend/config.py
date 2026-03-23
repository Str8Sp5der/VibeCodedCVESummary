import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App
    APP_NAME: str = "CVE Database API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/cve_db"
    )
    
    # JWT & Auth
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", 
        "dev-secret-key-change-in-production"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7
    
    # CORS
    ALLOWED_ORIGINS: list = [
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:5173",  # Vite default
    ]
    
    # NVD API
    NVD_API_KEY: str = os.getenv("NVD_API_KEY", "")
    NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # Exploit-DB API
    EXPLOIT_DB_URL: str = "https://www.exploit-db.com/api"
    EXPLOIT_DB_API_KEY: str = os.getenv("EXPLOIT_DB_API_KEY", "")
    
    # Sync Schedule (in minutes)
    FULL_SYNC_INTERVAL: int = 60  # Full sync every 60 minutes
    DELTA_SYNC_INTERVAL: int = 10  # Delta sync every 10 minutes
    
    # Security
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "dev-encryption-key-change-in-prod")
    ENABLE_HTTPS_REDIRECT: bool = not DEBUG
    
    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = 100
    RATE_LIMIT_GLOBAL_PER_HOUR: int = 1000
    LOGIN_RATE_LIMIT_PER_HOUR: int = 10
    
    # Session
    SESSION_COOKIE_SECURE: bool = not DEBUG
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "strict"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env without raising errors


@lru_cache()
def get_settings() -> Settings:
    return Settings()

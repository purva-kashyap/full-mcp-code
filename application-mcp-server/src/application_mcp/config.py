"""Configuration management for production deployment"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration with validation"""
    
    # Azure/Auth Configuration
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    
    # HTTP Client Configuration
    HTTP_TIMEOUT: float = float(os.getenv("HTTP_TIMEOUT", "30.0"))
    HTTP_MAX_CONNECTIONS: int = int(os.getenv("HTTP_MAX_CONNECTIONS", "100"))
    HTTP_MAX_KEEPALIVE: int = int(os.getenv("HTTP_MAX_KEEPALIVE", "20"))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_MAX_WAIT: int = int(os.getenv("RETRY_MAX_WAIT", "60"))
    
    # Concurrency Configuration
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "50"))
    
    # Rate Limiting Configuration (requests per time_period in seconds)
    # Based on Microsoft Graph API documented limits
    # Format: "max_requests,time_period_seconds"
    
    # Global rate limit (applies to all endpoints)
    RATE_LIMIT_GLOBAL: str = os.getenv("RATE_LIMIT_GLOBAL", "2000,10")  # 2000 per 10 seconds
    
    # Mail API rate limits
    RATE_LIMIT_MAIL: str = os.getenv("RATE_LIMIT_MAIL", "10000,600")  # 10,000 per 10 minutes
    
    # Calendar API rate limits
    RATE_LIMIT_CALENDAR: str = os.getenv("RATE_LIMIT_CALENDAR", "10000,600")  # 10,000 per 10 minutes
    
    # Teams channel messages (heavily throttled)
    RATE_LIMIT_TEAMS_MESSAGES: str = os.getenv("RATE_LIMIT_TEAMS_MESSAGES", "120,60")  # 120 per minute
    
    # Search API (very restrictive)
    RATE_LIMIT_SEARCH: str = os.getenv("RATE_LIMIT_SEARCH", "5,1")  # 5 per second
    
    # User/Group API
    RATE_LIMIT_USERS: str = os.getenv("RATE_LIMIT_USERS", "10000,600")  # 10,000 per 10 minutes
    
    # OneDrive/Files
    RATE_LIMIT_FILES: str = os.getenv("RATE_LIMIT_FILES", "10000,600")  # 10,000 per 10 minutes
    
    # Meeting/Online Meeting API
    RATE_LIMIT_MEETINGS: str = os.getenv("RATE_LIMIT_MEETINGS", "10000,600")  # 10,000 per 10 minutes
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or text
    
    # Server Configuration
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
    MCP_HOST: str = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT: int = int(os.getenv("MCP_PORT", "8001"))
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate required configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not cls.AZURE_CLIENT_ID:
            errors.append("AZURE_CLIENT_ID is required")
        
        if not cls.AZURE_CLIENT_SECRET:
            errors.append("AZURE_CLIENT_SECRET is required")
        
        if not cls.AZURE_TENANT_ID:
            errors.append("AZURE_TENANT_ID is required (cannot use 'common' or 'consumers' for application permissions)")
        
        if cls.HTTP_TIMEOUT <= 0:
            errors.append("HTTP_TIMEOUT must be positive")
        
        if cls.HTTP_MAX_CONNECTIONS <= 0:
            errors.append("HTTP_MAX_CONNECTIONS must be positive")
        
        if cls.MAX_RETRIES < 0:
            errors.append("MAX_RETRIES must be non-negative")
        
        if cls.MAX_CONCURRENT_REQUESTS <= 0:
            errors.append("MAX_CONCURRENT_REQUESTS must be positive")
        
        if cls.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL (got {cls.LOG_LEVEL})")
        
        if cls.LOG_FORMAT not in ["json", "text"]:
            errors.append(f"LOG_FORMAT must be 'json' or 'text' (got {cls.LOG_FORMAT})")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """Print non-sensitive configuration"""
        print("📋 Application Configuration:")
        print(f"   HTTP Timeout: {cls.HTTP_TIMEOUT}s")
        print(f"   Max Connections: {cls.HTTP_MAX_CONNECTIONS}")
        print(f"   Max Keepalive: {cls.HTTP_MAX_KEEPALIVE}")
        print(f"   Max Retries: {cls.MAX_RETRIES}")
        print(f"   Max Concurrent Requests: {cls.MAX_CONCURRENT_REQUESTS}")
        print(f"   Log Level: {cls.LOG_LEVEL}")
        print(f"   Log Format: {cls.LOG_FORMAT}")
        print(f"   FastAPI: {cls.FASTAPI_HOST}:{cls.FASTAPI_PORT}")
        print(f"   MCP: {cls.MCP_HOST}:{cls.MCP_PORT}")
        print()
        print("⚡ Rate Limits:")
        print(f"   Global: {cls.RATE_LIMIT_GLOBAL}")
        print(f"   Mail: {cls.RATE_LIMIT_MAIL}")
        print(f"   Calendar: {cls.RATE_LIMIT_CALENDAR}")
        print(f"   Teams Messages: {cls.RATE_LIMIT_TEAMS_MESSAGES}")
        print(f"   Search: {cls.RATE_LIMIT_SEARCH}")
        print(f"   Users: {cls.RATE_LIMIT_USERS}")
        print(f"   Files: {cls.RATE_LIMIT_FILES}")
        print(f"   Meetings: {cls.RATE_LIMIT_MEETINGS}")


# Global config instance
config = Config()

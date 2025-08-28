"""
Environment-specific configurations for VeriaGuide application
"""
import os
from typing import Dict, Any
from enum import Enum


class Environment(Enum):
    """Application environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class BaseConfig:
    """Base configuration with common settings"""
    
    # Application
    APP_NAME = "VeriaGuide"
    APP_DESCRIPTION = "Your ultimate guide to exploring Veria, Greece"
    APP_VERSION = "1.0.0"
    
    # Site settings
    SITE_NAME = "VeriaGuide"
    SITE_DESCRIPTION = "Your ultimate guide to exploring Veria, Greece"
    SITE_URL = os.getenv("SITE_URL", "https://veriaguide.com")
    
    # Pagination
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", "12"))
    
    # WordPress API
    WP_API_USERNAME = os.getenv("WP_API_USERNAME", "admin")
    WP_API_PASSWORD = os.getenv("WP_API_PASSWORD", "password")
    
    # Google Maps
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Cache settings
    CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "3600"))  # 1 hour
    REDIS_DEFAULT_TTL = int(os.getenv("REDIS_DEFAULT_TTL", "1800"))  # 30 minutes
    REDIS_CACHE_PREFIX = os.getenv("REDIS_CACHE_PREFIX", "veriaguide:")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", None)
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Request timeouts
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
    WP_API_TIMEOUT = int(os.getenv("WP_API_TIMEOUT", "30"))
    
    # Connection pooling
    HTTP_POOL_CONNECTIONS = int(os.getenv("HTTP_POOL_CONNECTIONS", "10"))
    HTTP_POOL_MAXSIZE = int(os.getenv("HTTP_POOL_MAXSIZE", "10"))
    
    # Post type mapping
    POST_TYPES = {
        "museums": "museum",
        "archaeological_sites": "archaeological_site",
        "religious_sites": "religious_site",
        "hiking-trails": "hiking-trail",
        "restaurants": "restaurant",
        "cafes": "cafe",
        "accommodations": "accommodation",
        "ski_resorts": "ski_resort",
        "tours": "tour",
        "hidden_gems": "hidden_gem",
    }


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # WordPress API
    WP_API_URL = os.getenv("WP_API_URL", "http://wordpress:80/wp-json/wp/v2")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Logging
    LOG_LEVEL = "DEBUG"
    
    # Cache settings (shorter TTL for development)
    CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "300"))  # 5 minutes
    REDIS_DEFAULT_TTL = int(os.getenv("REDIS_DEFAULT_TTL", "300"))  # 5 minutes
    
    # Development-specific settings
    RELOAD = True
    WORKERS = 1


class StagingConfig(BaseConfig):
    """Staging environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # WordPress API
    WP_API_URL = os.getenv("WP_API_URL", "http://wordpress:80/wp-json/wp/v2")
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")  # Different DB
    
    # Logging
    LOG_LEVEL = "INFO"
    
    # Cache settings
    CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "1800"))  # 30 minutes
    REDIS_DEFAULT_TTL = int(os.getenv("REDIS_DEFAULT_TTL", "900"))  # 15 minutes
    
    # Performance settings
    RELOAD = False
    WORKERS = 2


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # WordPress API (your production server)
    WP_API_URL = os.getenv("WP_API_URL", "http://veriaguide.gr/wp-json/wp/v2")
    
    # Site settings (your production domain)
    SITE_URL = os.getenv("SITE_URL", "http://veriaguide.gr")
    
    # Redis (local Redis server)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Database settings (your production database)
    DB_NAME = os.getenv("DB_NAME", "veri_veriaguide_db")
    DB_USER = os.getenv("DB_USER", "wp_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # Changed from WARNING to INFO for better monitoring
    
    # Cache settings (longer TTL for production)
    CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "7200"))  # 2 hours
    REDIS_DEFAULT_TTL = int(os.getenv("REDIS_DEFAULT_TTL", "3600"))  # 1 hour
    
    # Performance settings
    RELOAD = False
    WORKERS = int(os.getenv("WORKERS", "4"))
    
    # Security settings (your domain)
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "veriaguide.gr,www.veriaguide.gr").split(",")
    
    # Connection pooling (optimized for production)
    HTTP_POOL_CONNECTIONS = int(os.getenv("HTTP_POOL_CONNECTIONS", "20"))
    HTTP_POOL_MAXSIZE = int(os.getenv("HTTP_POOL_MAXSIZE", "20"))
    
    # Timeouts (more conservative in production)
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "60"))
    WP_API_TIMEOUT = int(os.getenv("WP_API_TIMEOUT", "45"))
    
    @property
    def database_url(self):
        """MySQL connection string for production"""
        return f"mysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class TestingConfig(BaseConfig):
    """Testing environment configuration"""
    
    DEBUG = True
    TESTING = True
    
    # WordPress API (mock or test instance)
    WP_API_URL = os.getenv("WP_API_URL", "http://localhost:8080/wp-json/wp/v2")
    
    # Redis (separate DB for testing)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/15")
    
    # Cache settings (very short TTL for testing)
    CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "60"))  # 1 minute
    REDIS_DEFAULT_TTL = int(os.getenv("REDIS_DEFAULT_TTL", "60"))  # 1 minute
    
    # Testing-specific settings
    ITEMS_PER_PAGE = 5  # Smaller for faster tests


# Configuration mapping
CONFIGS = {
    Environment.DEVELOPMENT: DevelopmentConfig,
    Environment.STAGING: StagingConfig,
    Environment.PRODUCTION: ProductionConfig,
    Environment.TESTING: TestingConfig,
}


def get_config(env_name: str = None) -> BaseConfig:
    """Get configuration based on environment"""
    if env_name is None:
        env_name = os.getenv("ENVIRONMENT", "development")
    
    try:
        environment = Environment(env_name.lower())
        config_class = CONFIGS[environment]
        return config_class()
    except ValueError:
        print(f"Warning: Unknown environment '{env_name}', falling back to development")
        return DevelopmentConfig()


def validate_config(config: BaseConfig) -> Dict[str, Any]:
    """Validate configuration and return validation results"""
    issues = []
    warnings = []
    
    # Required settings validation
    if not config.GOOGLE_MAPS_API_KEY:
        issues.append("GOOGLE_MAPS_API_KEY is not set")
    
    if config.SECRET_KEY == "dev-secret-key-change-in-production" and not config.DEBUG:
        issues.append("SECRET_KEY must be changed in non-development environments")
    
    if not config.WP_API_URL:
        issues.append("WP_API_URL is not set")
    
    if not config.REDIS_URL:
        issues.append("REDIS_URL is not set")
    
    # Warnings for suboptimal settings
    if config.DEBUG and not config.TESTING:
        warnings.append("DEBUG is enabled in non-testing environment")
    
    if config.CACHE_EXPIRY < 60:
        warnings.append("CACHE_EXPIRY is very low, may impact performance")
    
    if config.WORKERS > 8:
        warnings.append("High number of workers may cause resource issues")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "environment": config.__class__.__name__
    }
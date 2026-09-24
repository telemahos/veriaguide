"""
Configuration package for VeriaGuide application
"""
from .environments import Environment, get_config, validate_config

# Get the current configuration
config = get_config()

# Export commonly used configuration values
DEBUG = config.DEBUG
TESTING = config.TESTING
APP_NAME = config.APP_NAME
APP_DESCRIPTION = config.APP_DESCRIPTION
APP_VERSION = config.APP_VERSION

# Site settings
SITE_NAME = config.SITE_NAME
SITE_DESCRIPTION = config.SITE_DESCRIPTION
SITE_URL = config.SITE_URL

# API settings
WP_API_URL = config.WP_API_URL
WP_API_USERNAME = config.WP_API_USERNAME
WP_API_PASSWORD = config.WP_API_PASSWORD
WP_API_TIMEOUT = config.WP_API_TIMEOUT

# Google Maps
GOOGLE_MAPS_API_KEY = config.GOOGLE_MAPS_API_KEY

# Cache settings
CACHE_EXPIRY = config.CACHE_EXPIRY
REDIS_URL = config.REDIS_URL
REDIS_CACHE_PREFIX = config.REDIS_CACHE_PREFIX
REDIS_DEFAULT_TTL = config.REDIS_DEFAULT_TTL

# Application settings
ITEMS_PER_PAGE = config.ITEMS_PER_PAGE
POST_TYPES = config.POST_TYPES
SECRET_KEY = config.SECRET_KEY
ALLOWED_HOSTS = config.ALLOWED_HOSTS

# Performance settings
HTTP_TIMEOUT = config.HTTP_TIMEOUT
HTTP_POOL_CONNECTIONS = config.HTTP_POOL_CONNECTIONS
HTTP_POOL_MAXSIZE = config.HTTP_POOL_MAXSIZE

# Logging
LOG_LEVEL = config.LOG_LEVEL
LOG_FORMAT = config.LOG_FORMAT

# Server settings (for production deployment)
RELOAD = getattr(config, 'RELOAD', False)
WORKERS = getattr(config, 'WORKERS', 1)

__all__ = [
    'config',
    'validate_config',
    'Environment',
    'DEBUG',
    'TESTING',
    'APP_NAME',
    'APP_DESCRIPTION',
    'APP_VERSION',
    'SITE_NAME',
    'SITE_DESCRIPTION',
    'SITE_URL',
    'WP_API_URL',
    'WP_API_USERNAME',
    'WP_API_PASSWORD',
    'WP_API_TIMEOUT',
    'GOOGLE_MAPS_API_KEY',
    'CACHE_EXPIRY',
    'REDIS_URL',
    'REDIS_CACHE_PREFIX',
    'REDIS_DEFAULT_TTL',
    'ITEMS_PER_PAGE',
    'POST_TYPES',
    'SECRET_KEY',
    'ALLOWED_HOSTS',
    'HTTP_TIMEOUT',
    'HTTP_POOL_CONNECTIONS',
    'HTTP_POOL_MAXSIZE',
    'LOG_LEVEL',
    'LOG_FORMAT',
    'RELOAD',
    'WORKERS',
]
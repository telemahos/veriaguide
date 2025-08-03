"""
Legacy configuration file - kept for backward compatibility
Import from app.config package instead
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Import from the new configuration system
from app.config import (
    DEBUG,
    WP_API_URL,
    WP_API_USERNAME,
    WP_API_PASSWORD,
    WP_API_TIMEOUT,
    GOOGLE_MAPS_API_KEY,
    CACHE_EXPIRY,
    REDIS_URL,
    REDIS_CACHE_PREFIX,
    REDIS_DEFAULT_TTL,
    SITE_NAME,
    SITE_DESCRIPTION,
    SITE_URL,
    ITEMS_PER_PAGE,
    POST_TYPES,
    HTTP_TIMEOUT,
    HTTP_POOL_CONNECTIONS,
    HTTP_POOL_MAXSIZE,
)

# Backward compatibility exports
__all__ = [
    'BASE_DIR',
    'DEBUG',
    'WP_API_URL',
    'WP_API_USERNAME',
    'WP_API_PASSWORD',
    'WP_API_TIMEOUT',
    'GOOGLE_MAPS_API_KEY',
    'CACHE_EXPIRY',
    'REDIS_URL',
    'REDIS_CACHE_PREFIX',
    'REDIS_DEFAULT_TTL',
    'SITE_NAME',
    'SITE_DESCRIPTION',
    'SITE_URL',
    'ITEMS_PER_PAGE',
    'POST_TYPES',
    'HTTP_TIMEOUT',
    'HTTP_POOL_CONNECTIONS',
    'HTTP_POOL_MAXSIZE',
] 
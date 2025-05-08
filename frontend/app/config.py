import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# WordPress API settings
WP_API_URL = os.getenv("WP_API_URL", "http://wordpress:80/wp-json/wp/v2")
WP_API_USERNAME = os.getenv("WP_API_USERNAME", "admin")
WP_API_PASSWORD = os.getenv("WP_API_PASSWORD", "password")

# Google Maps API settings
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_GOOGLE_MAPS_API_KEY")

# Cache settings
CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", 3600))  # Default: 1 hour

# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

# Site settings
SITE_NAME = "VeriaGuide"
SITE_DESCRIPTION = "Your ultimate guide to exploring Veria, Greece"
SITE_URL = "https://veriaguide.com"

# Pagination
ITEMS_PER_PAGE = 12

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
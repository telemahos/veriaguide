# Project Structure

## Root Directory
```
├── docker-compose.yml          # Container orchestration
├── README.md                   # Project documentation
├── acf-export-2025-05-09.json  # ACF field definitions export
├── frontend/                   # FastAPI application
├── wp-content/                 # WordPress content directory
└── mysql-data/                 # Database persistence
```

## Frontend Application (`frontend/`)
```
frontend/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── app/                        # Application modules
│   ├── __init__.py
│   ├── config.py              # Configuration and constants
│   ├── api/                   # External API integrations
│   │   └── wordpress.py       # WordPress REST API client
│   └── utils/                 # Utility modules
│       ├── favorites.py       # Favorites management
│       └── helpers.py         # Helper functions
├── static/                    # Static assets
│   ├── css/
│   ├── js/
│   └── img/
└── templates/                 # Jinja2 HTML templates
    ├── base/                  # Base templates
    ├── accommodations/        # Category-specific templates
    ├── archaeological_sites/
    ├── cafes/
    ├── contact/
    ├── favorites/
    ├── hiking_trails/
    ├── museums/
    ├── religious_sites/
    ├── restaurants/
    ├── search/
    ├── ski_resorts/
    └── tours/
```

## WordPress Content (`wp-content/`)
- **plugins/**: WordPress plugins including ACF, Custom Post Type UI
- **themes/**: WordPress themes (twentytwentyfive, etc.)
- **uploads/**: Media files and user uploads

## Key Conventions

### Template Organization
- Each content type has its own template directory
- Standard template names: `list.html` for listings, `detail.html` for individual items
- Base templates in `base/` directory for shared layouts

### URL Structure
- Category listings: `/{category}` (e.g., `/restaurants`, `/museums`)
- Item details: `/{category}/{slug}` (e.g., `/restaurants/taverna-example`)
- Special routes: `/map`, `/search`, `/favorites`, `/contact`

### Content Types Mapping
```python
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
```

### Configuration
- Environment variables in `.env` files and Docker environment
- Main configuration in `frontend/app/config.py`
- WordPress configuration via `docker-compose.yml`

### Static Assets
- CSS files in `frontend/static/css/`
- JavaScript files in `frontend/static/js/`
- Images in `frontend/static/img/`
- Served at `/static/` URL path
# Technology Stack

## Backend
- **WordPress**: Headless CMS for content management
- **MariaDB**: Database for WordPress content storage
- **Advanced Custom Fields (ACF)**: Custom field management for structured content
- **Custom Post Type UI**: Managing different content types (museums, restaurants, etc.)

## Frontend
- **FastAPI**: Python web framework for the user-facing application
- **Jinja2**: Template engine for HTML rendering
- **Uvicorn**: ASGI server for FastAPI
- **Pydantic**: Data validation and serialization
- **Requests/HTTPX**: HTTP client libraries for WordPress API communication

## Infrastructure
- **Docker Compose**: Container orchestration for development
- **Python 3.11**: Runtime environment
- **Redis**: In-memory caching for improved performance
- **Google Maps API**: Interactive maps and location services

## Key Dependencies
```
fastapi>=0.92.0
uvicorn>=0.21.1
jinja2>=3.1.2
requests>=2.31.0
python-dotenv>=1.0.0
aiohttp>=3.8.4
redis>=4.5.0
aioredis>=2.0.0
```

## Common Commands

### Development Setup
```bash
# Start the entire stack
docker-compose down && docker-compose up --build

# Access services
# WordPress admin: http://localhost:8086/wp-admin
# Frontend app: http://localhost:8000
# Database: localhost:3306
```

### Frontend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Clear application cache
curl http://localhost:8000/admin/clear-cache

# Warm cache (requires ADMIN_API_KEY)
curl -X POST http://localhost:8000/admin/warm-cache \
  -H "X-API-Key: $ADMIN_API_KEY"

# Check cache warming status
curl http://localhost:8000/admin/cache-warming-status \
  -H "X-API-Key: $ADMIN_API_KEY"
```

### Database Credentials
- Database: `veriaguide_db`
- User: `wp_user`
- Password: `***REMOVED***` (should be changed in production)

### Redis Configuration
- URL: `redis://redis:6379/0`
- Default TTL: 30 minutes
- Cache prefix: `veriaguide:`
- **Cache Warming**: Automatic on startup (575 items in ~1.5s)
- **Cache Invalidation**: Available via admin endpoints

## Cache Warming

The application automatically warms the cache on startup to improve performance:

- **Automatic**: Runs in background 2 seconds after startup
- **Content Cached**: All museums, archaeological sites, religious sites, restaurants, cafes, accommodations, and map locations
- **Performance**: First requests are 5-10x faster with warm cache
- **Manual Control**: Admin endpoints available for cache management

See `CACHE_WARMING_GUIDE.md` for detailed documentation.

## Environment Variables
- `WP_API_URL`: WordPress REST API endpoint
- `GOOGLE_MAPS_API_KEY`: Google Maps API key
- `DEBUG`: Enable debug mode
- `CACHE_EXPIRY`: Cache expiration time in seconds
- `REDIS_URL`: Redis connection URL
- `REDIS_DEFAULT_TTL`: Default Redis cache TTL in seconds
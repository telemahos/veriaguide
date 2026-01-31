# VeriaGuide - AI Travel Guide for Veria, Greece

VeriaGuide is a comprehensive tourism directory web application for Veria, Greece. It serves as a guide for exploring the city's attractions, restaurants, accommodations, and cultural sites.

## Features

- **Multi-category listings**: Museums, archaeological sites, religious sites, hiking trails, restaurants, cafes, accommodations, ski resorts, tours, and hidden gems
- **Interactive maps**: OpenStreetMap integration with location markers and detailed views
- **Search and filtering**: Full-text search across all content types with advanced filtering options
- **Favorites system**: Users can save and manage their favorite places
- **Responsive design**: Mobile-friendly interface for tourists on the go
- **Multilingual support**: German language interface with Greek location content
- **Booking.com Integration**: Display pricing, ratings, and booking links for accommodations

## Architecture

The application uses a headless WordPress backend for content management with a FastAPI frontend for the user-facing website.

```
┌─────────────────────────────────────────────────────────────┐
│                    WordPress (Backend)                      │
│  - Content Management                                       │
│  - ACF Custom Fields                                        │
│  - REST API                                                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI (Frontend)                       │
│  - User-facing application                                  │
│  - Template rendering                                       │
│  - Redis caching                                            │
│  - Booking.com integration                                  │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **WordPress**: Headless CMS for content management
- **MariaDB**: Database for WordPress content storage
- **Advanced Custom Fields (ACF)**: Custom field management for structured content
- **Custom Post Type UI**: Managing different content types

### Frontend
- **FastAPI**: Python web framework for the user-facing application
- **Jinja2**: Template engine for HTML rendering
- **Uvicorn**: ASGI server for FastAPI
- **Pydantic**: Data validation and serialization
- **HTTPX**: HTTP client for WordPress API communication

### Infrastructure
- **Docker Compose**: Container orchestration for development
- **Python 3.11**: Runtime environment
- **Redis**: In-memory caching for improved performance
- **OpenStreetMap (Leaflet.js)**: Interactive maps and location services

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/veriaguide.git
cd veriaguide
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the application:
```bash
docker-compose up -d
```

4. Access the services:
- **Frontend**: http://localhost:8000
- **WordPress Admin**: http://localhost:8086/wp-admin
- **Database**: localhost:3306

## Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# WordPress Configuration
WP_API_URL=http://wordpress:80/wp-json/wp/v2
WP_API_USERNAME=your_username
WP_API_PASSWORD=your_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_DEFAULT_TTL=1800

# Booking.com Integration
BOOKING_AFFILIATE_ID=your_affiliate_id
BOOKING_TRACKING_SOURCE=veriaguide
BOOKING_TRACKING_CAMPAIGN=accommodations

# Application Settings
DEBUG=True
SITE_URL=http://localhost:8000
```

## Booking.com Integration

VeriaGuide integrates with Booking.com to display accommodation pricing, ratings, and booking links.

### Features

- Display Booking.com prices and ratings
- Generate affiliate links for bookings
- Manual data management via WordPress ACF fields
- Data validation and XSS protection

### Setup

1. **Configure ACF Fields in WordPress**:
   - See `docs/BOOKING_INTEGRATION.md` for detailed instructions

2. **Set Environment Variables**:
   ```bash
   BOOKING_AFFILIATE_ID=your_affiliate_id
   ```

3. **Update Accommodation Data**:
   - Edit accommodations in WordPress
   - Fill in Booking.com ACF fields
   - Save and verify display

For detailed documentation, see:
- [Booking.com Integration Guide](docs/BOOKING_INTEGRATION.md)
- [Implementation Summary](docs/BOOKING_INTEGRATION_SUMMARY.md)

## Development

### Project Structure

```
veriaguide/
├── frontend/                   # FastAPI application
│   ├── app/
│   │   ├── api/               # External API integrations
│   │   ├── services/          # Business logic services
│   │   ├── utils/             # Utility functions
│   │   ├── middleware/        # Custom middleware
│   │   └── tests/             # Test suite
│   ├── static/                # Static assets (CSS, JS, images)
│   ├── templates/             # Jinja2 HTML templates
│   └── main.py                # Application entry point
├── wp-content/                # WordPress content
├── docs/                      # Documentation
├── .kiro/specs/               # Feature specifications
└── docker-compose.yml         # Container orchestration
```

### Running Tests

```bash
# Run all tests
docker-compose exec frontend pytest -v

# Run specific test suite
docker-compose exec frontend pytest app/tests/test_booking_*.py -v

# Run with coverage
docker-compose exec frontend pytest --cov=app --cov-report=html

# Run property-based tests
docker-compose exec frontend pytest -v -m property
```

### Common Commands

```bash
# Start the entire stack
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Restart frontend
docker-compose restart frontend

# Clear cache
curl http://localhost:8000/admin/clear-cache -H "X-API-Key: your_api_key"

# Warm cache
curl -X POST http://localhost:8000/admin/warm-cache -H "X-API-Key: your_api_key"

# Check health
curl http://localhost:8000/health
```

## Cache Management

### Automatic Cache Warming

The application automatically warms the cache on startup:

- **Automatic**: Runs in background 2 seconds after startup
- **Content Cached**: All museums, archaeological sites, religious sites, restaurants, cafes, accommodations, and map locations
- **Performance**: First requests are 5-10x faster with warm cache

### Manual Cache Control

```bash
# Clear all cache
curl http://localhost:8000/admin/clear-cache -H "X-API-Key: your_api_key"

# Clear specific pattern
curl -X POST http://localhost:8000/admin/clear-cache/accommodation -H "X-API-Key: your_api_key"

# Warm cache for specific category
curl -X POST http://localhost:8000/admin/warm-cache/accommodation -H "X-API-Key: your_api_key"

# Check cache status
curl http://localhost:8000/admin/cache-warming-status -H "X-API-Key: your_api_key"
```

## API Endpoints

### Public Endpoints

- `GET /` - Home page
- `GET /{category}` - Category listing (e.g., `/restaurants`, `/museums`)
- `GET /{category}/{slug}` - Item detail page
- `GET /map` - Interactive map view
- `GET /search` - Search results
- `GET /favorites` - User favorites
- `GET /contact` - Contact form
- `GET /health` - Health check
- `GET /sitemap.xml` - SEO sitemap
- `GET /robots.txt` - Robots file

### Admin Endpoints (Require API Key)

- `GET /admin/clear-cache` - Clear application cache
- `GET /admin/cache-info` - Get cache statistics
- `POST /admin/warm-cache` - Manually trigger cache warming
- `GET /admin/metrics` - Get application metrics
- `GET /admin/config` - Get configuration (sanitized)

## Monitoring

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

### Metrics

```bash
# Application metrics
curl http://localhost:8000/admin/metrics -H "X-API-Key: your_api_key"

# Health metrics
curl http://localhost:8000/admin/metrics/health -H "X-API-Key: your_api_key"
```

## Documentation

- [Booking.com Integration](docs/BOOKING_INTEGRATION.md)
- [Implementation Summary](docs/BOOKING_INTEGRATION_SUMMARY.md)
- [Cache Warming Guide](docs/CACHE_WARMING_GUIDE.md)
- [Security Setup](docs/SECURITY_SETUP.md)
- [Deployment Guide](docs/DEPLOYMENT_FIX.md)

## Troubleshooting

### Common Issues

1. **WordPress API not accessible**:
   - Check WordPress container is running: `docker-compose ps`
   - Verify WordPress URL in `.env`
   - Check WordPress REST API: `curl http://localhost:8086/wp-json/wp/v2`

2. **Redis connection failed**:
   - Check Redis container is running: `docker-compose ps`
   - Verify Redis URL in `.env`
   - Test Redis: `docker-compose exec redis redis-cli ping`

3. **Booking.com data not displaying**:
   - Check ACF fields are configured in WordPress
   - Verify `BOOKING_AFFILIATE_ID` is set in `.env`
   - Check application logs: `docker-compose logs frontend`

4. **Cache not working**:
   - Check Redis is running
   - Clear cache: `curl http://localhost:8000/admin/clear-cache`
   - Check cache stats: `curl http://localhost:8000/admin/cache-info`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

### Development Workflow

1. Create a spec in `.kiro/specs/` for new features
2. Write tests first (TDD approach)
3. Implement the feature
4. Run tests and ensure coverage > 85%
5. Update documentation
6. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues or questions:

1. Check the documentation in `docs/`
2. Review application logs: `docker-compose logs frontend`
3. Check WordPress logs: `docker-compose logs wordpress`
4. Open an issue on GitHub

## Acknowledgments

- Built with FastAPI and WordPress
- Maps powered by OpenStreetMap
- Booking integration with Booking.com
- Caching with Redis

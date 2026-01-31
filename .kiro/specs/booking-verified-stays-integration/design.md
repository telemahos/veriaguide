# Design Document: Booking.com Verified Stays Integration

## Overview

This design specifies the integration of Booking.com Demand API into VeriaGuide to provide a "Verified Stays" category with real-time accommodation data. The integration follows VeriaGuide's existing architecture pattern: WordPress backend for data storage, FastAPI frontend for user interface, and Redis for caching. The system fetches accommodation data from Booking.com's API, stores it in WordPress as custom posts, and displays it through dedicated frontend routes with filtering, sorting, and deep linking to Booking.com for reservations.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                             │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Frontend Application                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes: /verified-stays, /verified-stays/{slug}     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Booking API Client (HTTPX async)                    │  │
│  │  - Rate Limiter                                       │  │
│  │  - Response Validator                                 │  │
│  │  - Error Handler                                      │  │
│  └──────────────────────────────────────────────────────┘  │
└────────┬─────────────────────────┬──────────────────────────┘
         │                         │
         │ REST API                │ Redis Protocol
         ▼                         ▼
┌──────────────────────┐  ┌──────────────────────┐
│  WordPress Backend   │  │   Redis Cache        │
│  - verified_stay CPT │  │  - API responses     │
│  - ACF Fields        │  │  - Processed data    │
│  - REST API          │  │  - TTL: 30 min       │
└──────────────────────┘  └──────────────────────┘
         ▲
         │ Sync Job (Daily Cron)
         │
┌──────────────────────────────────────────────────────────────┐
│              Booking.com Demand API                          │
│  - /accommodations/search                                    │
│  - /accommodations/details                                   │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

**User Browsing Flow:**
1. User requests /verified-stays
2. FastAPI checks Redis cache for property list
3. If cache miss, FastAPI queries WordPress REST API
4. FastAPI renders list view with cached/fresh data
5. User clicks property → FastAPI fetches detail from cache/WordPress
6. User clicks "Book Now" → Redirected to Booking.com via deep link

**Synchronization Flow:**
1. Daily cron triggers sync job
2. Sync job calls Booking.com search API (coordinates + radius)
3. For each property, fetch detailed information
4. Validate and transform API response
5. Check if property exists in WordPress (by booking_hotel_id)
6. Create new or update existing verified_stay post
7. Update ACF fields with all property data
8. Invalidate relevant Redis caches
9. Log sync statistics

## Components and Interfaces

### 1. Booking API Client (`app/api/booking.py`)

**Purpose:** Async HTTP client for Booking.com Demand API with rate limiting, caching, and error handling.

**Class: BookingAPIClient**

```python
class BookingAPIClient:
    """Async client for Booking.com Demand API."""
    
    def __init__(
        self,
        api_key: str,
        affiliate_id: str,
        base_url: str = "https://api.booking.com/v3",
        rate_limit: int = 10,  # requests per second
        redis_client: Optional[Redis] = None
    ):
        """Initialize client with credentials and rate limiter."""
        
    async def search_accommodations(
        self,
        latitude: float,
        longitude: float,
        radius_km: int = 10,
        checkin: Optional[date] = None,
        checkout: Optional[date] = None,
        currency: str = "EUR",
        limit: int = 100
    ) -> List[AccommodationSearchResult]:
        """
        Search for accommodations within radius of coordinates.
        
        Returns list of basic property information.
        Caches results in Redis for 30 minutes.
        """
        
    async def get_accommodation_details(
        self,
        hotel_id: str,
        checkin: Optional[date] = None,
        checkout: Optional[date] = None,
        currency: str = "EUR"
    ) -> AccommodationDetail:
        """
        Get detailed information for a specific property.
        
        Returns complete property data including facilities, photos, reviews.
        Caches results in Redis for 30 minutes.
        """
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make rate-limited API request with retry logic.
        
        Implements exponential backoff for retries (max 3 attempts).
        Raises BookingAPIError on failure.
        """
```

**Error Handling:**
- `BookingAPIError`: Base exception for all API errors
- `BookingAuthError`: Authentication failures (401, 403)
- `BookingRateLimitError`: Rate limit exceeded (429)
- `BookingNotFoundError`: Property not found (404)
- `BookingValidationError`: Invalid response data

### 2. Rate Limiter (`app/utils/rate_limiter.py`)

**Purpose:** Token bucket rate limiter to enforce API request limits.

**Class: RateLimiter**

```python
class RateLimiter:
    """Token bucket rate limiter for API requests."""
    
    def __init__(self, rate: int, per_seconds: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            rate: Maximum requests allowed
            per_seconds: Time window in seconds
        """
        
    async def acquire(self) -> None:
        """
        Acquire permission to make a request.
        
        Blocks until a token is available.
        Uses asyncio.sleep for non-blocking delays.
        """
        
    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
```

### 3. Data Models (`app/models/booking.py`)

**Purpose:** Pydantic models for API request/response validation.

```python
class AccommodationSearchResult(BaseModel):
    """Search result from /accommodations/search."""
    hotel_id: str
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str
    min_price: Optional[float] = Field(ge=0)
    currency: str = "EUR"
    rating: Optional[float] = Field(ge=0, le=10)
    review_score: Optional[float] = Field(ge=0, le=10)
    review_count: Optional[int] = Field(ge=0)
    thumbnail_url: Optional[str]
    deep_link: str

class Facility(BaseModel):
    """Property facility/amenity."""
    name: str
    icon: Optional[str]
    category: Optional[str]

class Photo(BaseModel):
    """Property photo."""
    url: str
    caption: Optional[str]
    width: Optional[int]
    height: Optional[int]

class AccommodationDetail(BaseModel):
    """Detailed property information from /accommodations/details."""
    hotel_id: str
    name: str
    description: Optional[str]
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str
    city: str
    postal_code: Optional[str]
    country: str
    min_price: Optional[float] = Field(ge=0)
    currency: str = "EUR"
    rating: Optional[float] = Field(ge=0, le=10)
    review_score: Optional[float] = Field(ge=0, le=10)
    review_count: Optional[int] = Field(ge=0)
    facilities: List[Facility] = []
    photos: List[Photo] = []
    deep_link: str
    check_in_time: Optional[str]
    check_out_time: Optional[str]
```

### 4. WordPress Sync Service (`app/services/booking_sync.py`)

**Purpose:** Synchronize Booking.com data to WordPress verified_stay posts.

**Class: BookingSyncService**

```python
class BookingSyncService:
    """Service for syncing Booking.com data to WordPress."""
    
    def __init__(
        self,
        booking_client: BookingAPIClient,
        wordpress_client: WordPressClient,
        redis_client: Redis
    ):
        """Initialize sync service with API clients."""
        
    async def sync_all_properties(
        self,
        latitude: float,
        longitude: float,
        radius_km: int = 10
    ) -> SyncResult:
        """
        Sync all properties within search radius.
        
        Returns:
            SyncResult with counts of created, updated, failed properties
        """
        
    async def sync_property(
        self,
        hotel_id: str
    ) -> bool:
        """
        Sync a single property by hotel_id.
        
        Returns True if successful, False otherwise.
        """
        
    async def _create_or_update_post(
        self,
        detail: AccommodationDetail
    ) -> int:
        """
        Create new or update existing verified_stay post.
        
        Returns WordPress post ID.
        """
        
    def _transform_to_acf_fields(
        self,
        detail: AccommodationDetail
    ) -> Dict[str, Any]:
        """Transform API data to ACF field format."""

class SyncResult(BaseModel):
    """Result of sync operation."""
    total_found: int
    created: int
    updated: int
    failed: int
    errors: List[str]
    duration_seconds: float
```

### 5. WordPress Client Extension (`app/api/wordpress.py`)

**Purpose:** Extend existing WordPress client with verified_stay operations.

**New Methods:**

```python
class WordPressClient:
    # ... existing methods ...
    
    async def get_verified_stay_by_booking_id(
        self,
        booking_hotel_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find verified_stay post by booking_hotel_id ACF field.
        
        Returns post data or None if not found.
        """
        
    async def create_verified_stay(
        self,
        title: str,
        acf_fields: Dict[str, Any],
        status: str = "publish"
    ) -> int:
        """
        Create new verified_stay post with ACF fields.
        
        Returns post ID.
        """
        
    async def update_verified_stay(
        self,
        post_id: int,
        acf_fields: Dict[str, Any]
    ) -> bool:
        """
        Update verified_stay post ACF fields.
        
        Returns True if successful.
        """
        
    async def get_verified_stays(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "price_asc"
    ) -> List[Dict[str, Any]]:
        """
        Get paginated list of verified stays with filtering and sorting.
        
        Filters: price_min, price_max, min_rating, facilities
        Sort: price_asc, price_desc, rating_desc, distance_asc
        """
```

### 6. FastAPI Routes (`main.py`)

**Purpose:** HTTP endpoints for verified stays browsing.

```python
@app.get("/verified-stays")
async def list_verified_stays(
    request: Request,
    page: int = 1,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    min_rating: Optional[float] = None,
    facilities: Optional[str] = None,  # comma-separated
    sort: str = "price_asc"
):
    """
    Display list of verified stays with filtering and sorting.
    
    Caches rendered page in Redis for 30 minutes.
    """

@app.get("/verified-stays/{slug}")
async def verified_stay_detail(
    request: Request,
    slug: str
):
    """
    Display detailed property information.
    
    Caches property data in Redis for 30 minutes.
    """

@app.post("/admin/sync-verified-stays")
async def trigger_sync(
    request: Request,
    api_key: str = Header(None, alias="X-API-Key")
):
    """
    Manually trigger Booking.com data sync.
    
    Requires admin API key authentication.
    Returns sync statistics.
    """
```

### 7. Caching Strategy (`app/utils/booking_cache.py`)

**Purpose:** Redis caching layer for Booking.com data.

**Cache Keys:**
- `veriaguide:booking:search:{lat}:{lng}:{radius}` - Search results (30 min)
- `veriaguide:booking:detail:{hotel_id}` - Property details (30 min)
- `veriaguide:booking:list:{page}:{filters_hash}` - Rendered list pages (30 min)
- `veriaguide:booking:property:{slug}` - Rendered detail pages (30 min)

**Functions:**

```python
async def cache_search_results(
    redis: Redis,
    latitude: float,
    longitude: float,
    radius: int,
    results: List[AccommodationSearchResult],
    ttl: int = 1800
) -> None:
    """Cache search results."""

async def get_cached_search_results(
    redis: Redis,
    latitude: float,
    longitude: float,
    radius: int
) -> Optional[List[AccommodationSearchResult]]:
    """Retrieve cached search results."""

async def invalidate_verified_stays_cache(
    redis: Redis
) -> int:
    """
    Invalidate all verified stays caches.
    
    Returns count of keys deleted.
    """
```

### 8. Background Sync Job (`app/jobs/sync_booking.py`)

**Purpose:** Scheduled task for daily data synchronization.

```python
async def run_daily_sync():
    """
    Daily sync job for Booking.com data.
    
    Configured via environment variables:
    - VERIA_LATITUDE: 40.5246
    - VERIA_LONGITUDE: 22.2022
    - BOOKING_SEARCH_RADIUS: 10
    
    Logs sync statistics and errors.
    """
```

**Scheduling:** Use APScheduler or system cron to run daily at configured time (e.g., 3 AM local time).

## Data Models

### WordPress Custom Post Type: verified_stay

**Post Type Configuration:**
- Name: `verified_stay`
- Labels: "Verified Stay" / "Verified Stays"
- Public: Yes
- Has Archive: Yes
- Rewrite: `verified-stays`
- Supports: title, editor, thumbnail
- Menu Icon: dashicons-building

### ACF Field Group: Booking.com Data

**Field Group Configuration:**
- Location: Post Type = verified_stay
- Style: Standard
- Position: Normal

**Fields:**

| Field Name | Type | Required | Description |
|------------|------|----------|-------------|
| booking_hotel_id | Text | Yes | Unique Booking.com property ID |
| booking_name | Text | Yes | Property name |
| booking_description | Textarea | No | Property description |
| booking_address | Text | Yes | Full street address |
| booking_city | Text | Yes | City name |
| booking_postal_code | Text | No | Postal code |
| booking_country | Text | Yes | Country name |
| booking_latitude | Number | Yes | Latitude coordinate |
| booking_longitude | Number | Yes | Longitude coordinate |
| booking_price_min | Number | No | Minimum nightly price |
| booking_currency | Text | Yes | Price currency code |
| booking_rating | Number | No | Property star rating (0-10) |
| booking_review_score | Number | No | Guest review score (0-10) |
| booking_review_count | Number | No | Number of reviews |
| booking_facilities | Repeater | No | Property facilities/amenities |
| ↳ facility_name | Text | Yes | Facility name |
| ↳ facility_icon | Text | No | Icon identifier |
| ↳ facility_category | Text | No | Category (e.g., "General", "Room") |
| booking_photos | Gallery | No | Property photos |
| booking_deep_link | URL | Yes | Affiliate link to Booking.com |
| booking_check_in_time | Text | No | Check-in time |
| booking_check_out_time | Text | No | Check-out time |
| booking_last_synced | Date Time Picker | Yes | Last sync timestamp |

### Database Indexes

For performance, add WordPress database indexes:
- Index on `booking_hotel_id` meta key (unique lookups)
- Index on `booking_price_min` meta key (price filtering)
- Index on `booking_rating` meta key (rating filtering)
- Index on `booking_last_synced` meta key (sync monitoring)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: API Authentication Headers

*For any* Booking.com API request (search or details), the HTTP headers must include a valid Bearer token and the Affiliate ID parameter.

**Validates: Requirements 2.1**

### Property 2: API Request Date Parameters

*For any* search or detail request where check-in and check-out dates are provided, those dates must be included in the API request parameters.

**Validates: Requirements 2.6**

### Property 3: Sync Updates Existing Properties

*For any* property that already exists in WordPress (matched by booking_hotel_id), running the sync operation must update the existing post rather than creating a duplicate.

**Validates: Requirements 3.3**

### Property 4: Sync Creates New Properties

*For any* property returned by the Booking.com API that does not exist in WordPress, running the sync operation must create a new verified_stay post.

**Validates: Requirements 3.4**

### Property 5: Sync Timestamp Recording

*For any* property synchronized from Booking.com, the resulting WordPress post must have a booking_last_synced timestamp reflecting the sync operation time.

**Validates: Requirements 3.5**

### Property 6: Sync Error Isolation

*For any* batch of properties being synchronized, if one property fails to sync, the remaining properties in the batch must still be processed.

**Validates: Requirements 3.6**

### Property 7: Sync Inactive Property Marking

*For any* property that exists in WordPress but is no longer returned by the Booking.com API search, the sync operation must mark it as inactive.

**Validates: Requirements 3.8**

### Property 8: WordPress Storage Completeness

*For any* Booking.com property data, when stored in WordPress, all required ACF fields (booking_hotel_id, booking_name, booking_address, booking_latitude, booking_longitude, booking_price_min, booking_currency, booking_rating, booking_review_score, booking_review_count, booking_facilities, booking_photos, booking_deep_link, booking_last_synced) must be populated with the corresponding API data or sensible defaults.

**Validates: Requirements 4.1, 4.4, 4.5, 4.6, 4.7**

### Property 9: Unique Hotel ID Constraint

*For any* booking_hotel_id value, attempting to create multiple verified_stay posts with the same booking_hotel_id must result in either updating the existing post or preventing the duplicate creation.

**Validates: Requirements 4.2, 4.3**

### Property 10: Facility Data Structure

*For any* property with facilities, each facility stored in the booking_facilities repeater field must have both a name subfield and an icon subfield.

**Validates: Requirements 4.8**

### Property 11: API Response Caching

*For any* Booking.com API response (search or details), after caching in Redis, retrieving the cache within 30 minutes must return the same data without making a new API call.

**Validates: Requirements 5.1, 5.2**

### Property 12: Cache Key Prefix Convention

*For any* cache key created by the Verified Stays system, the key must start with the prefix "veriaguide:booking:".

**Validates: Requirements 5.3**

### Property 13: Cache Hit Behavior

*For any* request where valid cached data exists in Redis, the system must return the cached data without making an API call to Booking.com.

**Validates: Requirements 5.4**

### Property 14: Cache Invalidation on Sync

*For any* sync operation that updates property data, all relevant cache entries for verified stays must be invalidated.

**Validates: Requirements 5.7**

### Property 15: List View Field Display

*For any* property displayed in the list view, the rendered output must contain the property name, thumbnail image, minimum price, currency, rating, review score, and review count.

**Validates: Requirements 6.2, 6.3**

### Property 16: Filter Correctness

*For any* combination of filters (price range, minimum rating, facilities), all properties returned in the filtered results must satisfy all applied filter criteria.

**Validates: Requirements 6.4**

### Property 17: Sort Order Correctness

*For any* sort option selected (price ascending, price descending, rating descending, distance ascending), the returned properties must be ordered according to that criterion.

**Validates: Requirements 6.5**

### Property 18: Pagination Consistency

*For any* page number in the paginated results, the page must contain at most 20 properties, and no property must appear on multiple pages.

**Validates: Requirements 6.7**

### Property 19: Distance Calculation Presence

*For any* property displayed, the output must include a calculated distance from Veria center coordinates (40.5246, 22.2022).

**Validates: Requirements 6.8**

### Property 20: Detail View Field Completeness

*For any* property detail page, the rendered output must contain the property name, full address, description, location map, minimum price, currency, rating, review score, review count, and last synchronization timestamp.

**Validates: Requirements 7.2, 7.4, 7.5, 7.8**

### Property 21: Photo Gallery Completeness

*For any* property with N photos, the detail view must display all N photos in the gallery.

**Validates: Requirements 7.3**

### Property 22: Facility List Completeness

*For any* property with N facilities, the detail view must display all N facilities with their icons.

**Validates: Requirements 7.6**

### Property 23: Deep Link Presence

*For any* property detail page, the rendered output must contain a "Book Now" button with a deep link URL to Booking.com.

**Validates: Requirements 7.7**

### Property 24: Deep Link Structure

*For any* property, the generated deep link must include the affiliate ID, the specific hotel ID, and tracking parameters. When check-in and check-out dates are provided, the deep link must also include those dates.

**Validates: Requirements 8.1, 8.2, 8.3, 8.5**

### Property 25: Deep Link Target Attribute

*For any* deep link rendered in HTML, the anchor tag must have the target="_blank" attribute to open in a new tab.

**Validates: Requirements 8.4**

### Property 26: Rate Limiting Enforcement

*For any* sequence of API requests to Booking.com, the rate limiter must ensure that no more than 10 requests are made within any 1-second window.

**Validates: Requirements 9.1, 9.2, 9.4**

### Property 27: Rate Limit Event Logging

*For any* rate limiting event (delay or queue), a log entry must be created recording the event.

**Validates: Requirements 9.5**

### Property 28: API Error Logging

*For any* Booking.com API error response, a log entry must be created containing the error details and full context.

**Validates: Requirements 10.1**

### Property 29: API Failure Fallback to Cache

*For any* request where the Booking.com API is unavailable and cached data exists, the system must return the cached data.

**Validates: Requirements 10.2**

### Property 30: Detail Request Fallback to WordPress

*For any* property detail request where the Booking.com API fails, the system must return basic information from the WordPress verified_stay post.

**Validates: Requirements 10.5**

### Property 31: API Request Retry Logic

*For any* failed API request, the system must retry up to 3 times with exponential backoff delays before giving up.

**Validates: Requirements 10.6**

### Property 32: API Request Logging

*For any* Booking.com API request, a log entry must be created containing the timestamp, endpoint, and request parameters.

**Validates: Requirements 11.1**

### Property 33: API Response Logging

*For any* Booking.com API response, a log entry must be created containing the status code and response summary.

**Validates: Requirements 11.2**

### Property 34: Sync Operation Logging

*For any* sync operation, log entries must be created for sync start, completion, and statistics (properties created, updated, failed).

**Validates: Requirements 11.3**

### Property 35: Cache Operation Logging

*For any* cache hit or miss, a log entry must be created for performance monitoring.

**Validates: Requirements 11.5**

### Property 36: Error Stack Trace Logging

*For any* error or exception, a log entry must be created containing the full stack trace.

**Validates: Requirements 11.6**

### Property 37: Structured Log Format

*For any* log entry created by the system, it must include a severity level (DEBUG, INFO, WARNING, ERROR).

**Validates: Requirements 11.7**

### Property 38: Configuration Validation on Startup

*For any* required configuration parameter (API credentials, coordinates, radius, cache TTL, rate limits), if it is missing or invalid at startup, the system must fail to start and raise a clear error message.

**Validates: Requirements 12.6, 12.7**

### Property 39: API Response Validation

*For any* Booking.com API response, the data must be validated against Pydantic models, and invalid responses must raise validation exceptions.

**Validates: Requirements 14.1, 14.2**

### Property 40: Required Field Validation

*For any* API response, if required fields (hotel_id, name, latitude, longitude) are missing, validation must fail with an exception.

**Validates: Requirements 14.3**

### Property 41: Numeric Field Validation

*For any* API response, numeric fields (price, rating, review_score, review_count) must be validated as non-negative numbers, and invalid values must cause validation errors.

**Validates: Requirements 14.4**

### Property 42: Coordinate Range Validation

*For any* API response, latitude values must be in the range [-90, 90] and longitude values must be in the range [-180, 180], and out-of-range values must cause validation errors.

**Validates: Requirements 14.5**

### Property 43: Optional Field Default Values

*For any* API response where optional fields are missing, the system must populate those fields with sensible default values (e.g., empty list for facilities, None for optional strings).

**Validates: Requirements 14.6**

### Property 44: Text Field Sanitization

*For any* text field received from the API (name, description, address), the system must sanitize the content to prevent injection attacks before storing or displaying.

**Validates: Requirements 14.7**

## Error Handling

### Error Categories

**1. API Errors**
- Authentication failures (401, 403)
- Rate limiting (429)
- Not found (404)
- Server errors (500, 502, 503)
- Network timeouts
- Connection failures

**2. Validation Errors**
- Invalid API response structure
- Missing required fields
- Out-of-range values
- Type mismatches

**3. Data Errors**
- Duplicate hotel IDs
- Missing WordPress posts
- ACF field update failures
- Database connection errors

**4. Cache Errors**
- Redis connection failures
- Cache serialization errors
- Cache key conflicts

### Error Handling Strategies

**API Errors:**
- Retry with exponential backoff (3 attempts)
- Log full error context
- Fall back to cached data when available
- Display user-friendly error messages
- Alert administrators for authentication failures

**Validation Errors:**
- Log validation details
- Skip invalid properties during sync
- Continue processing remaining items
- Report validation failures in sync statistics

**Data Errors:**
- Log database errors with context
- Roll back failed transactions
- Continue processing remaining items
- Report failures in sync statistics

**Cache Errors:**
- Log cache failures
- Continue operation without cache
- Degrade gracefully to direct API/database access
- Monitor cache health

### Error Response Format

```python
class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: str
```

### Logging Strategy

All errors must be logged with:
- Timestamp
- Severity level (ERROR, WARNING)
- Error type and message
- Full stack trace
- Request context (endpoint, parameters)
- User-facing message (if applicable)

## Testing Strategy

### Dual Testing Approach

The Verified Stays integration requires both unit tests and property-based tests for comprehensive coverage:

**Unit Tests** focus on:
- Specific configuration values (Veria coordinates, 10km radius, EUR currency)
- Specific endpoint usage (/accommodations/search, /accommodations/details)
- WordPress configuration (verified_stay post type exists)
- Navigation menu rendering (both menu items present)
- Edge cases (empty results, no cached data, authentication failures)
- Integration points (WordPress API, Redis connection)

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- API authentication across all requests
- Data validation across all responses
- Caching behavior for any API response
- Sync operations for any property data
- Filter and sort correctness for any criteria
- Field display completeness for any property
- Deep link structure for any property
- Rate limiting for any request sequence
- Error handling for any failure scenario

### Property-Based Testing Configuration

**Library:** Use Hypothesis for Python property-based testing

**Configuration:**
- Minimum 100 iterations per property test
- Each test must reference its design document property
- Tag format: `# Feature: booking-verified-stays-integration, Property N: [property text]`

**Example Test Structure:**

```python
from hypothesis import given, strategies as st
import pytest

# Feature: booking-verified-stays-integration, Property 8: WordPress Storage Completeness
@given(
    hotel_id=st.text(min_size=1),
    name=st.text(min_size=1),
    latitude=st.floats(min_value=-90, max_value=90),
    longitude=st.floats(min_value=-180, max_value=180),
    price=st.floats(min_value=0, allow_nan=False, allow_infinity=False),
)
def test_wordpress_storage_completeness(hotel_id, name, latitude, longitude, price):
    """For any property data, all required ACF fields must be stored."""
    # Create property data
    property_data = AccommodationDetail(
        hotel_id=hotel_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        address="Test Address",
        city="Veria",
        country="Greece",
        min_price=price,
        currency="EUR",
        deep_link=f"https://booking.com/hotel/{hotel_id}"
    )
    
    # Sync to WordPress
    post_id = sync_service.sync_property(property_data)
    
    # Retrieve from WordPress
    post = wordpress_client.get_post(post_id)
    acf = post['acf']
    
    # Verify all required fields are present
    assert acf['booking_hotel_id'] == hotel_id
    assert acf['booking_name'] == name
    assert acf['booking_latitude'] == latitude
    assert acf['booking_longitude'] == longitude
    assert acf['booking_price_min'] == price
    assert acf['booking_currency'] == "EUR"
    assert 'booking_last_synced' in acf
```

### Test Coverage Requirements

**Minimum Coverage:**
- 90% code coverage for all new modules
- 100% coverage for critical paths (API client, sync service, validation)
- All 44 correctness properties must have property-based tests
- All edge cases must have unit tests

**Test Organization:**
```
frontend/app/tests/
├── test_booking_api.py           # API client tests
├── test_booking_sync.py          # Sync service tests
├── test_booking_cache.py         # Caching tests
├── test_booking_routes.py        # FastAPI route tests
├── test_booking_validation.py    # Pydantic model tests
├── test_rate_limiter.py          # Rate limiter tests
└── property_tests/
    ├── test_properties_api.py    # Properties 1-2, 26-27, 31-33, 39-44
    ├── test_properties_sync.py   # Properties 3-10
    ├── test_properties_cache.py  # Properties 11-14
    ├── test_properties_display.py # Properties 15-25
    └── test_properties_logging.py # Properties 28, 32-37
```

### Integration Testing

**Test Scenarios:**
1. End-to-end sync flow (API → WordPress → Cache)
2. User browsing flow (List → Detail → Deep Link)
3. Error recovery flow (API failure → Cache fallback)
4. Cache warming on startup
5. Rate limiting under load

**Test Environment:**
- Use Docker Compose for integration tests
- Mock Booking.com API with test fixtures
- Use test WordPress instance
- Use test Redis instance
- Isolate test data from production

### Performance Testing

**Benchmarks:**
- API response time < 200ms (with cache)
- Sync operation < 5 minutes for 100 properties
- List page render < 100ms
- Detail page render < 150ms
- Rate limiter overhead < 10ms per request

**Load Testing:**
- Simulate 100 concurrent users
- Test cache effectiveness under load
- Verify rate limiting prevents API overload
- Monitor memory usage during sync

## Configuration

### Environment Variables

```bash
# Booking.com API Configuration
BOOKING_API_KEY=your_api_key_here
BOOKING_AFFILIATE_ID=your_affiliate_id_here
BOOKING_API_BASE_URL=https://api.booking.com/v3

# Search Configuration
VERIA_LATITUDE=40.5246
VERIA_LONGITUDE=22.2022
BOOKING_SEARCH_RADIUS=10  # kilometers

# Rate Limiting
BOOKING_RATE_LIMIT=10  # requests per second

# Caching
BOOKING_CACHE_TTL=1800  # 30 minutes in seconds

# Sync Configuration
BOOKING_SYNC_ENABLED=true
BOOKING_SYNC_SCHEDULE="0 3 * * *"  # Daily at 3 AM (cron format)
BOOKING_SYNC_MAX_PROPERTIES=100

# Logging
BOOKING_LOG_LEVEL=INFO
BOOKING_LOG_API_REQUESTS=true
BOOKING_LOG_API_RESPONSES=false  # Set true for debugging

# WordPress Configuration (existing)
WP_API_URL=http://wordpress:80/wp-json
WP_ADMIN_USER=admin
WP_ADMIN_PASSWORD=admin_password
```

### Configuration Validation

On startup, the system must validate:
- BOOKING_API_KEY is set and non-empty
- BOOKING_AFFILIATE_ID is set and non-empty
- VERIA_LATITUDE is in range [-90, 90]
- VERIA_LONGITUDE is in range [-180, 180]
- BOOKING_SEARCH_RADIUS is positive integer
- BOOKING_RATE_LIMIT is positive integer
- BOOKING_CACHE_TTL is positive integer
- Redis connection is available
- WordPress API is accessible

If any validation fails, the system must:
1. Log clear error message indicating which configuration is invalid
2. Fail to start (raise exception)
3. Provide guidance on how to fix the configuration

## Deployment Considerations

### Docker Compose Updates

Add Booking.com configuration to `docker-compose.yml`:

```yaml
services:
  frontend:
    environment:
      - BOOKING_API_KEY=${BOOKING_API_KEY}
      - BOOKING_AFFILIATE_ID=${BOOKING_AFFILIATE_ID}
      - VERIA_LATITUDE=40.5246
      - VERIA_LONGITUDE=22.2022
      - BOOKING_SEARCH_RADIUS=10
      - BOOKING_RATE_LIMIT=10
      - BOOKING_CACHE_TTL=1800
      - BOOKING_SYNC_ENABLED=true
      - BOOKING_SYNC_SCHEDULE=0 3 * * *
```

### WordPress Setup

1. Install Custom Post Type UI plugin (if not already installed)
2. Create `verified_stay` custom post type via UI or code
3. Install Advanced Custom Fields plugin (if not already installed)
4. Import ACF field group from JSON export
5. Verify REST API access to verified_stay post type

### Initial Data Population

After deployment:
1. Verify configuration with `/admin/config-check` endpoint
2. Trigger initial sync with `/admin/sync-verified-stays` endpoint
3. Monitor sync progress in logs
4. Verify properties appear in WordPress admin
5. Test frontend display at `/verified-stays`
6. Verify cache warming on next restart

### Monitoring

**Key Metrics:**
- API request count and error rate
- Cache hit/miss ratio
- Sync success/failure rate
- Average response times
- Rate limiter queue depth

**Alerts:**
- Authentication failures
- Sync failures > 10%
- API error rate > 5%
- Cache unavailable
- Response time > 1 second

### Security Considerations

**API Credentials:**
- Store in environment variables, never in code
- Use secrets management in production (AWS Secrets Manager, etc.)
- Rotate credentials periodically
- Monitor for unauthorized access

**Data Sanitization:**
- Sanitize all text fields from API before storage
- Escape HTML in templates
- Validate all user inputs (filters, sort parameters)
- Use parameterized queries for database access

**Rate Limiting:**
- Enforce rate limits to prevent abuse
- Monitor for unusual traffic patterns
- Implement IP-based rate limiting for frontend endpoints
- Log rate limit violations

**Deep Links:**
- Validate affiliate ID format
- Ensure tracking parameters don't leak sensitive data
- Use HTTPS for all external links
- Implement link expiration if needed

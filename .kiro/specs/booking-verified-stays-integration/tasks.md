# Implementation Plan: Booking.com Verified Stays Integration

## Overview

This implementation plan breaks down the Booking.com Demand API integration into incremental coding tasks. Each task builds on previous work, starting with core infrastructure (API client, data models), then data synchronization, caching, frontend display, and finally testing and deployment configuration.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Add new dependencies to `frontend/requirements.txt`: `httpx>=0.24.0`, `hypothesis>=6.82.0` for async HTTP and property-based testing
  - Create directory structure: `frontend/app/api/booking.py`, `frontend/app/models/booking.py`, `frontend/app/services/booking_sync.py`, `frontend/app/utils/rate_limiter.py`, `frontend/app/utils/booking_cache.py`, `frontend/app/jobs/sync_booking.py`
  - Create template directories: `frontend/templates/verified_stays/` with `list.html` and `detail.html`
  - Update `frontend/app/config.py` with Booking.com configuration constants
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 2. Implement Pydantic data models for API validation
  - [ ] 2.1 Create `frontend/app/models/booking.py` with Pydantic models
    - Define `AccommodationSearchResult` model with validation for hotel_id, name, coordinates, pricing, ratings
    - Define `Facility` model for property amenities
    - Define `Photo` model for property images
    - Define `AccommodationDetail` model with all property fields
    - Define `SyncResult` model for sync operation statistics
    - Add field validators for coordinate ranges, non-negative numbers, required fields
    - _Requirements: 14.1, 14.3, 14.4, 14.5, 14.6_
  
  - [ ] 2.2 Write property test for coordinate validation
    - **Property 42: Coordinate Range Validation**
    - **Validates: Requirements 14.5**
  
  - [ ] 2.3 Write property test for required field validation
    - **Property 40: Required Field Validation**
    - **Validates: Requirements 14.3**
  
  - [ ] 2.4 Write property test for numeric field validation
    - **Property 41: Numeric Field Validation**
    - **Validates: Requirements 14.4**

- [ ] 3. Implement rate limiter utility
  - [ ] 3.1 Create `frontend/app/utils/rate_limiter.py` with token bucket algorithm
    - Implement `RateLimiter` class with configurable rate and time window
    - Implement `acquire()` async method that blocks until token available
    - Implement `_refill_tokens()` method for token replenishment
    - Add logging for rate limit events
    - _Requirements: 9.1, 9.2, 9.4, 9.5_
  
  - [ ] 3.2 Write property test for rate limiting enforcement
    - **Property 26: Rate Limiting Enforcement**
    - **Validates: Requirements 9.1, 9.2, 9.4**
  
  - [ ] 3.3 Write property test for rate limit event logging
    - **Property 27: Rate Limit Event Logging**
    - **Validates: Requirements 9.5**

- [ ] 4. Implement Booking.com API client
  - [ ] 4.1 Create `frontend/app/api/booking.py` with async HTTP client
    - Implement `BookingAPIClient` class with HTTPX async client
    - Implement `__init__` with API credentials, base URL, rate limiter initialization
    - Implement `search_accommodations()` method for property search by coordinates
    - Implement `get_accommodation_details()` method for detailed property info
    - Implement `_make_request()` private method with retry logic and exponential backoff
    - Add custom exceptions: `BookingAPIError`, `BookingAuthError`, `BookingRateLimitError`, `BookingNotFoundError`, `BookingValidationError`
    - Add request/response logging with timestamps and parameters
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 10.6, 11.1, 11.2_
  
  - [ ] 4.2 Write property test for API authentication headers
    - **Property 1: API Authentication Headers**
    - **Validates: Requirements 2.1**
  
  - [ ] 4.3 Write property test for date parameter inclusion
    - **Property 2: API Request Date Parameters**
    - **Validates: Requirements 2.6**
  
  - [ ] 4.4 Write property test for API request retry logic
    - **Property 31: API Request Retry Logic**
    - **Validates: Requirements 10.6**
  
  - [ ] 4.5 Write unit tests for API client
    - Test search endpoint with mock responses
    - Test details endpoint with mock responses
    - Test authentication failure handling
    - Test rate limit error handling
    - Test network timeout handling
    - _Requirements: 2.1, 2.4, 2.5, 10.1, 10.4_

- [ ] 5. Implement caching layer for Booking.com data
  - [ ] 5.1 Create `frontend/app/utils/booking_cache.py` with Redis caching functions
    - Implement `cache_search_results()` function with 30-minute TTL
    - Implement `get_cached_search_results()` function
    - Implement `cache_property_detail()` function with 30-minute TTL
    - Implement `get_cached_property_detail()` function
    - Implement `invalidate_verified_stays_cache()` function to clear all booking caches
    - Use cache key prefix "veriaguide:booking:" for all keys
    - Add cache hit/miss logging
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 11.5_
  
  - [ ] 5.2 Write property test for API response caching
    - **Property 11: API Response Caching**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ] 5.3 Write property test for cache key prefix convention
    - **Property 12: Cache Key Prefix Convention**
    - **Validates: Requirements 5.3**
  
  - [ ] 5.4 Write property test for cache hit behavior
    - **Property 13: Cache Hit Behavior**
    - **Validates: Requirements 5.4**

- [ ] 6. Extend WordPress client for verified_stay operations
  - [ ] 6.1 Add verified_stay methods to `frontend/app/api/wordpress.py`
    - Implement `get_verified_stay_by_booking_id()` to find posts by booking_hotel_id ACF field
    - Implement `create_verified_stay()` to create new posts with ACF fields
    - Implement `update_verified_stay()` to update existing post ACF fields
    - Implement `get_verified_stays()` with pagination, filtering (price, rating, facilities), and sorting
    - Add helper method `_transform_filters_to_wp_query()` for filter translation
    - _Requirements: 4.1, 4.2, 4.3, 6.4, 6.5, 6.7_
  
  - [ ] 6.2 Write unit tests for WordPress client extensions
    - Test finding posts by booking_hotel_id
    - Test creating new verified_stay posts
    - Test updating existing posts
    - Test pagination logic
    - Test filter translation
    - _Requirements: 4.1, 4.2, 4.3_

- [ ] 7. Implement Booking.com sync service
  - [ ] 7.1 Create `frontend/app/services/booking_sync.py` with sync logic
    - Implement `BookingSyncService` class with API and WordPress clients
    - Implement `sync_all_properties()` method to sync all properties in radius
    - Implement `sync_property()` method to sync single property by hotel_id
    - Implement `_create_or_update_post()` private method for WordPress operations
    - Implement `_transform_to_acf_fields()` to convert API data to ACF format
    - Add error handling to continue on individual property failures
    - Add sync statistics tracking (created, updated, failed counts)
    - Add comprehensive logging for sync operations
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.4, 4.5, 4.6, 4.7, 4.8, 11.3_
  
  - [ ] 7.2 Write property test for sync updates existing properties
    - **Property 3: Sync Updates Existing Properties**
    - **Validates: Requirements 3.3**
  
  - [ ] 7.3 Write property test for sync creates new properties
    - **Property 4: Sync Creates New Properties**
    - **Validates: Requirements 3.4**
  
  - [ ] 7.4 Write property test for sync timestamp recording
    - **Property 5: Sync Timestamp Recording**
    - **Validates: Requirements 3.5**
  
  - [ ] 7.5 Write property test for sync error isolation
    - **Property 6: Sync Error Isolation**
    - **Validates: Requirements 3.6**
  
  - [ ] 7.6 Write property test for WordPress storage completeness
    - **Property 8: WordPress Storage Completeness**
    - **Validates: Requirements 4.1, 4.4, 4.5, 4.6, 4.7**
  
  - [ ] 7.7 Write property test for unique hotel ID constraint
    - **Property 9: Unique Hotel ID Constraint**
    - **Validates: Requirements 4.2, 4.3**
  
  - [ ] 7.8 Write property test for facility data structure
    - **Property 10: Facility Data Structure**
    - **Validates: Requirements 4.8**

- [ ] 8. Checkpoint - Ensure core infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement FastAPI routes for verified stays
  - [ ] 9.1 Add verified stays routes to `frontend/main.py`
    - Implement `GET /verified-stays` route for list view with pagination
    - Add query parameters: page, price_min, price_max, min_rating, facilities, sort
    - Implement filtering logic for price range, rating, facilities
    - Implement sorting logic: price_asc, price_desc, rating_desc, distance_asc
    - Calculate distance from Veria center for each property
    - Implement `GET /verified-stays/{slug}` route for detail view
    - Implement `POST /admin/sync-verified-stays` route for manual sync trigger (requires API key)
    - Add cache integration for both list and detail views
    - Add error handling with fallback to cached/WordPress data
    - _Requirements: 1.2, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 10.2, 10.3, 10.5_
  
  - [ ] 9.2 Write property test for filter correctness
    - **Property 16: Filter Correctness**
    - **Validates: Requirements 6.4**
  
  - [ ] 9.3 Write property test for sort order correctness
    - **Property 17: Sort Order Correctness**
    - **Validates: Requirements 6.5**
  
  - [ ] 9.4 Write property test for pagination consistency
    - **Property 18: Pagination Consistency**
    - **Validates: Requirements 6.7**
  
  - [ ] 9.5 Write property test for distance calculation presence
    - **Property 19: Distance Calculation Presence**
    - **Validates: Requirements 6.8**
  
  - [ ] 9.6 Write unit tests for route handlers
    - Test list view with various filter combinations
    - Test detail view with valid and invalid slugs
    - Test empty results handling
    - Test API failure fallback to cache
    - Test API failure fallback to WordPress
    - _Requirements: 6.1, 6.6, 7.1, 10.2, 10.3, 10.5_

- [ ] 10. Create Jinja2 templates for verified stays
  - [ ] 10.1 Create `frontend/templates/verified_stays/list.html`
    - Extend base template with verified stays list layout
    - Display property cards with thumbnail, name, price, currency, rating, review score, review count
    - Add filter form for price range, minimum rating, facilities
    - Add sort dropdown for price and rating options
    - Add pagination controls
    - Display distance from Veria center for each property
    - Show helpful message when no results match filters
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.8_
  
  - [ ] 10.2 Create `frontend/templates/verified_stays/detail.html`
    - Extend base template with property detail layout
    - Display property name, full address, description
    - Display photo gallery with all property images
    - Display price, currency, rating, review score, review count
    - Display all facilities with icons in organized sections
    - Add prominent "Book Now" button with deep link (target="_blank")
    - Display last synchronization timestamp
    - Embed interactive map with property location marker
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_
  
  - [ ] 10.3 Write property test for list view field display
    - **Property 15: List View Field Display**
    - **Validates: Requirements 6.2, 6.3**
  
  - [ ] 10.4 Write property test for detail view field completeness
    - **Property 20: Detail View Field Completeness**
    - **Validates: Requirements 7.2, 7.4, 7.5, 7.8**
  
  - [ ] 10.5 Write property test for photo gallery completeness
    - **Property 21: Photo Gallery Completeness**
    - **Validates: Requirements 7.3**
  
  - [ ] 10.6 Write property test for facility list completeness
    - **Property 22: Facility List Completeness**
    - **Validates: Requirements 7.6**
  
  - [ ] 10.7 Write property test for deep link presence
    - **Property 23: Deep Link Presence**
    - **Validates: Requirements 7.7**

- [ ] 11. Implement deep link generation
  - [ ] 11.1 Add deep link utility to `frontend/app/utils/helpers.py`
    - Implement `generate_booking_deep_link()` function
    - Include affiliate ID in URL parameters
    - Include hotel ID in URL path or parameters
    - Include check-in and check-out dates when provided
    - Include tracking parameters for attribution
    - Return properly encoded URL
    - _Requirements: 8.1, 8.2, 8.3, 8.5_
  
  - [ ] 11.2 Write property test for deep link structure
    - **Property 24: Deep Link Structure**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.5**
  
  - [ ] 11.3 Write property test for deep link target attribute
    - **Property 25: Deep Link Target Attribute**
    - **Validates: Requirements 8.4**
  
  - [ ] 11.4 Write unit tests for deep link generation
    - Test link with all parameters
    - Test link without dates
    - Test URL encoding of special characters
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [ ] 12. Implement background sync job
  - [ ] 12.1 Create `frontend/app/jobs/sync_booking.py` with scheduled sync
    - Implement `run_daily_sync()` async function
    - Read Veria coordinates and radius from configuration
    - Initialize Booking API client and sync service
    - Call `sync_all_properties()` and log results
    - Invalidate verified stays caches after successful sync
    - Add error handling and administrator alerts for failures
    - _Requirements: 3.1, 3.2, 5.7, 10.1, 10.4_
  
  - [ ] 12.2 Add APScheduler integration to `frontend/main.py`
    - Add `apscheduler>=3.10.0` to requirements.txt
    - Configure scheduler with cron trigger from environment variable
    - Register `run_daily_sync()` job
    - Start scheduler on application startup
    - _Requirements: 3.1_
  
  - [ ] 12.3 Write property test for cache invalidation on sync
    - **Property 14: Cache Invalidation on Sync**
    - **Validates: Requirements 5.7**
  
  - [ ] 12.4 Write unit test for sync job execution
    - Test sync job runs successfully
    - Test sync job handles API failures
    - Test sync job logs statistics
    - _Requirements: 3.1, 3.2, 11.3_

- [ ] 13. Add navigation menu integration
  - [ ] 13.1 Update base template navigation
    - Add "Verified Stays" menu item linking to `/verified-stays`
    - Ensure "Accommodations" menu item remains unchanged
    - Add appropriate icons for both menu items
    - _Requirements: 1.3, 1.5_
  
  - [ ] 13.2 Write unit test for navigation menu
    - Test both menu items are present in rendered HTML
    - Test links point to correct URLs
    - _Requirements: 1.3, 1.5_

- [ ] 14. Implement configuration validation
  - [ ] 14.1 Add configuration validation to `frontend/app/config.py`
    - Define required Booking.com configuration variables
    - Implement `validate_booking_config()` function
    - Validate API key and affiliate ID are non-empty
    - Validate coordinate ranges for latitude and longitude
    - Validate positive integers for radius, rate limit, cache TTL
    - Validate Redis connection availability
    - Validate WordPress API accessibility
    - Raise clear exceptions with guidance for invalid configuration
    - _Requirements: 12.6, 12.7_
  
  - [ ] 14.2 Call validation on application startup in `frontend/main.py`
    - Add startup event handler
    - Call `validate_booking_config()` before starting server
    - Log validation success or failure
    - _Requirements: 12.6, 12.7_
  
  - [ ] 14.3 Write property test for configuration validation
    - **Property 38: Configuration Validation on Startup**
    - **Validates: Requirements 12.6, 12.7**
  
  - [ ] 14.4 Write unit tests for configuration validation
    - Test validation passes with valid config
    - Test validation fails with missing API key
    - Test validation fails with invalid coordinates
    - Test validation fails with negative rate limit
    - _Requirements: 12.6, 12.7_

- [ ] 15. Checkpoint - Ensure all application tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement comprehensive logging
  - [ ] 16.1 Configure structured logging in `frontend/app/config.py`
    - Set up Python logging with JSON formatter
    - Configure log levels from environment variable
    - Add request ID middleware for request tracing
    - _Requirements: 11.7_
  
  - [ ] 16.2 Add logging throughout the application
    - Add API request/response logging to `booking.py`
    - Add sync operation logging to `booking_sync.py`
    - Add cache operation logging to `booking_cache.py`
    - Add rate limit event logging to `rate_limiter.py`
    - Add error logging with stack traces to all exception handlers
    - Ensure all logs include severity levels (DEBUG, INFO, WARNING, ERROR)
    - _Requirements: 10.1, 11.1, 11.2, 11.3, 11.5, 11.6, 11.7_
  
  - [ ] 16.3 Write property test for API error logging
    - **Property 28: API Error Logging**
    - **Validates: Requirements 10.1**
  
  - [ ] 16.4 Write property test for API request logging
    - **Property 32: API Request Logging**
    - **Validates: Requirements 11.1**
  
  - [ ] 16.5 Write property test for API response logging
    - **Property 33: API Response Logging**
    - **Validates: Requirements 11.2**
  
  - [ ] 16.6 Write property test for sync operation logging
    - **Property 34: Sync Operation Logging**
    - **Validates: Requirements 11.3**
  
  - [ ] 16.7 Write property test for cache operation logging
    - **Property 35: Cache Operation Logging**
    - **Validates: Requirements 11.5**
  
  - [ ] 16.8 Write property test for error stack trace logging
    - **Property 36: Error Stack Trace Logging**
    - **Validates: Requirements 11.6**
  
  - [ ] 16.9 Write property test for structured log format
    - **Property 37: Structured Log Format**
    - **Validates: Requirements 11.7**

- [ ] 17. Implement error handling and fallbacks
  - [ ] 17.1 Add error handling to API client
    - Implement retry logic with exponential backoff (already in task 4.1)
    - Add specific exception handling for auth, rate limit, not found errors
    - Log all errors with full context
    - _Requirements: 10.1, 10.4, 10.6_
  
  - [ ] 17.2 Add fallback logic to route handlers
    - Implement cache fallback when API is unavailable
    - Implement WordPress fallback when both API and cache fail
    - Display user-friendly error messages for complete failures
    - _Requirements: 10.2, 10.3, 10.5_
  
  - [ ] 17.3 Write property test for API failure fallback to cache
    - **Property 29: API Failure Fallback to Cache**
    - **Validates: Requirements 10.2**
  
  - [ ] 17.4 Write property test for detail request fallback to WordPress
    - **Property 30: Detail Request Fallback to WordPress**
    - **Validates: Requirements 10.5**
  
  - [ ] 17.5 Write unit tests for error scenarios
    - Test authentication failure handling
    - Test rate limit error handling
    - Test network timeout handling
    - Test empty cache fallback
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 18. Implement text sanitization for security
  - [ ] 18.1 Add sanitization utility to `frontend/app/utils/helpers.py`
    - Implement `sanitize_text()` function for HTML escaping
    - Implement `sanitize_url()` function for URL validation
    - Apply sanitization to all API text fields before storage
    - Apply sanitization in templates for display
    - _Requirements: 14.7_
  
  - [ ] 18.2 Write property test for text field sanitization
    - **Property 44: Text Field Sanitization**
    - **Validates: Requirements 14.7**
  
  - [ ] 18.3 Write unit tests for sanitization
    - Test HTML tag removal
    - Test script tag removal
    - Test SQL injection prevention
    - Test XSS prevention
    - _Requirements: 14.7_

- [ ] 19. Create WordPress configuration files
  - [ ] 19.1 Create ACF field group JSON export
    - Create `acf-verified-stays-export.json` with all booking ACF fields
    - Include field definitions for: booking_hotel_id, booking_name, booking_address, booking_latitude, booking_longitude, booking_price_min, booking_currency, booking_rating, booking_review_score, booking_review_count
    - Include repeater field for booking_facilities with name and icon subfields
    - Include gallery field for booking_photos
    - Include URL field for booking_deep_link
    - Include datetime picker for booking_last_synced
    - Set location rules to verified_stay post type
    - _Requirements: 1.4, 4.5, 4.6, 4.7, 4.8_
  
  - [ ] 19.2 Create WordPress setup documentation
    - Document Custom Post Type UI configuration for verified_stay
    - Document ACF field group import process
    - Document REST API verification steps
    - Add to project README or separate WORDPRESS_SETUP.md
    - _Requirements: 1.1, 1.4_

- [ ] 20. Update Docker Compose configuration
  - [ ] 20.1 Add Booking.com environment variables to `docker-compose.yml`
    - Add BOOKING_API_KEY, BOOKING_AFFILIATE_ID, BOOKING_API_BASE_URL
    - Add VERIA_LATITUDE=40.5246, VERIA_LONGITUDE=22.2022, BOOKING_SEARCH_RADIUS=10
    - Add BOOKING_RATE_LIMIT=10, BOOKING_CACHE_TTL=1800
    - Add BOOKING_SYNC_ENABLED=true, BOOKING_SYNC_SCHEDULE="0 3 * * *"
    - Add BOOKING_LOG_LEVEL=INFO, BOOKING_LOG_API_REQUESTS=true
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 20.2 Create `.env.example` file
    - Document all required Booking.com environment variables
    - Provide example values and descriptions
    - Include security notes for API credentials
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 21. Create integration tests
  - [ ] 21.1 Write end-to-end sync flow test
    - Test complete flow: API → WordPress → Cache
    - Use mock Booking.com API responses
    - Verify data in WordPress and cache
    - _Requirements: 3.2, 3.3, 3.4, 4.1, 5.1_
  
  - [ ] 21.2 Write end-to-end browsing flow test
    - Test complete flow: List → Detail → Deep Link
    - Verify all data displays correctly
    - Verify filters and sorting work
    - _Requirements: 6.1, 6.4, 6.5, 7.1, 8.1_
  
  - [ ] 21.3 Write cache warming test
    - Test cache warming on application startup
    - Verify verified stays are cached
    - Measure cache warming performance
    - _Requirements: 5.1, 5.6_

- [ ] 22. Create deployment documentation
  - [ ] 22.1 Create `docs/BOOKING_VERIFIED_STAYS_SETUP.md`
    - Document WordPress setup steps (Custom Post Type UI, ACF import)
    - Document environment variable configuration
    - Document initial sync process
    - Document monitoring and alerting setup
    - Document security considerations
    - Document troubleshooting common issues
    - _Requirements: 1.1, 1.4, 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 22.2 Update main README.md
    - Add Verified Stays section to features list
    - Add Booking.com API configuration to setup instructions
    - Add link to detailed setup documentation
    - _Requirements: 1.2, 12.1_

- [ ] 23. Final checkpoint - Complete system verification
  - Run full test suite (unit tests and property tests)
  - Verify all 44 correctness properties pass
  - Test manual sync trigger via admin endpoint
  - Verify list and detail pages render correctly
  - Verify deep links work and include affiliate ID
  - Verify caching reduces API calls
  - Verify rate limiting prevents API overload
  - Verify error handling and fallbacks work
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples, edge cases, and integration points
- All 44 correctness properties have corresponding property-based tests
- The implementation follows VeriaGuide's existing architecture patterns
- All async operations use HTTPX and FastAPI async handlers
- All caching uses Redis with "veriaguide:booking:" prefix
- All configuration comes from environment variables
- All errors are logged with structured logging and severity levels

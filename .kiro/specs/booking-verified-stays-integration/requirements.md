# Requirements Document

## Introduction

This document specifies the requirements for integrating Booking.com Demand API into VeriaGuide to provide verified accommodation listings with real-time pricing and availability. The integration creates a new "Verified Stays" category separate from the existing accommodations directory, populated with data from Booking.com's API.

## Glossary

- **Verified_Stays_System**: The complete integration system including API client, data synchronization, caching, and display components
- **Booking_API**: Booking.com Demand API v3+ for retrieving accommodation data
- **WordPress_Backend**: Headless WordPress CMS storing verified stay data as custom post types
- **FastAPI_Frontend**: Python web application serving user-facing pages
- **Redis_Cache**: In-memory cache for API responses and processed data
- **Sync_Job**: Scheduled task that fetches and updates Booking.com data
- **Deep_Link**: Affiliate URL directing users to Booking.com for reservations
- **ACF_Fields**: Advanced Custom Fields storing structured Booking.com data
- **Search_Radius**: Geographic area around Veria coordinates (10km) for property search
- **Rate_Limiter**: Component enforcing API request limits per Booking.com terms

## Requirements

### Requirement 1: New Content Category

**User Story:** As a VeriaGuide administrator, I want a separate "Verified Stays" category for Booking.com properties, so that I can distinguish API-sourced accommodations from manually curated ones.

#### Acceptance Criteria

1. THE WordPress_Backend SHALL create a custom post type named "verified_stay"
2. THE FastAPI_Frontend SHALL serve verified stays at the URL path "/verified-stays"
3. THE Verified_Stays_System SHALL maintain the existing "accommodations" category unchanged
4. THE WordPress_Backend SHALL register ACF field groups specific to verified_stay post type
5. THE FastAPI_Frontend SHALL provide separate navigation menu items for "Verified Stays" and "Accommodations"

### Requirement 2: Booking.com API Integration

**User Story:** As a developer, I want to integrate with Booking.com Demand API, so that I can retrieve real-time accommodation data for Veria.

#### Acceptance Criteria

1. THE Booking_API SHALL authenticate using Bearer token and Affiliate ID credentials
2. WHEN searching for properties, THE Booking_API SHALL use Veria coordinates (latitude 40.5246, longitude 22.2022)
3. THE Booking_API SHALL search within a 10km radius from Veria center
4. THE Booking_API SHALL use the /accommodations/search endpoint for property discovery
5. THE Booking_API SHALL use the /accommodations/details endpoint for detailed property information
6. THE Booking_API SHALL include check-in and check-out dates in search requests
7. THE Booking_API SHALL request pricing in EUR currency
8. THE Booking_API SHALL handle API version 3.0 or higher

### Requirement 3: Data Synchronization

**User Story:** As a system administrator, I want automated daily synchronization of Booking.com data, so that property information remains current without manual intervention.

#### Acceptance Criteria

1. THE Sync_Job SHALL execute daily at a configured time
2. WHEN synchronizing, THE Sync_Job SHALL fetch all properties within the search radius
3. WHEN a property exists in WordPress, THE Sync_Job SHALL update its data
4. WHEN a property is new, THE Sync_Job SHALL create a new verified_stay post
5. THE Sync_Job SHALL store the last synchronization timestamp in each post
6. WHEN synchronization fails, THE Sync_Job SHALL log errors and continue with remaining properties
7. THE Sync_Job SHALL update a maximum of 100 properties per execution to respect rate limits
8. WHEN a property is no longer available in API results, THE Sync_Job SHALL mark it as inactive

### Requirement 4: WordPress Data Storage

**User Story:** As a content manager, I want Booking.com data stored in WordPress, so that I can view and manage properties through the familiar WordPress interface.

#### Acceptance Criteria

1. THE WordPress_Backend SHALL store each Booking.com property as a verified_stay post
2. THE WordPress_Backend SHALL use booking_hotel_id as the unique identifier
3. THE WordPress_Backend SHALL prevent duplicate posts for the same booking_hotel_id
4. THE WordPress_Backend SHALL store all property data in ACF fields
5. THE ACF_Fields SHALL include: booking_hotel_id, booking_name, booking_address, booking_latitude, booking_longitude
6. THE ACF_Fields SHALL include: booking_price_min, booking_currency, booking_rating, booking_review_score, booking_review_count
7. THE ACF_Fields SHALL include: booking_facilities (repeater field), booking_photos (gallery field), booking_deep_link, booking_last_synced
8. THE WordPress_Backend SHALL store facility data as a repeater field with name and icon subfields

### Requirement 5: Redis Caching

**User Story:** As a system operator, I want API responses cached in Redis, so that the application responds quickly and reduces API calls.

#### Acceptance Criteria

1. THE Redis_Cache SHALL cache Booking_API search responses for 30 minutes
2. THE Redis_Cache SHALL cache Booking_API detail responses for 30 minutes
3. THE Redis_Cache SHALL use cache keys prefixed with "veriaguide:booking:"
4. WHEN cache data exists and is valid, THE Verified_Stays_System SHALL return cached data without API calls
5. WHEN cache data expires, THE Verified_Stays_System SHALL fetch fresh data from Booking_API
6. THE Redis_Cache SHALL cache processed property lists for list view rendering
7. THE Redis_Cache SHALL invalidate relevant caches when Sync_Job updates data

### Requirement 6: List View Display

**User Story:** As a tourist, I want to browse verified stays with pricing and ratings, so that I can compare accommodation options in Veria.

#### Acceptance Criteria

1. THE FastAPI_Frontend SHALL display a list of verified stays at /verified-stays
2. WHEN displaying properties, THE FastAPI_Frontend SHALL show property name, thumbnail image, minimum price, currency, and rating
3. THE FastAPI_Frontend SHALL display review scores and review counts
4. THE FastAPI_Frontend SHALL provide filters for price range, minimum rating, and facilities
5. THE FastAPI_Frontend SHALL provide sorting options: price (low to high), price (high to low), rating (high to low), distance from center
6. WHEN no properties match filters, THE FastAPI_Frontend SHALL display a helpful message
7. THE FastAPI_Frontend SHALL paginate results with 20 properties per page
8. THE FastAPI_Frontend SHALL display property distance from Veria center

### Requirement 7: Detail View Display

**User Story:** As a tourist, I want to view complete property information, so that I can make informed booking decisions.

#### Acceptance Criteria

1. THE FastAPI_Frontend SHALL display detailed property information at /verified-stays/{slug}
2. THE FastAPI_Frontend SHALL show property name, full address, description, and location map
3. THE FastAPI_Frontend SHALL display all property photos in a gallery
4. THE FastAPI_Frontend SHALL show current minimum price with currency
5. THE FastAPI_Frontend SHALL display rating, review score, and review count
6. THE FastAPI_Frontend SHALL list all available facilities with icons
7. THE FastAPI_Frontend SHALL provide a prominent "Book Now" button with Deep_Link to Booking.com
8. THE FastAPI_Frontend SHALL display the last synchronization timestamp
9. THE FastAPI_Frontend SHALL show property location on an interactive map

### Requirement 8: Booking.com Deep Links

**User Story:** As a VeriaGuide operator, I want affiliate deep links to Booking.com, so that users can complete bookings and I can earn referral revenue.

#### Acceptance Criteria

1. THE Verified_Stays_System SHALL generate Deep_Link URLs including the affiliate ID
2. THE Deep_Link SHALL direct users to the specific property page on Booking.com
3. THE Deep_Link SHALL preserve check-in and check-out dates when available
4. THE Deep_Link SHALL open in a new browser tab when clicked
5. THE Deep_Link SHALL include tracking parameters for attribution

### Requirement 9: API Rate Limiting

**User Story:** As a system administrator, I want API rate limiting enforced, so that the application complies with Booking.com terms of service.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a maximum of 10 requests per second to Booking_API
2. WHEN rate limit is approached, THE Rate_Limiter SHALL delay requests to stay within limits
3. THE Rate_Limiter SHALL track request counts per time window
4. WHEN rate limit is exceeded, THE Rate_Limiter SHALL queue requests for later execution
5. THE Rate_Limiter SHALL log rate limit events for monitoring

### Requirement 10: Error Handling

**User Story:** As a user, I want the application to handle API errors gracefully, so that I can still browse available information when external services fail.

#### Acceptance Criteria

1. WHEN Booking_API returns an error, THE Verified_Stays_System SHALL log the error with full context
2. WHEN Booking_API is unavailable, THE FastAPI_Frontend SHALL display cached data if available
3. WHEN no cached data exists, THE FastAPI_Frontend SHALL display a user-friendly error message
4. WHEN authentication fails, THE Verified_Stays_System SHALL alert administrators
5. WHEN a property detail request fails, THE FastAPI_Frontend SHALL show basic information from WordPress
6. THE Verified_Stays_System SHALL retry failed API requests up to 3 times with exponential backoff
7. WHEN Sync_Job encounters errors, THE Sync_Job SHALL continue processing remaining properties

### Requirement 11: Logging and Monitoring

**User Story:** As a system administrator, I want comprehensive logging, so that I can troubleshoot issues and monitor system health.

#### Acceptance Criteria

1. THE Verified_Stays_System SHALL log all Booking_API requests with timestamps and parameters
2. THE Verified_Stays_System SHALL log all Booking_API responses with status codes
3. THE Sync_Job SHALL log synchronization start, completion, and statistics (properties updated, created, failed)
4. THE Rate_Limiter SHALL log rate limiting events
5. THE Verified_Stays_System SHALL log cache hits and misses for performance monitoring
6. THE Verified_Stays_System SHALL log all errors with stack traces
7. THE Verified_Stays_System SHALL use structured logging with severity levels (DEBUG, INFO, WARNING, ERROR)

### Requirement 12: Configuration Management

**User Story:** As a developer, I want externalized configuration, so that I can deploy the application across different environments without code changes.

#### Acceptance Criteria

1. THE Verified_Stays_System SHALL read Booking.com API credentials from environment variables
2. THE Verified_Stays_System SHALL read search coordinates and radius from configuration
3. THE Verified_Stays_System SHALL read cache TTL values from configuration
4. THE Verified_Stays_System SHALL read rate limit values from configuration
5. THE Verified_Stays_System SHALL read sync schedule from configuration
6. THE Verified_Stays_System SHALL validate all required configuration on startup
7. WHEN required configuration is missing, THE Verified_Stays_System SHALL fail startup with clear error messages

### Requirement 13: Async API Operations

**User Story:** As a developer, I want asynchronous API calls, so that the application remains responsive during external API operations.

#### Acceptance Criteria

1. THE Booking_API SHALL use async HTTP client (HTTPX) for all API requests
2. THE Booking_API SHALL support concurrent requests for multiple properties
3. WHEN fetching property details, THE Booking_API SHALL process up to 5 requests concurrently
4. THE FastAPI_Frontend SHALL use async route handlers for all verified stays endpoints
5. THE Sync_Job SHALL use async operations for API calls and database updates

### Requirement 14: Data Validation

**User Story:** As a developer, I want API response validation, so that the application handles unexpected data formats safely.

#### Acceptance Criteria

1. THE Booking_API SHALL validate all API responses against Pydantic models
2. WHEN API response is invalid, THE Booking_API SHALL log validation errors and raise exceptions
3. THE Booking_API SHALL validate required fields: hotel_id, name, latitude, longitude
4. THE Booking_API SHALL validate numeric fields: price, rating, review_score, review_count
5. THE Booking_API SHALL validate coordinate ranges: latitude (-90 to 90), longitude (-180 to 180)
6. WHEN optional fields are missing, THE Booking_API SHALL use sensible defaults
7. THE Booking_API SHALL sanitize text fields to prevent injection attacks

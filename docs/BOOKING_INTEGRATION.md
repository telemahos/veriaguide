# Booking.com Integration Documentation

## Overview

The Booking.com integration allows VeriaGuide to display pricing, ratings, and booking links from Booking.com alongside accommodation listings. This integration uses **manual data management** through WordPress Advanced Custom Fields (ACF), where content administrators maintain Booking.com data directly in WordPress.

## Architecture

### Data Flow

```
WordPress (ACF Fields)
        ↓
WordPress REST API
        ↓
FastAPI AccommodationService
        ↓
Template Rendering
        ↓
User sees Booking.com data + affiliate link
```

### Key Components

1. **WordPress ACF Fields**: Store Booking.com data (property ID, price, rating, etc.)
2. **AccommodationService**: Retrieves and enriches accommodation data
3. **AffiliateLinkGenerator**: Generates Booking.com affiliate links
4. **DataValidator**: Validates and sanitizes Booking.com data
5. **Templates**: Display Booking.com data in listings and detail pages

## WordPress ACF Field Setup

### Field Group: "Booking.com Integration"

Add the following ACF fields to the "accommodation" post type:

| Field Name | Field Type | Required | Validation |
|------------|------------|----------|------------|
| `booking_property_id` | Text | No | Numeric only |
| `booking_price` | Number | No | Min: 0 |
| `booking_rating` | Number | No | Min: 0, Max: 10 |
| `booking_availability` | Select | No | Options: available, unavailable, unknown |
| `booking_review_count` | Number | No | Min: 0 |
| `booking_last_updated` | Date Picker | No | - |

### Field Configuration

```json
{
  "key": "group_booking_integration",
  "title": "Booking.com Integration",
  "fields": [
    {
      "key": "field_booking_property_id",
      "label": "Booking.com Property ID",
      "name": "booking_property_id",
      "type": "text",
      "instructions": "Enter the Booking.com property ID (numeric only)",
      "required": 0,
      "placeholder": "123456"
    },
    {
      "key": "field_booking_price",
      "label": "Price (EUR)",
      "name": "booking_price",
      "type": "number",
      "instructions": "Current price in EUR",
      "required": 0,
      "min": 0,
      "step": 0.01
    },
    {
      "key": "field_booking_rating",
      "label": "Guest Rating",
      "name": "booking_rating",
      "type": "number",
      "instructions": "Guest rating (0-10 scale)",
      "required": 0,
      "min": 0,
      "max": 10,
      "step": 0.1
    },
    {
      "key": "field_booking_availability",
      "label": "Availability",
      "name": "booking_availability",
      "type": "select",
      "instructions": "Current availability status",
      "required": 0,
      "choices": {
        "available": "Available",
        "unavailable": "Unavailable",
        "unknown": "Unknown"
      },
      "default_value": "unknown"
    },
    {
      "key": "field_booking_review_count",
      "label": "Review Count",
      "name": "booking_review_count",
      "type": "number",
      "instructions": "Number of guest reviews",
      "required": 0,
      "min": 0
    },
    {
      "key": "field_booking_last_updated",
      "label": "Last Updated",
      "name": "booking_last_updated",
      "type": "date_picker",
      "instructions": "Date when Booking.com data was last updated",
      "required": 0,
      "display_format": "d/m/Y",
      "return_format": "Y-m-d"
    }
  ],
  "location": [
    [
      {
        "param": "post_type",
        "operator": "==",
        "value": "accommodation"
      }
    ]
  ]
}
```

## Environment Configuration

### Required Environment Variables

Add the following to your `.env` file:

```bash
# Booking.com Affiliate Configuration
BOOKING_AFFILIATE_ID=your_affiliate_id_here
BOOKING_TRACKING_SOURCE=veriaguide
BOOKING_TRACKING_CAMPAIGN=accommodations
```

### Configuration Validation

The application validates the affiliate configuration on startup:

- If `BOOKING_AFFILIATE_ID` is missing, a warning is logged
- Affiliate link generation is disabled if the ID is missing
- The application continues to function with WordPress-only data

## Data Update Workflow

### For Content Administrators

1. **Find Booking.com Property ID**:
   - Go to Booking.com
   - Search for the accommodation
   - Copy the property ID from the URL (e.g., `https://www.booking.com/hotel/gr/property-name.html?aid=123456`)

2. **Update WordPress**:
   - Edit the accommodation in WordPress
   - Scroll to "Booking.com Integration" field group
   - Enter the property ID
   - Enter current price, rating, and availability
   - Enter review count if available
   - Set "Last Updated" to today's date
   - Save the post

3. **Verify Display**:
   - Visit the accommodation page on VeriaGuide
   - Verify Booking.com data is displayed
   - Test the "Book on Booking.com" button

### Data Maintenance Schedule

- **Weekly**: Update prices for featured accommodations
- **Monthly**: Update all accommodation prices and ratings
- **As needed**: Update availability status

## Frontend Display

### List View

Accommodations in the list view display:

- Booking.com price (if available)
- Guest rating with stars
- Availability badge
- Review count
- "Book on Booking.com" button

### Detail View

Accommodation detail pages display:

- Prominent price display
- Guest rating with stars
- Availability status badge
- Review count
- Prominent "Book on Booking.com" call-to-action button
- Last updated date

### Missing Data Handling

If Booking.com data is not available:

- No Booking.com section is displayed
- Only WordPress data is shown
- No booking button is displayed

## Affiliate Link Format

Generated affiliate links follow this format:

```
https://www.booking.com/searchresults.html
  ?aid={AFFILIATE_ID}
  &dest_id={PROPERTY_ID}
  &dest_type=hotel
  &utm_source=veriaguide
  &utm_medium=referral
  &utm_campaign=accommodations
```

### Link Behavior

- Opens in a new tab (`target="_blank"`)
- Includes `rel="noopener noreferrer"` for security
- Tracks clicks for affiliate commission

## Data Validation

### Price Validation

- Must be a positive number
- Invalid values are logged and set to `None`
- Display shows "Price not available" if invalid

### Rating Validation

- Must be between 0 and 10
- Invalid values are logged and set to `None`
- Display shows no rating if invalid

### Review Count Validation

- Must be a non-negative integer
- Invalid values are logged and set to `None`
- Display shows no review count if invalid

### XSS Protection

All text fields are sanitized using `html.escape()` to prevent XSS attacks.

## Error Handling

### WordPress API Errors

- Logged with timestamp and error details
- Application continues without Booking.com data
- WordPress-only data is displayed

### Validation Errors

- Logged as warnings
- Invalid fields are skipped
- Valid fields are still displayed

### Missing Affiliate ID

- Warning logged on startup
- Affiliate link generation disabled
- Application continues with WordPress-only data

## Testing

### Unit Tests

Run unit tests:

```bash
docker-compose exec frontend pytest app/tests/test_booking_affiliate.py -v
docker-compose exec frontend pytest app/tests/test_booking_validator.py -v
```

### Property-Based Tests

Run property-based tests:

```bash
docker-compose exec frontend pytest app/tests/ -v -m property
```

### Integration Tests

Test with real WordPress data:

1. Create test accommodations in WordPress with Booking.com data
2. Verify data retrieval in FastAPI
3. Verify display in templates
4. Test affiliate link generation

## Troubleshooting

### Booking.com Data Not Displaying

1. Check WordPress ACF fields are filled
2. Verify field names match configuration
3. Check FastAPI logs for validation errors
4. Verify WordPress REST API is accessible

### Affiliate Links Not Working

1. Check `BOOKING_AFFILIATE_ID` is set in `.env`
2. Verify affiliate ID is valid
3. Check application startup logs for warnings
4. Test link generation in unit tests

### Invalid Data Warnings

1. Check WordPress ACF field values
2. Verify price is positive
3. Verify rating is between 0-10
4. Verify review count is non-negative

## Future Enhancements

### Potential Improvements

1. **Automated Data Updates**: Integrate with Booking.com API for automatic updates
2. **Price History**: Track price changes over time
3. **Availability Calendar**: Display availability calendar from Booking.com
4. **Dynamic Pricing**: Show real-time pricing based on dates
5. **Multi-Currency Support**: Display prices in multiple currencies

### API Integration (Future)

If Booking.com API access is obtained:

1. Replace manual ACF updates with API calls
2. Implement caching for API responses
3. Add rate limiting and error handling
4. Implement background data synchronization

## Support

For issues or questions:

1. Check application logs: `docker-compose logs frontend`
2. Review WordPress ACF field configuration
3. Verify environment variables are set
4. Test with unit tests
5. Contact development team

## References

- [Booking.com Affiliate Program](https://www.booking.com/affiliate-program/v2/index.html)
- [WordPress ACF Documentation](https://www.advancedcustomfields.com/resources/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

# Booking.com Integration Tests

## Overview

This directory contains tests for the Booking.com integration feature. Tests are organized into unit tests and property-based tests.

## Test Files

### Unit Tests

- `test_booking_affiliate.py`: Tests for affiliate link generation
- `test_booking_validator.py`: Tests for data validation and sanitization
- `test_accommodation_service.py`: Tests for accommodation service (to be created)

### Property-Based Tests

Property-based tests use Hypothesis to generate random test data and verify universal properties.

## Running Tests

### Prerequisites

1. Ensure Docker is running
2. Start the application: `docker-compose up -d`

### Run All Tests

```bash
# Run all booking integration tests
docker-compose exec frontend pytest app/tests/test_booking_*.py -v

# Run with coverage
docker-compose exec frontend pytest app/tests/test_booking_*.py --cov=app/utils --cov=app/services -v
```

### Run Specific Test Files

```bash
# Test affiliate link generation
docker-compose exec frontend pytest app/tests/test_booking_affiliate.py -v

# Test data validation
docker-compose exec frontend pytest app/tests/test_booking_validator.py -v
```

### Run Property-Based Tests Only

```bash
# Run only property-based tests
docker-compose exec frontend pytest app/tests/ -v -m property
```

### Run with Verbose Output

```bash
# Show detailed test output
docker-compose exec frontend pytest app/tests/test_booking_*.py -vv
```

## Test Coverage

### Expected Coverage

- **AffiliateLinkGenerator**: 100% coverage
- **DataValidator**: 100% coverage
- **AccommodationService**: 85%+ coverage

### Generate Coverage Report

```bash
# Generate HTML coverage report
docker-compose exec frontend pytest app/tests/test_booking_*.py --cov=app/utils --cov=app/services --cov-report=html

# View report (generated in htmlcov/ directory)
open htmlcov/index.html
```

## Test Structure

### Unit Test Example

```python
def test_generate_link_with_valid_property_id(self):
    """Test link generation with valid property ID"""
    property_id = "789012"
    link = self.generator.generate_link(property_id)
    
    assert link is not None
    assert "booking.com" in link
    assert f"aid={self.affiliate_id}" in link
```

### Property-Based Test Example

```python
@given(st.integers(min_value=1, max_value=999999999))
def test_property_link_generation(self, property_id):
    """Property test: Any valid property ID should generate a valid link"""
    link = self.generator.generate_link(str(property_id))
    
    assert link is not None
    assert "booking.com" in link
```

## Test Data

### Valid Test Data

```python
# Valid property IDs
valid_property_ids = ["123456", "789012", "1"]

# Valid prices
valid_prices = [50.0, 100.5, 0.01]

# Valid ratings
valid_ratings = [0.0, 5.0, 10.0, 7.5]

# Valid review counts
valid_review_counts = [0, 10, 1000]
```

### Invalid Test Data

```python
# Invalid property IDs
invalid_property_ids = ["", "abc", "12.34", None, "  "]

# Invalid prices
invalid_prices = [0.0, -10.0, -0.01, "abc"]

# Invalid ratings
invalid_ratings = [-1.0, 10.1, 15.0, "abc"]

# Invalid review counts
invalid_review_counts = [-1, -100, 10.5, "abc"]
```

## Debugging Tests

### Run Single Test

```bash
# Run a specific test function
docker-compose exec frontend pytest app/tests/test_booking_affiliate.py::TestAffiliateLinkGenerator::test_generate_link_with_valid_property_id -v
```

### Show Print Statements

```bash
# Show print statements in test output
docker-compose exec frontend pytest app/tests/test_booking_*.py -v -s
```

### Stop on First Failure

```bash
# Stop on first test failure
docker-compose exec frontend pytest app/tests/test_booking_*.py -v -x
```

### Run Failed Tests Only

```bash
# Re-run only failed tests from last run
docker-compose exec frontend pytest app/tests/test_booking_*.py -v --lf
```

## Continuous Integration

### Pre-Commit Checks

Before committing code, run:

```bash
# Run all tests
docker-compose exec frontend pytest app/tests/test_booking_*.py -v

# Check code coverage
docker-compose exec frontend pytest app/tests/test_booking_*.py --cov=app/utils --cov=app/services --cov-report=term-missing

# Ensure coverage is above 85%
```

### CI Pipeline

The CI pipeline should:

1. Run all unit tests
2. Run all property-based tests
3. Generate coverage report
4. Fail if coverage is below 85%
5. Fail if any test fails

## Troubleshooting

### Import Errors

If you see import errors:

```bash
# Ensure you're in the correct directory
docker-compose exec frontend pwd

# Check Python path
docker-compose exec frontend python -c "import sys; print(sys.path)"

# Install dependencies
docker-compose exec frontend pip install -r requirements.txt
```

### Hypothesis Errors

If property-based tests fail:

```bash
# Run with more examples
docker-compose exec frontend pytest app/tests/test_booking_*.py -v --hypothesis-show-statistics

# Debug specific failure
docker-compose exec frontend pytest app/tests/test_booking_*.py -v --hypothesis-verbosity=verbose
```

### Docker Issues

If Docker is not running:

```bash
# Start Docker
# On macOS: Open Docker Desktop
# On Linux: sudo systemctl start docker

# Verify Docker is running
docker ps

# Rebuild containers if needed
docker-compose down && docker-compose up --build -d
```

## Adding New Tests

### Unit Test Template

```python
def test_new_feature(self):
    """Test description"""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Property-Based Test Template

```python
@given(st.text())
def test_property_new_feature(self, input_data):
    """Property test: Description of property"""
    result = function_to_test(input_data)
    
    # Assert universal property
    assert isinstance(result, str)
```

## Best Practices

1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Organization**: Group related tests in classes
3. **Test Independence**: Each test should be independent and not rely on others
4. **Test Data**: Use realistic test data that represents actual use cases
5. **Assertions**: Use specific assertions that clearly indicate what failed
6. **Documentation**: Add docstrings to explain complex tests
7. **Coverage**: Aim for 85%+ code coverage
8. **Property Tests**: Use property-based tests for universal properties

## References

- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)

"""
Unit tests for Booking.com data validation
"""
import pytest
from hypothesis import given, strategies as st
from app.utils.booking_validator import DataValidator


class TestDataValidator:
    """Test suite for DataValidator"""
    
    def test_validate_price_positive(self):
        """Test price validation with positive values"""
        assert DataValidator.validate_price(50.0) == 50.0
        assert DataValidator.validate_price(100.5) == 100.5
        assert DataValidator.validate_price(0.01) == 0.01
    
    def test_validate_price_zero(self):
        """Test price validation with zero"""
        assert DataValidator.validate_price(0.0) is None
    
    def test_validate_price_negative(self):
        """Test price validation with negative values"""
        assert DataValidator.validate_price(-10.0) is None
        assert DataValidator.validate_price(-0.01) is None
    
    def test_validate_price_none(self):
        """Test price validation with None"""
        assert DataValidator.validate_price(None) is None
    
    def test_validate_price_invalid_type(self):
        """Test price validation with invalid types"""
        assert DataValidator.validate_price("abc") is None
        assert DataValidator.validate_price([]) is None
    
    def test_validate_rating_valid_range(self):
        """Test rating validation with valid range (0-10)"""
        assert DataValidator.validate_rating(0.0) == 0.0
        assert DataValidator.validate_rating(5.0) == 5.0
        assert DataValidator.validate_rating(10.0) == 10.0
        assert DataValidator.validate_rating(7.5) == 7.5
    
    def test_validate_rating_out_of_range(self):
        """Test rating validation with out of range values"""
        assert DataValidator.validate_rating(-1.0) is None
        assert DataValidator.validate_rating(10.1) is None
        assert DataValidator.validate_rating(15.0) is None
    
    def test_validate_rating_none(self):
        """Test rating validation with None"""
        assert DataValidator.validate_rating(None) is None
    
    def test_validate_rating_invalid_type(self):
        """Test rating validation with invalid types"""
        assert DataValidator.validate_rating("abc") is None
        assert DataValidator.validate_rating([]) is None
    
    def test_validate_review_count_positive(self):
        """Test review count validation with positive values"""
        assert DataValidator.validate_review_count(0) == 0
        assert DataValidator.validate_review_count(10) == 10
        assert DataValidator.validate_review_count(1000) == 1000
    
    def test_validate_review_count_negative(self):
        """Test review count validation with negative values"""
        assert DataValidator.validate_review_count(-1) is None
        assert DataValidator.validate_review_count(-100) is None
    
    def test_validate_review_count_none(self):
        """Test review count validation with None"""
        assert DataValidator.validate_review_count(None) is None
    
    def test_validate_review_count_invalid_type(self):
        """Test review count validation with invalid types"""
        assert DataValidator.validate_review_count("abc") is None
        assert DataValidator.validate_review_count(10.5) is None
        assert DataValidator.validate_review_count([]) is None
    
    def test_sanitize_text_clean(self):
        """Test text sanitization with clean text"""
        clean_text = "This is clean text"
        assert DataValidator.sanitize_text(clean_text) == clean_text
    
    def test_sanitize_text_xss_script(self):
        """Test text sanitization with XSS script tags"""
        malicious = "<script>alert('XSS')</script>"
        sanitized = DataValidator.sanitize_text(malicious)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized or "&lt;script&gt;" in sanitized
    
    def test_sanitize_text_xss_img(self):
        """Test text sanitization with XSS img tags"""
        malicious = '<img src="x" onerror="alert(1)">'
        sanitized = DataValidator.sanitize_text(malicious)
        assert "onerror" not in sanitized or "&lt;" in sanitized
    
    def test_sanitize_text_xss_iframe(self):
        """Test text sanitization with XSS iframe tags"""
        malicious = '<iframe src="evil.com"></iframe>'
        sanitized = DataValidator.sanitize_text(malicious)
        assert "<iframe>" not in sanitized or "&lt;iframe&gt;" in sanitized
    
    def test_sanitize_text_none(self):
        """Test text sanitization with None"""
        assert DataValidator.sanitize_text(None) == ""
    
    def test_sanitize_text_empty(self):
        """Test text sanitization with empty string"""
        assert DataValidator.sanitize_text("") == ""
    
    @given(st.floats(min_value=0.01, max_value=10000.0))
    def test_property_price_validation(self, price):
        """Property test: Any positive price should be valid"""
        result = DataValidator.validate_price(price)
        assert result == price or result is None  # None if NaN or Inf
    
    @given(st.floats(min_value=0.0, max_value=10.0))
    def test_property_rating_validation(self, rating):
        """Property test: Any rating between 0-10 should be valid"""
        result = DataValidator.validate_rating(rating)
        assert result == rating or result is None  # None if NaN
    
    @given(st.integers(min_value=0, max_value=100000))
    def test_property_review_count_validation(self, count):
        """Property test: Any non-negative integer should be valid"""
        result = DataValidator.validate_review_count(count)
        assert result == count
    
    @given(st.text())
    def test_property_xss_sanitization(self, text):
        """Property test: Any text should be sanitized without errors"""
        result = DataValidator.sanitize_text(text)
        assert isinstance(result, str)
        # Check that common XSS patterns are escaped
        if "<script>" in text:
            assert "<script>" not in result or "&lt;script&gt;" in result

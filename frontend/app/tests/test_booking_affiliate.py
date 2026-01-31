"""
Unit tests for Booking.com affiliate link generation
"""
import pytest
from hypothesis import given, strategies as st
from app.utils.booking_affiliate import AffiliateLinkGenerator


class TestAffiliateLinkGenerator:
    """Test suite for AffiliateLinkGenerator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.affiliate_id = "123456"
        self.tracking_params = {
            "utm_source": "veriaguide",
            "utm_medium": "referral",
            "utm_campaign": "accommodations"
        }
        self.generator = AffiliateLinkGenerator(
            self.affiliate_id,
            self.tracking_params
        )
    
    def test_generate_link_with_valid_property_id(self):
        """Test link generation with valid property ID"""
        property_id = "789012"
        link = self.generator.generate_link(property_id)
        
        assert link is not None
        assert "booking.com" in link
        assert f"aid={self.affiliate_id}" in link
        assert f"dest_id={property_id}" in link
        assert "dest_type=hotel" in link
        assert "utm_source=veriaguide" in link
        assert "utm_medium=referral" in link
        assert "utm_campaign=accommodations" in link
    
    def test_generate_link_with_invalid_property_id(self):
        """Test link generation with invalid property ID"""
        invalid_ids = ["", "abc", "12.34", None, "  "]
        
        for invalid_id in invalid_ids:
            link = self.generator.generate_link(invalid_id)
            assert link is None
    
    def test_validate_property_id_valid(self):
        """Test property ID validation with valid IDs"""
        valid_ids = ["123456", "789012", "1"]
        
        for valid_id in valid_ids:
            assert self.generator.validate_property_id(valid_id) is True
    
    def test_validate_property_id_invalid(self):
        """Test property ID validation with invalid IDs"""
        invalid_ids = ["", "abc", "12.34", None, "  ", "12-34"]
        
        for invalid_id in invalid_ids:
            assert self.generator.validate_property_id(invalid_id) is False
    
    def test_affiliate_parameter_inclusion(self):
        """Test that affiliate parameters are included in link"""
        property_id = "123456"
        link = self.generator.generate_link(property_id)
        
        assert f"aid={self.affiliate_id}" in link
    
    def test_tracking_parameter_inclusion(self):
        """Test that tracking parameters are included in link"""
        property_id = "123456"
        link = self.generator.generate_link(property_id)
        
        for key, value in self.tracking_params.items():
            assert f"{key}={value}" in link
    
    def test_link_format(self):
        """Test that generated link has correct format"""
        property_id = "123456"
        link = self.generator.generate_link(property_id)
        
        assert link.startswith("https://www.booking.com/")
        assert "?" in link  # Query parameters present
    
    @given(st.integers(min_value=1, max_value=999999999))
    def test_property_link_generation(self, property_id):
        """Property test: Any valid property ID should generate a valid link"""
        link = self.generator.generate_link(str(property_id))
        
        assert link is not None
        assert "booking.com" in link
        assert f"aid={self.affiliate_id}" in link
        assert f"dest_id={property_id}" in link

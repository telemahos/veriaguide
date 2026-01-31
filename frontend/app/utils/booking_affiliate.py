"""
Booking.com Affiliate Link Generator

Generates affiliate links to Booking.com with tracking parameters.
"""
from typing import Optional, Dict
from urllib.parse import urlencode
import re


class AffiliateLinkGenerator:
    """Generate Booking.com affiliate links with tracking parameters"""
    
    def __init__(self, affiliate_id: str, tracking_params: Dict[str, str]):
        """
        Initialize affiliate link generator
        
        Args:
            affiliate_id: Booking.com affiliate ID
            tracking_params: Dictionary of tracking parameters (utm_source, utm_medium, utm_campaign)
        """
        self.affiliate_id = affiliate_id
        self.tracking_params = tracking_params
        self.base_url = "https://www.booking.com/searchresults.html"
    
    def generate_link(self, property_id: Optional[str]) -> Optional[str]:
        """
        Generate Booking.com affiliate link for a property
        
        Args:
            property_id: Booking.com property ID
            
        Returns:
            Affiliate link URL or None if property_id is invalid
        """
        if not self.validate_property_id(property_id):
            return None
        
        # Build query parameters
        params = {
            "aid": self.affiliate_id,
            "dest_id": property_id,
            "dest_type": "hotel",
            **self.tracking_params
        }
        
        # Generate URL with parameters
        query_string = urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def validate_property_id(self, property_id: Optional[str]) -> bool:
        """
        Validate property ID format
        
        Args:
            property_id: Property ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not property_id:
            return False
        
        if not isinstance(property_id, str):
            return False
        
        # Remove whitespace
        property_id = property_id.strip()
        
        if not property_id:
            return False
        
        # Check if it's a valid numeric ID
        if not re.match(r'^\d+$', property_id):
            return False
        
        return True

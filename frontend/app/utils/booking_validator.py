"""
Booking.com Data Validator

Validates and sanitizes Booking.com data from WordPress ACF fields.
"""
from typing import Optional
import html
import math


class DataValidator:
    """Validate and sanitize Booking.com data"""
    
    @staticmethod
    def validate_price(price: Optional[float]) -> Optional[float]:
        """
        Validate price is positive
        
        Args:
            price: Price value to validate
            
        Returns:
            Valid price or None if invalid
        """
        if price is None:
            return None
        
        try:
            price_float = float(price)
            
            # Check for NaN or Inf
            if math.isnan(price_float) or math.isinf(price_float):
                return None
            
            # Price must be positive
            if price_float <= 0:
                return None
            
            return price_float
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_rating(rating: Optional[float]) -> Optional[float]:
        """
        Validate rating is between 0-10
        
        Args:
            rating: Rating value to validate
            
        Returns:
            Valid rating or None if invalid
        """
        if rating is None:
            return None
        
        try:
            rating_float = float(rating)
            
            # Check for NaN or Inf
            if math.isnan(rating_float) or math.isinf(rating_float):
                return None
            
            # Rating must be between 0 and 10
            if rating_float < 0 or rating_float > 10:
                return None
            
            return rating_float
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def validate_review_count(count: Optional[int]) -> Optional[int]:
        """
        Validate review count is non-negative
        
        Args:
            count: Review count to validate
            
        Returns:
            Valid count or None if invalid
        """
        if count is None:
            return None
        
        try:
            count_int = int(count)
            
            # Count must be non-negative
            if count_int < 0:
                return None
            
            return count_int
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def sanitize_text(text: Optional[str]) -> str:
        """
        Remove XSS payloads from text
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        if text is None:
            return ""
        
        if not isinstance(text, str):
            return ""
        
        # Use html.escape to escape HTML special characters
        # This prevents XSS attacks by converting < > & " ' to HTML entities
        return html.escape(text)

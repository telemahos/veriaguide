"""
Input validation and sanitization utilities
"""
import re
import html
from typing import Any, Optional, Dict, List
from fastapi import HTTPException
from app.utils.logging_config import get_logger

logger = get_logger("validation")


class InputValidator:
    """Input validation and sanitization utilities"""
    
    # Common regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    SLUG_PATTERN = re.compile(r'^[a-z0-9-]+$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]+$')
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        if not text:
            return ""
        
        # HTML escape
        sanitized = html.escape(text)
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'onmouseover=',
            r'<script',
            r'</script>',
            r'<iframe',
            r'</iframe>',
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email or len(email) > 254:
            return False
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate URL slug format"""
        if not slug or len(slug) > 200:
            return False
        return bool(InputValidator.SLUG_PATTERN.match(slug))
    
    @staticmethod
    def validate_safe_string(text: str, max_length: int = 1000) -> bool:
        """Validate that string contains only safe characters"""
        if not text or len(text) > max_length:
            return False
        return bool(InputValidator.SAFE_STRING_PATTERN.match(text))
    
    @staticmethod
    def validate_integer(value: Any, min_val: int = None, max_val: int = None) -> bool:
        """Validate integer value with optional range"""
        try:
            int_val = int(value)
            if min_val is not None and int_val < min_val:
                return False
            if max_val is not None and int_val > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """Validate and sanitize search query"""
        if not query:
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # Sanitize
        sanitized = InputValidator.sanitize_html(query)
        
        # Length check
        if len(sanitized) > 200:
            raise HTTPException(status_code=400, detail="Search query too long")
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        if not sanitized:
            raise HTTPException(status_code=400, detail="Invalid search query")
        
        return sanitized
    
    @staticmethod
    def validate_pagination_params(page: int, per_page: int) -> Dict[str, int]:
        """Validate pagination parameters"""
        if not InputValidator.validate_integer(page, min_val=1, max_val=1000):
            raise HTTPException(status_code=400, detail="Invalid page number")
        
        if not InputValidator.validate_integer(per_page, min_val=1, max_val=100):
            raise HTTPException(status_code=400, detail="Invalid per_page value")
        
        return {"page": int(page), "per_page": int(per_page)}
    
    @staticmethod
    def validate_contact_form(name: str, email: str, subject: str, message: str) -> Dict[str, str]:
        """Validate contact form data"""
        errors = []
        
        # Validate name
        if not name or len(name.strip()) < 2:
            errors.append("Name must be at least 2 characters long")
        elif len(name) > 100:
            errors.append("Name must be less than 100 characters")
        elif not InputValidator.validate_safe_string(name, 100):
            errors.append("Name contains invalid characters")
        
        # Validate email
        if not email:
            errors.append("Email is required")
        elif not InputValidator.validate_email(email):
            errors.append("Invalid email format")
        
        # Validate subject
        if not subject or len(subject.strip()) < 5:
            errors.append("Subject must be at least 5 characters long")
        elif len(subject) > 200:
            errors.append("Subject must be less than 200 characters")
        
        # Validate message
        if not message or len(message.strip()) < 10:
            errors.append("Message must be at least 10 characters long")
        elif len(message) > 5000:
            errors.append("Message must be less than 5000 characters")
        
        if errors:
            raise HTTPException(status_code=400, detail="; ".join(errors))
        
        return {
            "name": InputValidator.sanitize_html(name.strip()),
            "email": email.strip().lower(),
            "subject": InputValidator.sanitize_html(subject.strip()),
            "message": InputValidator.sanitize_html(message.strip())
        }
    
    @staticmethod
    def validate_admin_access(request) -> bool:
        """Secure admin access validation with API key"""
        import os
        import hmac
        
        # Get API key from request headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning(f"Admin access attempt without API key from {request.client.host if request.client else 'unknown'}")
            return False
        
        # Get expected API key from environment
        expected_api_key = os.getenv("ADMIN_API_KEY")
        if not expected_api_key:
            logger.error("ADMIN_API_KEY not configured in environment")
            return False
        
        # Validate API key (constant-time comparison to prevent timing attacks)
        is_valid = hmac.compare_digest(api_key, expected_api_key)
        
        if not is_valid:
            logger.warning(f"Invalid admin API key attempt from {request.client.host if request.client else 'unknown'}")
        
        return is_valid
    
    @staticmethod
    def validate_submission_form(
        business_name: str,
        category: str,
        description: str,
        email: str,
        phone: str,
        address: str,
        city: str,
        opening_hours: str,
        website: Optional[str] = None,
        latitude: Optional[str] = None,
        longitude: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate business submission form data"""
        errors = []
        
        # Validate business name
        if not business_name or len(business_name.strip()) < 2:
            errors.append("Geschäftsname muss mindestens 2 Zeichen lang sein")
        elif len(business_name) > 200:
            errors.append("Geschäftsname darf maximal 200 Zeichen lang sein")
        
        # Validate category
        valid_categories = ["restaurant", "cafe", "accommodation", "museum", "tour", "shop", "service"]
        if category not in valid_categories:
            errors.append("Ungültige Kategorie ausgewählt")
        
        # Validate description
        if not description or len(description.strip()) < 50:
            errors.append("Beschreibung muss mindestens 50 Zeichen lang sein")
        elif len(description) > 2000:
            errors.append("Beschreibung darf maximal 2000 Zeichen lang sein")
        
        # Validate email
        if not email:
            errors.append("E-Mail ist erforderlich")
        elif not InputValidator.validate_email(email):
            errors.append("Ungültiges E-Mail-Format")
        
        # Validate phone
        phone_pattern = re.compile(r'^[\d\s\+\-\(\)]+$')
        if not phone or len(phone.strip()) < 6:
            errors.append("Telefonnummer ist erforderlich")
        elif len(phone) > 20:
            errors.append("Telefonnummer zu lang")
        elif not phone_pattern.match(phone):
            errors.append("Ungültige Telefonnummer")
        
        # Validate address
        if not address or len(address.strip()) < 5:
            errors.append("Adresse muss mindestens 5 Zeichen lang sein")
        elif len(address) > 200:
            errors.append("Adresse zu lang")
        
        # Validate city
        if not city or len(city.strip()) < 2:
            errors.append("Stadt ist erforderlich")
        elif len(city) > 100:
            errors.append("Stadtname zu lang")
        
        # Validate opening hours
        if not opening_hours or len(opening_hours.strip()) < 5:
            errors.append("Öffnungszeiten sind erforderlich")
        elif len(opening_hours) > 500:
            errors.append("Öffnungszeiten zu lang")
        
        # Validate website (optional)
        if website:
            url_pattern = re.compile(r'^https?://[^\s]+$')
            if not url_pattern.match(website) or len(website) > 500:
                errors.append("Ungültige Website-URL")
        
        # Validate coordinates (optional)
        lat_val = None
        lon_val = None
        if latitude or longitude:
            try:
                if latitude:
                    lat_val = float(latitude)
                    if not (-90 <= lat_val <= 90):
                        errors.append("Breitengrad muss zwischen -90 und 90 liegen")
                if longitude:
                    lon_val = float(longitude)
                    if not (-180 <= lon_val <= 180):
                        errors.append("Längengrad muss zwischen -180 und 180 liegen")
            except ValueError:
                errors.append("Ungültige GPS-Koordinaten")
        
        if errors:
            raise HTTPException(status_code=400, detail="; ".join(errors))
        
        return {
            "business_name": InputValidator.sanitize_html(business_name.strip()),
            "category": category,
            "description": InputValidator.sanitize_html(description.strip()),
            "email": email.strip().lower(),
            "phone": phone.strip(),
            "address": InputValidator.sanitize_html(address.strip()),
            "city": InputValidator.sanitize_html(city.strip()),
            "opening_hours": InputValidator.sanitize_html(opening_hours.strip()),
            "website": website.strip() if website else None,
            "latitude": lat_val,
            "longitude": lon_val
        }
"""
Contact Service - Handles contact form operations
"""
from typing import Dict, Any
from app.api.wordpress import submit_contact_form


class ContactService:
    """Service class for handling contact form operations"""
    
    @staticmethod
    async def submit_contact_form(
        name: str,
        email: str,
        subject: str,
        message: str
    ) -> Dict[str, Any]:
        """Submit contact form and return result"""
        return await submit_contact_form(name, email, subject, message)
"""
Contact Service - Handles contact form operations
"""
from typing import Any

from app.api.wordpress import submit_contact_form


class ContactService:
    """Service class for handling contact form operations"""
    
    @staticmethod
    async def submit_contact_form(
        name: str,
        email: str,
        subject: str,
        message: str
    ) -> dict[str, Any]:
        """Submit contact form and return result"""
        return await submit_contact_form(name, email, subject, message)
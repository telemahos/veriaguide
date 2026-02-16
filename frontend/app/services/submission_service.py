"""
Submission Service - Handles user-submitted business listings
"""
import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class SubmissionService:
    """Service class for handling user submissions"""
    
    SUBMISSIONS_DIR = Path("data/submissions")
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGES = 10
    
    @classmethod
    def _ensure_submissions_dir(cls):
        """Ensure submissions directory exists"""
        cls.SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def save_submission(
        cls,
        business_name: str,
        category: str,
        description: str,
        email: str,
        phone: str,
        address: str,
        city: str,
        opening_hours: str,
        website: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        images: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Save user submission to file system"""
        try:
            cls._ensure_submissions_dir()
            
            # Generate unique submission ID
            submission_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Prepare submission data
            submission_data = {
                "id": submission_id,
                "status": "pending",
                "submitted_at": timestamp,
                "business_info": {
                    "name": business_name,
                    "category": category,
                    "description": description,
                    "city": city,
                    "address": address,
                    "phone": phone,
                    "email": email,
                    "website": website,
                    "opening_hours": opening_hours
                },
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                } if latitude and longitude else None,
                "images": images,
                "admin_notes": ""
            }
            
            # Save to JSON file
            submission_file = cls.SUBMISSIONS_DIR / f"{submission_id}.json"
            with open(submission_file, 'w', encoding='utf-8') as f:
                json.dump(submission_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"New submission saved: {submission_id} - {business_name}")
            
            return {
                "success": True,
                "submission_id": submission_id,
                "message": "Ihre Einreichung wurde erfolgreich gespeichert und wird geprüft."
            }
            
        except Exception as e:
            logger.error(f"Error saving submission: {str(e)}")
            return {
                "success": False,
                "message": "Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."
            }
    
    @classmethod
    def validate_image(cls, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate uploaded image"""
        # Check file extension
        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_IMAGE_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Ungültiges Dateiformat. Erlaubt: {', '.join(cls.ALLOWED_IMAGE_EXTENSIONS)}"
            }
        
        # Check file size
        if file_size > cls.MAX_IMAGE_SIZE:
            return {
                "valid": False,
                "error": f"Datei zu groß. Maximum: {cls.MAX_IMAGE_SIZE / (1024*1024):.0f}MB"
            }
        
        return {"valid": True}
    
    @classmethod
    async def get_pending_submissions(cls) -> List[Dict[str, Any]]:
        """Get all pending submissions (admin only)"""
        try:
            cls._ensure_submissions_dir()
            submissions = []
            
            for file_path in cls.SUBMISSIONS_DIR.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("status") == "pending":
                        submissions.append(data)
            
            # Sort by submission date (newest first)
            submissions.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
            
            return submissions
            
        except Exception as e:
            logger.error(f"Error loading submissions: {str(e)}")
            return []
    
    @classmethod
    async def update_submission_status(
        cls,
        submission_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update submission status (admin only)"""
        try:
            submission_file = cls.SUBMISSIONS_DIR / f"{submission_id}.json"
            
            if not submission_file.exists():
                return {"success": False, "message": "Submission not found"}
            
            with open(submission_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["status"] = status
            data["updated_at"] = datetime.utcnow().isoformat()
            
            if admin_notes:
                data["admin_notes"] = admin_notes
            
            with open(submission_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Submission {submission_id} status updated to: {status}")
            
            return {"success": True, "message": "Status updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating submission: {str(e)}")
            return {"success": False, "message": str(e)}

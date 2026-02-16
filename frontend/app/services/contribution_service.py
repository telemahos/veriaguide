"""
Contribution Service - Handles user contributions to existing listings
"""
import os
import json
import uuid
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class ContributionService:
    """Service class for handling user contributions"""
    
    CONTRIBUTIONS_DIR = Path("data/contributions")
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.ogg'}
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGES = 10
    MAX_VIDEOS = 3
    
    @classmethod
    def _ensure_contributions_dir(cls):
        """Ensure contributions directory exists"""
        cls.CONTRIBUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def save_contribution(
        cls,
        listing_id: str,
        listing_category: str,
        contribution_types: List[str],
        email: str,
        name: Optional[str],
        description: Optional[str],
        photos: List[Dict[str, Any]],
        videos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Save user contribution to file system"""
        try:
            cls._ensure_contributions_dir()
            
            # Generate unique contribution ID
            contribution_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Prepare contribution data
            contribution_data = {
                "id": contribution_id,
                "status": "pending",
                "submitted_at": timestamp,
                "listing_info": {
                    "listing_id": listing_id,
                    "category": listing_category
                },
                "contributor": {
                    "email": email,
                    "name": name
                },
                "contribution_types": contribution_types,
                "content": {
                    "description": description,
                    "photos": photos,
                    "videos": videos
                },
                "admin_notes": ""
            }
            
            # Save to JSON file
            contribution_file = cls.CONTRIBUTIONS_DIR / f"{contribution_id}.json"
            with open(contribution_file, 'w', encoding='utf-8') as f:
                json.dump(contribution_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"New contribution saved: {contribution_id} for listing {listing_id}")
            
            return {
                "success": True,
                "contribution_id": contribution_id,
                "message": "Η συνεισφορά σας υποβλήθηκε επιτυχώς και θα ελεγχθεί."
            }
            
        except Exception as e:
            logger.error(f"Error saving contribution: {str(e)}")
            return {
                "success": False,
                "message": "Παρουσιάστηκε σφάλμα. Παρακαλώ δοκιμάστε ξανά αργότερα."
            }
    
    @classmethod
    def validate_image(cls, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate uploaded image"""
        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_IMAGE_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Μη έγκυρη μορφή εικόνας. Επιτρεπόμενες: {', '.join(cls.ALLOWED_IMAGE_EXTENSIONS)}"
            }
        
        if file_size > cls.MAX_IMAGE_SIZE:
            return {
                "valid": False,
                "error": f"Η εικόνα είναι πολύ μεγάλη. Μέγιστο: {cls.MAX_IMAGE_SIZE / (1024*1024):.0f}MB"
            }
        
        return {"valid": True}
    
    @classmethod
    def validate_video(cls, filename: str, file_size: int) -> Dict[str, Any]:
        """Validate uploaded video"""
        ext = Path(filename).suffix.lower()
        if ext not in cls.ALLOWED_VIDEO_EXTENSIONS:
            return {
                "valid": False,
                "error": f"Μη έγκυρη μορφή βίντεο. Επιτρεπόμενες: {', '.join(cls.ALLOWED_VIDEO_EXTENSIONS)}"
            }
        
        if file_size > cls.MAX_VIDEO_SIZE:
            return {
                "valid": False,
                "error": f"Το βίντεο είναι πολύ μεγάλο. Μέγιστο: {cls.MAX_VIDEO_SIZE / (1024*1024):.0f}MB"
            }
        
        return {"valid": True}
    
    @classmethod
    async def get_pending_contributions(cls) -> List[Dict[str, Any]]:
        """Get all pending contributions (admin only)"""
        try:
            cls._ensure_contributions_dir()
            contributions = []
            
            for file_path in cls.CONTRIBUTIONS_DIR.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("status") == "pending":
                        contributions.append(data)
            
            contributions.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
            
            return contributions
            
        except Exception as e:
            logger.error(f"Error loading contributions: {str(e)}")
            return []
    
    @classmethod
    async def update_contribution_status(
        cls,
        contribution_id: str,
        status: str,
        admin_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update contribution status (admin only)"""
        try:
            contribution_file = cls.CONTRIBUTIONS_DIR / f"{contribution_id}.json"
            
            if not contribution_file.exists():
                return {"success": False, "message": "Contribution not found"}
            
            with open(contribution_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["status"] = status
            data["updated_at"] = datetime.utcnow().isoformat()
            
            if admin_notes:
                data["admin_notes"] = admin_notes
            
            with open(contribution_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Contribution {contribution_id} status updated to: {status}")
            
            return {"success": True, "message": "Status updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating contribution: {str(e)}")
            return {"success": False, "message": str(e)}

"""VeriaGuide AI Travel Guide (feature flag AI_GUIDE_ENABLED)."""
from app.ai_guide import translations  # noqa: F401
from app.ai_guide.config import is_enabled
from app.ai_guide.routes import create_router

__all__ = ["create_router", "is_enabled"]

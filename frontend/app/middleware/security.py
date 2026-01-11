"""
Security middleware for VeriaGuide application
"""
import time
from typing import Dict, Any
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from app.config import DEBUG, ALLOWED_HOSTS
from app.utils.logging_config import get_logger

logger = get_logger("security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy (always apply, but stricter in production)
        if DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://maps.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' https://maps.googleapis.com ws: wss:; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://maps.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://maps.googleapis.com; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests;"
            )
        response.headers["Content-Security-Policy"] = csp
        
        # HTTPS enforcement in production
        if not DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, Dict[str, Any]] = {}
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/admin/cache-health"] or request.url.path.startswith("/static"):
            return await call_next(request)
        
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        if client_ip in self.clients:
            client_data = self.clients[client_ip]
            client_data["requests"] = [
                req_time for req_time in client_data["requests"]
                if current_time - req_time < self.period
            ]
        else:
            self.clients[client_ip] = {"requests": []}
        
        # Check rate limit
        client_requests = self.clients[client_ip]["requests"]
        if len(client_requests) >= self.calls:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            
            # For API endpoints, return JSON
            if request.url.path.startswith("/admin/") or request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": self.period}
                )
            
            # For web pages, return HTML error page
            from fastapi.templating import Jinja2Templates
            templates = Jinja2Templates(directory="templates")
            try:
                return templates.TemplateResponse(
                    "errors/429.html",
                    {"request": request, "retry_after": self.period},
                    status_code=429
                )
            except Exception:
                # Fallback to JSON if template fails
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "retry_after": self.period}
                )
        
        # Add current request
        client_requests.append(current_time)
        
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size"""
    
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_size:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request entity too large"}
                )
        
        return await call_next(request)


def setup_cors_middleware(app):
    """Setup CORS middleware"""
    allowed_origins = ["*"] if DEBUG else [
        "https://veriaguide.com",
        "https://www.veriaguide.com",
        "https://cms.veriaguide.com"
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"]
    )
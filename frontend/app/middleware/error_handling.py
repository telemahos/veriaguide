"""
Error handling middleware and exception handlers
"""
import traceback
from typing import Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logging_config import get_logger
from app.config import DEBUG

logger = get_logger("error_handler")
templates = Jinja2Templates(directory="templates")


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")
    
    # For API endpoints, return JSON
    if request.url.path.startswith("/admin/") or request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": str(request.url.path)
            }
        )
    
    # For web pages, return HTML error page
    try:
        if exc.status_code == 404:
            return templates.TemplateResponse(
                "errors/404.html",
                {"request": request, "error": exc.detail},
                status_code=404
            )
        elif exc.status_code == 500:
            return templates.TemplateResponse(
                "errors/500.html",
                {"request": request, "error": exc.detail},
                status_code=500
            )
        else:
            return templates.TemplateResponse(
                "errors/generic.html",
                {
                    "request": request,
                    "error": exc.detail,
                    "status_code": exc.status_code
                },
                status_code=exc.status_code
            )
    except Exception as template_error:
        logger.error(f"Error rendering error template: {template_error}")
        # Fallback to simple HTML
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Error {exc.status_code}</title></head>
                <body>
                    <h1>Error {exc.status_code}</h1>
                    <p>{exc.detail}</p>
                </body>
            </html>
            """,
            status_code=exc.status_code
        )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    error_id = f"error_{int(time.time())}"
    
    logger.error(
        f"Unhandled exception {error_id} on {request.url}: {str(exc)}",
        extra={"traceback": traceback.format_exc()}
    )
    
    # In debug mode, show detailed error
    if DEBUG:
        error_detail = f"{type(exc).__name__}: {str(exc)}"
        traceback_info = traceback.format_exc()
    else:
        error_detail = "Internal server error"
        traceback_info = None
    
    # For API endpoints, return JSON
    if request.url.path.startswith("/admin/") or request.url.path.startswith("/api/"):
        content = {
            "error": error_detail,
            "error_id": error_id,
            "status_code": 500
        }
        if DEBUG and traceback_info:
            content["traceback"] = traceback_info
        
        return JSONResponse(status_code=500, content=content)
    
    # For web pages, return HTML error page
    try:
        return templates.TemplateResponse(
            "errors/500.html",
            {
                "request": request,
                "error": error_detail,
                "error_id": error_id,
                "traceback": traceback_info if DEBUG else None
            },
            status_code=500
        )
    except Exception as template_error:
        logger.error(f"Error rendering error template: {template_error}")
        # Fallback to simple HTML
        content = f"""
        <html>
            <head><title>Internal Server Error</title></head>
            <body>
                <h1>Internal Server Error</h1>
                <p>{error_detail}</p>
                <p>Error ID: {error_id}</p>
                {'<pre>' + traceback_info + '</pre>' if DEBUG and traceback_info else ''}
            </body>
        </html>
        """
        return HTMLResponse(content=content, status_code=500)


async def validation_exception_handler(request: Request, exc: Exception):
    """Handle validation exceptions"""
    logger.warning(f"Validation error on {request.url}: {str(exc)}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": str(exc),
            "status_code": 422
        }
    )
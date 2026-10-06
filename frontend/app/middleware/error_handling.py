"""
Error handling middleware and exception handlers
"""
import time
import traceback

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import DEBUG
from app.i18n import current_lang
from app.utils.logging_config import get_logger

logger = get_logger("error_handler")

# Set from main.py after filters/globals are registered on the app environment.
templates: Jinja2Templates | None = None


def configure_templates(jinja_templates: Jinja2Templates) -> None:
    """Reuse the application Jinja environment (i18n `t` filter, locale helpers)."""
    global templates
    templates = jinja_templates


def get_templates() -> Jinja2Templates:
    if templates is None:
        raise RuntimeError("Jinja templates are not configured")
    return templates


def _error_context(request: Request, extra: dict | None = None) -> dict:
    lang = getattr(getattr(request, "state", None), "lang", None) or current_lang()
    context = {"lang": lang}
    if extra:
        context.update(extra)
    return context


def _fallback_html(status_code: int, detail: str, extra: str = "") -> HTMLResponse:
    return HTMLResponse(
        content=f"""
            <html>
                <head><title>Error {status_code}</title></head>
                <body>
                    <h1>Error {status_code}</h1>
                    <p>{detail}</p>
                    {extra}
                </body>
            </html>
            """,
        status_code=status_code,
    )


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
        jinja = get_templates()
        if exc.status_code == 404:
            return jinja.TemplateResponse(
                request=request,
                name="errors/404.html",
                context=_error_context(request, {"error": exc.detail}),
                status_code=404
            )
        elif exc.status_code == 500:
            return jinja.TemplateResponse(
                request=request,
                name="errors/500.html",
                context=_error_context(request, {"error": exc.detail}),
                status_code=500
            )
        else:
            return jinja.TemplateResponse(
                request=request,
                name="errors/generic.html",
                context=_error_context(
                    request,
                    {
                        "error": exc.detail,
                        "status_code": exc.status_code
                    },
                ),
                status_code=exc.status_code
            )
    except Exception as template_error:
        logger.error(f"Error rendering error template: {template_error}")
        return _fallback_html(exc.status_code, exc.detail)


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
        return get_templates().TemplateResponse(
            request=request,
            name="errors/500.html",
            context=_error_context(
                request,
                {
                    "error": error_detail,
                    "error_id": error_id,
                    "traceback": traceback_info if DEBUG else None
                },
            ),
            status_code=500
        )
    except Exception as template_error:
        logger.error(f"Error rendering error template: {template_error}")
        extra = f"<p>Error ID: {error_id}</p>"
        if DEBUG and traceback_info:
            extra += f"<pre>{traceback_info}</pre>"
        return _fallback_html(500, error_detail, extra)


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

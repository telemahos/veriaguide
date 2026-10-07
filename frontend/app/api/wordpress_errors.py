"""Errors and HTTP mapping when the WordPress API is down."""
from fastapi import HTTPException

WP_RETRY_AFTER_SECONDS = "120"


class WordPressUnavailableError(Exception):
    """WordPress did not return a usable successful response."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def wordpress_unavailable_http() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="Service temporarily unavailable",
        headers={"Retry-After": WP_RETRY_AFTER_SECONDS},
    )

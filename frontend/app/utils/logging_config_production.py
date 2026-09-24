"""
Production logging configuration for VeriaGuide application
Logs only to console/stdout for Docker containers
"""
import logging
import logging.config
import sys

from app.config import DEBUG, LOG_FORMAT, LOG_LEVEL


def setup_logging():
    """Setup production logging configuration (console only)"""
    
    # Production logging configuration - only console output
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": LOG_LEVEL,
                "formatter": "standard",
                "stream": sys.stdout
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "json",
                "stream": sys.stderr
            }
        },
        "loggers": {
            "veriaguide": {
                "level": LOG_LEVEL,
                "handlers": ["console", "error_console"],
                "propagate": False
            },
            "app": {
                "level": LOG_LEVEL,
                "handlers": ["console", "error_console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": LOG_LEVEL,
            "handlers": ["console"]
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set specific log levels for third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    if DEBUG:
        # More verbose logging in debug mode
        logging.getLogger("app").setLevel(logging.DEBUG)
        logging.getLogger("veriaguide").setLevel(logging.DEBUG)
    
    # Get application logger
    logger = logging.getLogger("veriaguide")
    logger.info(f"Production logging configured with level: {LOG_LEVEL}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance"""
    if name is None:
        name = "veriaguide"
    return logging.getLogger(name)
"""
Logging setup for the Translation Service.

This module configures structured logging using structlog.
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import Processor

from src.config import settings


def setup_logging() -> None:
    """
    Set up structured logging for the application.
    
    This configures structlog with appropriate processors based on the
    application's environment (debug or production).
    """
    log_level = getattr(logging, settings.server.log_level.upper())
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
    )
    
    # Set log level for third-party libraries
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(logger_name).setLevel(log_level)
    
    # Configure processors for structlog
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]
    
    # Add different processors based on debug mode
    if settings.debug:
        # In debug mode, use a more human-readable format
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    else:
        # In production, use JSON format
        processors.extend([
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Create a logger instance
logger = structlog.get_logger() 
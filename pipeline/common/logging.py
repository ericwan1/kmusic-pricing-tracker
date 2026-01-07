"""
Structured logging for Cloud Logging integration.
"""

import os
import json
import logging
import sys
from datetime import datetime
from typing import Optional

# Try to import Cloud Logging, fall back to standard logging
try:
    import google.cloud.logging
    from google.cloud.logging.handlers import CloudLoggingHandler
    CLOUD_LOGGING_AVAILABLE = True
except ImportError:
    CLOUD_LOGGING_AVAILABLE = False


def setup_logging(
    name: str = "kpop-scraper",
    level: int = logging.INFO,
    use_cloud_logging: Optional[bool] = None
) -> logging.Logger:
    """
    Set up structured logging.

    Args:
        name: Logger name
        level: Logging level
        use_cloud_logging: Force Cloud Logging (None = auto-detect)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Determine if we should use Cloud Logging
    if use_cloud_logging is None:
        # Auto-detect: use Cloud Logging if in GCP environment
        use_cloud_logging = (
            CLOUD_LOGGING_AVAILABLE and
            os.getenv('GOOGLE_CLOUD_PROJECT') is not None
        )

    if use_cloud_logging and CLOUD_LOGGING_AVAILABLE:
        # Use Cloud Logging
        client = google.cloud.logging.Client()
        handler = CloudLoggingHandler(client, name=name)
        handler.setLevel(level)
        logger.addHandler(handler)

        # Also log to stdout for local development
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)
        logger.addHandler(stdout_handler)
    else:
        # Use standard structured JSON logging
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # JSON formatter for structured logs
        formatter = StructuredJSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class StructuredJSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'severity': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
        }

        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def log_run_start(
    logger: logging.Logger,
    vendor: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> None:
    """Log scraper run start."""
    logger.info(
        "Scraper run started",
        extra={
            'event': 'run_start',
            'vendor': vendor,
            'start_date': start_date,
            'end_date': end_date,
        }
    )


def log_run_complete(
    logger: logging.Logger,
    vendor: str,
    row_count: int,
    duration_seconds: float,
    gcs_path: Optional[str] = None
) -> None:
    """Log scraper run completion."""
    logger.info(
        "Scraper run completed",
        extra={
            'event': 'run_complete',
            'vendor': vendor,
            'row_count': row_count,
            'duration_seconds': duration_seconds,
            'gcs_path': gcs_path,
        }
    )


def log_run_error(
    logger: logging.Logger,
    vendor: str,
    error: Exception,
    duration_seconds: Optional[float] = None
) -> None:
    """Log scraper run error."""
    logger.error(
        f"Scraper run failed: {error}",
        extra={
            'event': 'run_error',
            'vendor': vendor,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'duration_seconds': duration_seconds,
        },
        exc_info=True
    )


def log_validation_error(
    logger: logging.Logger,
    vendor: str,
    errors: list[str]
) -> None:
    """Log validation errors."""
    logger.error(
        "Data validation failed",
        extra={
            'event': 'validation_error',
            'vendor': vendor,
            'errors': errors,
        }
    )

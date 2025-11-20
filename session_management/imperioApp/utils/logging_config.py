"""
Structured logging configuration using structlog (Month 2).

This module configures structlog for production-ready structured logging
with JSON output for easy parsing and analysis.
"""

import structlog
import logging
import logging.handlers
import sys
from pythonjsonlogger import jsonlogger


def configure_logging(app):
    """
    Configure structured logging for the application.

    This sets up structlog with appropriate processors for development
    and production environments.

    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    is_development = app.config.get('FLASK_ENV') == 'development'

    # Timestamper with ISO format
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    # Shared processors for both structlog and stdlib logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Choose renderer based on environment
    if is_development:
        # Human-readable console output for development
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=shared_processors,
        )
    else:
        # JSON output for production (easier to parse)
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # File handler for production
    if not is_development:
        # Rotating file handler (10MB max, keep 10 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Remove existing handlers
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)

    # Configure Flask app logger
    app.logger.handlers.clear()
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

    # Reduce noise from werkzeug in production
    if not is_development:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Log configuration completion
    logger = structlog.get_logger()
    logger.info(
        "logging_configured",
        environment=app.config.get('FLASK_ENV'),
        log_level=app.config.get('LOG_LEVEL'),
        format="json" if not is_development else "console"
    )


def get_logger(name=None):
    """
    Get a structured logger instance.

    Args:
        name: Optional logger name (defaults to caller's module)

    Returns:
        structlog.BoundLogger: Configured logger instance

    Usage:
        from imperioApp.utils.logging_config import get_logger
        log = get_logger(__name__)
        log.info("user_login", user_id=123, username="john")
    """
    return structlog.get_logger(name)


class RequestIDFilter(logging.Filter):
    """
    Logging filter that adds request ID to log records.

    This filter extracts the request ID from Flask's g object
    and adds it to the log record for request tracing.
    """

    def filter(self, record):
        from flask import g, has_request_context

        if has_request_context() and hasattr(g, 'request_id'):
            record.request_id = g.request_id
        else:
            record.request_id = None

        return True


def log_request_start(logger, method, path, **kwargs):
    """
    Log the start of an HTTP request.

    Args:
        logger: structlog logger instance
        method: HTTP method (GET, POST, etc.)
        path: Request path
        **kwargs: Additional context
    """
    logger.info(
        "request_start",
        method=method,
        path=path,
        **kwargs
    )


def log_request_end(logger, method, path, status_code, duration_ms, **kwargs):
    """
    Log the end of an HTTP request.

    Args:
        logger: structlog logger instance
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional context
    """
    logger.info(
        "request_end",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_user_action(logger, action, user_id, **kwargs):
    """
    Log a user action.

    Args:
        logger: structlog logger instance
        action: Action name (e.g., "login", "spin", "bet")
        user_id: User ID
        **kwargs: Additional context
    """
    logger.info(
        "user_action",
        action=action,
        user_id=user_id,
        **kwargs
    )


def log_game_event(logger, game_type, event, user_id, **kwargs):
    """
    Log a game-related event.

    Args:
        logger: structlog logger instance
        game_type: Type of game (blackjack, roulette, slots)
        event: Event name (e.g., "game_start", "game_end", "bet_placed")
        user_id: User ID
        **kwargs: Additional context (amount, result, etc.)
    """
    logger.info(
        "game_event",
        game_type=game_type,
        event=event,
        user_id=user_id,
        **kwargs
    )


def log_error(logger, error_type, error_message, **kwargs):
    """
    Log an error with structured context.

    Args:
        logger: structlog logger instance
        error_type: Type of error
        error_message: Error message
        **kwargs: Additional context
    """
    logger.error(
        "error_occurred",
        error_type=error_type,
        error_message=str(error_message),
        **kwargs
    )


def log_security_event(logger, event_type, user_id=None, ip_address=None, **kwargs):
    """
    Log a security-related event.

    Args:
        logger: structlog logger instance
        event_type: Type of security event (e.g., "failed_login", "rate_limit_exceeded")
        user_id: User ID (if applicable)
        ip_address: IP address
        **kwargs: Additional context
    """
    logger.warning(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        **kwargs
    )

"""
Flask middleware for request tracking and logging (Month 2).

This module provides middleware for adding request IDs to all requests
and logging request/response information.
"""

import uuid
import time
import structlog
from flask import request, g
from functools import wraps


def add_request_id_middleware(app):
    """
    Add request ID middleware to Flask app.

    This middleware:
    1. Generates a unique request ID for each request
    2. Adds the request ID to Flask's g object
    3. Adds the request ID to response headers
    4. Binds the request ID to structlog context

    Args:
        app: Flask application instance
    """
    logger = structlog.get_logger()

    @app.before_request
    def before_request():
        """Execute before each request."""
        # Generate or extract request ID
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        g.start_time = time.time()

        # Bind request context to structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=g.request_id,
            ip=request.remote_addr,
            method=request.method,
            path=request.path,
            user_agent=request.headers.get('User-Agent', 'Unknown')[:100]  # Limit length
        )

        # Log request start (excluding health checks and static files)
        if not request.path.startswith(('/health', '/static', '/favicon')):
            logger.debug(
                "request_received",
                method=request.method,
                path=request.path,
                query_string=request.query_string.decode('utf-8') if request.query_string else None
            )

    @app.after_request
    def after_request(response):
        """Execute after each request."""
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')

        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000

            # Log request completion (excluding health checks and static files)
            if not request.path.startswith(('/health', '/static', '/favicon')):
                logger.info(
                    "request_completed",
                    method=request.method,
                    path=request.path,
                    status_code=response.status_code,
                    duration_ms=round(duration_ms, 2)
                )

        return response

    logger.info("request_id_middleware_configured")


def add_error_logging_middleware(app):
    """
    Add error logging middleware to Flask app.

    This middleware logs all exceptions with full context.

    Args:
        app: Flask application instance
    """
    logger = structlog.get_logger()

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all exceptions with structured logging."""
        logger.error(
            "unhandled_exception",
            error_type=type(error).__name__,
            error_message=str(error),
            path=request.path if request else None,
            method=request.method if request else None,
            exc_info=True
        )

        # Re-raise to let Flask's error handlers deal with it
        raise

    logger.info("error_logging_middleware_configured")


def request_timing_decorator(f):
    """
    Decorator to log function execution time.

    Usage:
        @request_timing_decorator
        def my_function():
            # ... code ...

    Args:
        f: Function to wrap

    Returns:
        Wrapped function that logs execution time
    """
    logger = structlog.get_logger()

    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = f.__name__

        logger.debug("function_start", function=function_name)

        try:
            result = f(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            logger.debug(
                "function_end",
                function=function_name,
                duration_ms=round(duration_ms, 2),
                success=True
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                "function_error",
                function=function_name,
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e)
            )

            raise

    return wrapper


def log_user_activity(action_type):
    """
    Decorator to log user actions on endpoints.

    Usage:
        @app.route('/spin', methods=['POST'])
        @token_required
        @log_user_activity('slot_spin')
        def spin(current_user):
            # ... code ...

    Args:
        action_type: Type of action being logged

    Returns:
        Decorator function
    """
    logger = structlog.get_logger()

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Extract user from kwargs (injected by token_required decorator)
            current_user = kwargs.get('current_user') or (args[0] if args else None)

            user_id = current_user.id if current_user and hasattr(current_user, 'id') else None
            username = current_user.username if current_user and hasattr(current_user, 'username') else None

            logger.info(
                "user_activity",
                action=action_type,
                user_id=user_id,
                username=username
            )

            return f(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitLogger:
    """
    Logger for rate limit events.

    This class provides methods to log rate limit hits and violations.
    """

    def __init__(self):
        self.logger = structlog.get_logger()

    def log_rate_limit_hit(self, endpoint, limit, user_id=None):
        """
        Log when a rate limit is approaching.

        Args:
            endpoint: Endpoint that was rate limited
            limit: Rate limit that was hit
            user_id: User ID (if applicable)
        """
        self.logger.warning(
            "rate_limit_approaching",
            endpoint=endpoint,
            limit=limit,
            user_id=user_id,
            ip=request.remote_addr if request else None
        )

    def log_rate_limit_exceeded(self, endpoint, limit, user_id=None):
        """
        Log when a rate limit is exceeded.

        Args:
            endpoint: Endpoint that exceeded rate limit
            limit: Rate limit that was exceeded
            user_id: User ID (if applicable)
        """
        self.logger.warning(
            "rate_limit_exceeded",
            endpoint=endpoint,
            limit=limit,
            user_id=user_id,
            ip=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', 'Unknown')[:100]
        )


# Global rate limit logger instance
rate_limit_logger = RateLimitLogger()


def add_security_logging_middleware(app):
    """
    Add security event logging middleware.

    Logs suspicious activities and security events.

    Args:
        app: Flask application instance
    """
    logger = structlog.get_logger()

    @app.before_request
    def log_suspicious_activity():
        """Log potentially suspicious request patterns."""
        # Log requests with suspicious user agents
        user_agent = request.headers.get('User-Agent', '')
        suspicious_keywords = ['sqlmap', 'nikto', 'nmap', 'masscan', 'bot', 'crawler']

        if any(keyword in user_agent.lower() for keyword in suspicious_keywords):
            logger.warning(
                "suspicious_user_agent",
                user_agent=user_agent[:200],
                ip=request.remote_addr,
                path=request.path
            )

        # Log requests with suspicious paths
        suspicious_paths = ['../', '.env', 'admin', 'phpmyadmin', 'wp-admin']
        if any(path in request.path.lower() for path in suspicious_paths):
            logger.warning(
                "suspicious_path_access",
                path=request.path,
                ip=request.remote_addr,
                user_agent=user_agent[:100]
            )

    logger.info("security_logging_middleware_configured")

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .utils.config import Config  # Use relative import
import logging
import os
from flask_cors import CORS
from flask_session import Session  # Import Flask-Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

app = Flask(__name__)
app.config.from_object(Config)

# Set up logging based on environment
log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s %(name)s : %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Reduce verbose logging from werkzeug in production
if app.config.get('LOG_LEVEL') != 'DEBUG':
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

Session(app)  # Initialize Flask-Session

# Configure CORS with specific origins
CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}}, supports_credentials=True)

# Configure rate limiting with Redis (or memory in development)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config.get('RATELIMIT_STORAGE_URL'),
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",  # Options: "fixed-window", "moving-window"
    headers_enabled=True,  # Add rate limit headers to responses
    swallow_errors=True  # Don't crash if Redis is unavailable
)

# Log rate limiting configuration
logging.info(f"Rate limiting configured with storage: {app.config.get('RATELIMIT_STORAGE_URL')}")

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Migrate
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all HTTP responses"""
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Enable XSS protection in older browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Strict Transport Security (only in production with HTTPS)
    if app.config.get('SESSION_COOKIE_SECURE'):
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Content Security Policy
    # Note: 'unsafe-inline' for styles is kept for compatibility with Materialize CSS and inline styles.
    # If you can refactor all inline styles, remove 'unsafe-inline' from style-src.
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"

    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions Policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    return response

from . import routes  # Use relative imports
from .utils import models

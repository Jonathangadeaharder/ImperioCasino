import os
import secrets

class Config:
    # Secret key - MUST be set in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Only use generated key in development
        if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('FASTAPI_ENV') == 'production':
            raise ValueError("SECRET_KEY environment variable must be set in production")
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY env var in production!")

    # JWT Configuration
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 12

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app.db'
    DATABASE_URL = SQLALCHEMY_DATABASE_URI  # FastAPI compatible
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
    }

    # Game URLs - use environment variables
    CHERRY_CHARM_URL = os.environ.get('CHERRY_CHARM_URL', 'http://localhost:5173')
    BLACK_JACK_URL = os.environ.get('BLACK_JACK_URL', 'http://localhost:5174')
    ROULETTE_URL = os.environ.get('ROULETTE_URL', 'http://localhost:5175')

    # CORS allowed origins
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5174,http://localhost:5175').split(',')

    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')


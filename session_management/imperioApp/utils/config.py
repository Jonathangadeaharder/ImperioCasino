import os
import secrets

class Config:
    # Secret key - MUST be set in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Only use generated key in development
        if os.environ.get('FLASK_ENV') == 'production':
            raise ValueError("SECRET_KEY environment variable must be set in production")
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY env var in production!")

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Determine if we're using PostgreSQL
    is_postgres = SQLALCHEMY_DATABASE_URI.startswith('postgresql')

    # SQLAlchemy engine options
    engine_options = {
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # Recycle connections after 1 hour
    }

    # PostgreSQL-specific configuration
    if is_postgres:
        engine_options.update({
            'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),  # Larger pool for PostgreSQL
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 10)),  # Extra connections if pool is full
            'pool_timeout': 30,  # Timeout for getting connection from pool
            'connect_args': {
                'connect_timeout': 10,  # Connection timeout in seconds
                'options': '-c statement_timeout=30000',  # Statement timeout (30 seconds)
            }
        })
    else:
        # SQLite configuration - simpler options for testing/development
        engine_options = {
            'connect_args': {
                'check_same_thread': False,  # Allow SQLite to be used across threads
            }
        }

    SQLALCHEMY_ENGINE_OPTIONS = engine_options

    # Redis configuration for rate limiting and caching
    REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))

    # Build Redis URL
    if REDIS_PASSWORD:
        REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    else:
        REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # Rate limiter storage - use Redis in production, memory in development
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', REDIS_URL if os.environ.get('FLASK_ENV') == 'production' else 'memory://')
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() == 'true'

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

    # Caching configuration (Month 5)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'RedisCache' if os.environ.get('FLASK_ENV') == 'production' else 'SimpleCache')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))  # 5 minutes
    CACHE_KEY_PREFIX = 'imperiocasino_'


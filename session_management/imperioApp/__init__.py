"""
ImperioApp package initialization for FastAPI
Provides backward compatibility with Flask imports
"""
# Import the Flask compatibility layer
from .flask_compat import db

# Import FastAPI database setup
from .database import Base, engine, get_db

# Make db available for imports
__all__ = ['db', 'Base', 'engine', 'get_db']


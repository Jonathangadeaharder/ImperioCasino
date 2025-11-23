"""
Flask DB compatibility layer for FastAPI
Provides Flask's db.session interface using FastAPI's SessionLocal
"""
from .database import SessionLocal


class FlaskDBCompatibility:
    """
    Compatibility layer that mimics Flask-SQLAlchemy's db object
    This allows the existing game logic to work with FastAPI without modification
    """
    
    def __init__(self):
        self._session = None
    
    @property
    def session(self):
        """Lazy initialization of session"""
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    def init_session(self):
        """Initialize a new session (for use with context managers)"""
        self._session = SessionLocal()
        return self._session
    
    def set_session(self, session):
        """Set an existing session (for use with FastAPI dependency injection)"""
        self._session = session
    
    def close_session(self):
        """Close the current session"""
        if self._session:
            self._session.close()
            self._session = None
    
    def commit_session(self):
        """Commit the current session"""
        if self._session:
            self._session.commit()
    
    def rollback_session(self):
        """Rollback the current session"""
        if self._session:
            self._session.rollback()


# Global instance that can be imported by game logic
db = FlaskDBCompatibility()

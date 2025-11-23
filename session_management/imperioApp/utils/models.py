"""
Models compatibility layer
Re-exports FastAPI models for backward compatibility with Flask code
"""
# Import FastAPI models
from .models_fastapi import User, BlackjackGameState

# For backward compatibility, also support Flask-style model usage
__all__ = ['User', 'BlackjackGameState']


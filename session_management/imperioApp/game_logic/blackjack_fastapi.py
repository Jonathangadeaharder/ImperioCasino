"""
Blackjack game logic adapter for FastAPI
Wraps the original game logic to work with FastAPI by providing db.session compatibility
"""
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..utils.models_fastapi import User, BlackjackGameState
import logging

class DBSessionWrapper:
    """Wrapper to make SessionLocal compatible with Flask's db.session pattern"""
    def __init__(self):
        self._session = None
    
    def __enter__(self):
        self._session = SessionLocal()
        return self._session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            if exc_type:
                self._session.rollback()
            self._session.close()
    
    def query(self, *args, **kwargs):
        if not self._session:
            self._session = SessionLocal()
        return self._session.query(*args, **kwargs)
    
    def add(self, *args, **kwargs):
        if not self._session:
            self._session = SessionLocal()
        return self._session.add(*args, **kwargs)
    
    def commit(self):
        if not self._session:
            return
        return self._session.commit()
    
    def rollback(self):
        if not self._session:
            return
        return self._session.rollback()
    
    def refresh(self, *args, **kwargs):
        if not self._session:
            self._session = SessionLocal()
        return self._session.refresh(*args, **kwargs)


# Monkey-patch to make the blackjack module work
import sys
from types import ModuleType

# Create a mock imperioApp module if it doesn't exist in the expected form
class MockImperioApp(ModuleType):
    def __init__(self):
        super().__init__('mock_imperioApp')
        self.db = MockDB()

class MockDB:
    def __init__(self):
        self.session = DBSessionWrapper()


def start_game(user, wager):
    """Adapter for starting a blackjack game"""
    # Import the original function and inject our db
    from . import blackjack as bj_module
    
    # Temporarily replace db with our wrapper
    original_db = getattr(bj_module, 'db', None)
    bj_module.db = MockDB()
    
    try:
        result = bj_module.start_game(user, wager)
        return result
    finally:
        if original_db:
            bj_module.db = original_db


def player_action(user, action, game_id=None):
    """Adapter for blackjack player actions"""
    from . import blackjack as bj_module
    
    # Temporarily replace db with our wrapper
    original_db = getattr(bj_module, 'db', None)
    bj_module.db = MockDB()
    
    try:
        result = bj_module.player_action(user, action, game_id)
        return result
    finally:
        if original_db:
            bj_module.db = original_db

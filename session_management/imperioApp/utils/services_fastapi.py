"""
Services adapter for FastAPI
Provides database operations without requiring Flask's db context
"""
from typing import Optional
from ..database import SessionLocal
from .models_fastapi import User
import logging

logging.basicConfig(level=logging.DEBUG)


def get_db_session():
    """Get a database session"""
    return SessionLocal()


def get_user_by_username(username: str) -> Optional[User]:
    """
    Get a user by username
    
    Args:
        username: The username to search for
        
    Returns:
        User object if found, None otherwise
    """
    db = get_db_session()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logging.warning(f"User {username} not found in database")
        else:
            logging.debug(f"User {username} retrieved successfully from database")
        return user
    finally:
        db.close()


def create_user(username: str, email: str, password: str, starting_coins: Optional[int] = None) -> User:
    """
    Create a new user
    
    Args:
        username: Username for the new user
        email: Email for the new user
        password: Password for the new user
        starting_coins: Optional starting coin amount
        
    Returns:
        Created User object
    """
    db = get_db_session()
    try:
        user = User(
            username=username,
            email=email,
            coins=starting_coins
        )
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def update_user_coins(user: User, coins: int):
    """
    Update user's coin balance
    
    Args:
        user: User object to update
        coins: New coin balance
    """
    db = get_db_session()
    try:
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            db_user.coins = coins
            db.commit()
            # Update the passed user object to reflect changes
            user.coins = coins
    finally:
        db.close()


def increase_user_coins(user: User, amount: int):
    """
    Increase user's coin balance
    
    Args:
        user: User object to update
        amount: Amount to increase coins by
    """
    db = get_db_session()
    try:
        db_user = db.query(User).filter(User.id == user.id).first()
        if db_user:
            db_user.coins += amount
            db.commit()
            # Update the passed user object to reflect changes
            user.coins = db_user.coins
    finally:
        db.close()


def reduce_user_coins(user: User, amount: int):
    """
    Reduce user's coin balance
    
    Args:
        user: User object to update
        amount: Amount to reduce coins by
    """
    increase_user_coins(user, -amount)

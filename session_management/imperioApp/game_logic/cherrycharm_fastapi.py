"""
Cherry Charm game logic adapter for FastAPI
Wraps the original game logic to work with FastAPI
"""
import logging
from ..database import SessionLocal
from .models_fastapi import User


def cherryAction(spin_user: User):
    """
    Adapter for Cherry Charm spin action
    Makes the Flask game logic compatible with FastAPI
    
    Args:
        spin_user: User object from FastAPI
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    from .cherrycharm import spin_reels, get_fruits, calculate_winnings
    
    db = SessionLocal()
    try:
        logging.debug("Received spin request for user_id: %s", spin_user.username)
        
        # Lock user row for update to prevent race conditions
        locked_user = db.query(User).with_for_update().filter_by(id=spin_user.id).first()
        
        if not locked_user:
            return {'message': 'User not found'}, 404
        
        # Check if the user has enough coins to spin
        if locked_user.coins < 1:
            logging.warning("User %s does not have enough coins to spin.", locked_user.username)
            return {'message': 'Not enough coins to spin'}, 400
        
        # Deduct a coin for spinning
        locked_user.coins -= 1
        logging.info("User %s has spun the slot machine. Coins left: %s", locked_user.username, locked_user.coins)
        
        # Generate stop segments and fruits
        stop_segments = spin_reels()
        logging.info("Generated stop segments for user %s: %s", locked_user.username, stop_segments)
        fruits = get_fruits(stop_segments)
        logging.info("Fruits for user %s: %s", locked_user.username, fruits)
        
        # Compute winnings
        winnings = calculate_winnings(fruits)
        logging.info("User %s won: %s coins", locked_user.username, winnings)
        
        # Add winnings to user's coins
        locked_user.coins += winnings
        logging.info("User %s new coin balance: %s", locked_user.username, locked_user.coins)
        
        db.commit()
        
        # Update the original user object
        spin_user.coins = locked_user.coins
        
        # Prepare the response data
        response_data = {
            'stopSegments': stop_segments,
            'totalCoins': locked_user.coins
        }
        return response_data, 200
        
    finally:
        db.close()

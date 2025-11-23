"""
Games API routes for FastAPI
Migrated from Flask routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from ..database import get_db
from ..utils.auth_fastapi import get_current_user
from ..utils.models_fastapi import User

router = APIRouter()


# Pydantic models for game requests
class SpinRequest(BaseModel):
    pass  # Cherry charm spin doesn't need additional data


class BlackjackStartRequest(BaseModel):
    wager: int


class BlackjackActionRequest(BaseModel):
    action: str
    game_id: Optional[int] = None


class RouletteActionRequest(BaseModel):
    pass  # Will be populated from request body


# Helper function to execute game logic with proper session management
def execute_with_flask_compat(func, *args, **kwargs):
    """Execute a game logic function with Flask compatibility layer"""
    from ..flask_compat import db as compat_db
    
    # Initialize session
    compat_db.init_session()
    
    try:
        result = func(*args, **kwargs)
        compat_db.commit_session()
        return result
    except Exception as e:
        compat_db.rollback_session()
        logging.error(f"Error in game logic: {e}", exc_info=True)
        raise
    finally:
        compat_db.close_session()


# Cherry Charm (Spin) route
@router.post("/spin")
async def spin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a spin in Cherry Charm slot machine"""
    from ..game_logic.cherrycharm import spin_reels, get_fruits, calculate_winnings
    
    logging.debug("Received spin request for user_id: %s", current_user.username)
    
    # Lock user row for update
    locked_user = db.query(User).with_for_update().filter_by(id=current_user.id).first()
    
    if not locked_user:
        raise HTTPException(status_code=404, detail='User not found')
    
    if locked_user.coins < 1:
        logging.warning("User %s does not have enough coins to spin.", locked_user.username)
        raise HTTPException(status_code=400, detail='Not enough coins to spin')
    
    # Deduct coin
    locked_user.coins -= 1
    logging.info("User %s has spun. Coins left: %s", locked_user.username, locked_user.coins)
    
    # Generate results
    stop_segments = spin_reels()
    fruits = get_fruits(stop_segments)
    winnings = calculate_winnings(fruits)
    
    # Add winnings
    locked_user.coins += winnings
    logging.info("User %s won: %s coins. New balance: %s", locked_user.username, winnings, locked_user.coins)
    
    db.commit()
    db.refresh(locked_user)
    
    return {
        'stopSegments': stop_segments,
        'totalCoins': locked_user.coins
    }


# Blackjack routes
@router.post("/blackjack/start")
async def start_blackjack_game(
    game_request: BlackjackStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new blackjack game"""
    if game_request.wager is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wager is required"
        )
    
    # Use Flask compatibility layer for game logic
    from ..game_logic import blackjack
    from ..flask_compat import db as compat_db
    
    # Temporarily set the compat db's session to our FastAPI session
    compat_db._session = db
    
    try:
        game_state, status_code = blackjack.start_game(current_user, game_request.wager)
        
        logging.debug(f"Start Blackjack Game - Game State: {game_state.get('player_hand', 'N/A')}")
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=game_state.get("message", "Error"))
        
        return game_state
    finally:
        # Don't close the session as it's managed by FastAPI
        compat_db._session = None


@router.post("/blackjack/action")
async def blackjack_action(
    action_request: BlackjackActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a blackjack action (hit, stand, double down, split)"""
    if action_request.action is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action is required"
        )
    
    # Use Flask compatibility layer for game logic
    from ..game_logic import blackjack
    from ..flask_compat import db as compat_db
    
    # Temporarily set the compat db's session to our FastAPI session
    compat_db._session = db
    
    try:
        result, status_code = blackjack.player_action(
            current_user,
            action_request.action,
            action_request.game_id
        )
        
        logging.debug(f"Blackjack Action - Result: {result.get('player_hand', 'N/A')}")
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=result.get("message", "Error"))
        
        return result
    finally:
        # Don't close the session as it's managed by FastAPI
        compat_db._session = None


# Roulette route
@router.post("/roulette/action")
async def roulette_action(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a roulette action"""
    # Get the JSON data from the request
    data = await request.json()
    
    logging.debug(f"Roulette action data: {data}")
    
    # Use Flask compatibility layer for game logic
    from ..game_logic import roulette
    from ..flask_compat import db as compat_db
    
    # Temporarily set the compat db's session to our FastAPI session
    compat_db._session = db
    
    try:
        result, status_code = roulette.rouletteAction(current_user, data)
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=result.get("message", "Error"))
        
        return result
    finally:
        # Don't close the session as it's managed by FastAPI
        compat_db._session = None


"""
Coins API routes for FastAPI
Migrated from Flask routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from ..database import get_db
from ..utils.auth_fastapi import get_current_user
from ..utils.models_fastapi import User

router = APIRouter()


class CoinsUpdate(BaseModel):
    coins: int


@router.get("/getCoins")
async def get_coins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's coin balance"""
    logging.debug(f"Received getCoins request for user_id: {current_user.username} with coins: {current_user.coins}")
    return {"coins": current_user.coins}


@router.post("/updateCoins")
async def update_coins(
    coins_data: CoinsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the current user's coin balance"""
    logging.debug(f"Received updateCoins request for user_id: {current_user.username} with coins: {coins_data.coins}")
    
    if coins_data.coins is None:
        logging.warning("Coins are missing in updateCoins request.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coins are required"
        )
    
    # Update coins
    current_user.coins = coins_data.coins
    db.commit()
    db.refresh(current_user)
    
    logging.info(f"Coins successfully updated for user_id: {current_user.username} to {coins_data.coins} coins")
    return {"message": "Coins updated successfully"}

"""
User models for FastAPI-Users
Compatible with SQLite async database
"""
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index, PickleType
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.mutable import MutableList
from ..database import Base
from .constants import DEFAULT_COINS


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model compatible with FastAPI-Users"""
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_username_users', 'username'),
    )
    
    # FastAPI-Users required fields are inherited from SQLAlchemyBaseUserTableUUID
    # id (UUID primary key)
    # email (String, unique, indexed)
    # hashed_password (String)
    # is_active (Boolean)
    # is_superuser (Boolean)
    # is_verified (Boolean)
    
    # Additional custom fields
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    coins: Mapped[int] = mapped_column(Integer, nullable=False, default=DEFAULT_COINS)
    
    # Relationships
    blackjack_games = relationship("BlackjackGameState", back_populates="user")

    def __repr__(self):
        return f'<User {self.username}>'


class BlackjackGameState(Base):
    """Blackjack game state model"""
    __tablename__ = 'blackjack_game_state'
    __table_args__ = (
        Index('idx_user_game_state', 'user_id', 'game_over'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)  # UUID as string
    deck = Column(MutableList.as_mutable(PickleType), nullable=False)
    dealer_hand = Column(MutableList.as_mutable(PickleType), nullable=False)
    player_hand = Column(MutableList.as_mutable(PickleType), nullable=False)
    player_second_hand = Column(MutableList.as_mutable(PickleType), nullable=True)
    player_coins = Column(Integer, nullable=False)
    current_wager = Column(Integer, nullable=False)
    game_over = Column(Boolean, default=False)
    message = Column(String(255), default='')
    player_stood = Column(Boolean, default=False)
    double_down = Column(Boolean, default=False)
    split = Column(Boolean, default=False)
    current_hand = Column(String(10), default='first')
    dealer_value = Column(Integer, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="blackjack_games")

    def to_dict(self):
        """Convert game state to dictionary"""
        # Determine if player can double down
        can_double_down = (
            not self.game_over and 
            len(self.player_hand) == 2 and 
            not self.double_down and 
            not self.split and 
            not self.player_stood
        )
        
        # Determine if player can split
        can_split = (
            not self.game_over and
            not self.split and
            len(self.player_hand) == 2 and
            self.player_hand[0]['value'] == self.player_hand[1]['value']
        )
        
        return {
            'id': self.id,
            'user_id': str(self.user_id),
            'deck': self.deck,
            'dealer_hand': self.dealer_hand,
            'player_hand': self.player_hand,
            'player_coins': self.player_coins,
            'current_wager': self.current_wager,
            'game_over': self.game_over,
            'message': self.message,
            'player_stood': self.player_stood,
            'double_down': self.double_down,
            'split': self.split,
            'player_second_hand': self.player_second_hand,
            'current_hand': self.current_hand,
            'dealer_value': self.dealer_value,
            'can_double_down': can_double_down,
            'can_split': can_split
        }

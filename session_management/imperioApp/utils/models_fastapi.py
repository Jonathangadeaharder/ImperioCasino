"""
Database models for FastAPI
Migrated from Flask-SQLAlchemy to SQLAlchemy 2.0
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Index, PickleType
from sqlalchemy.orm import relationship
from passlib.hash import bcrypt
from ..database import Base
from .constants import DEFAULT_COINS
from sqlalchemy.ext.mutable import MutableList


class BlackjackGameState(Base):
    """Blackjack game state model"""
    __tablename__ = 'blackjack_game_state'
    __table_args__ = (
        Index('idx_user_game_state', 'user_id', 'game_over'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
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
            'user_id': self.user_id,
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


class User(Base):
    """User model"""
    __tablename__ = 'users'
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=True)
    coins = Column(Integer, nullable=False, default=DEFAULT_COINS)
    
    # Relationships
    blackjack_games = relationship("BlackjackGameState", back_populates="user")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.coins is None:
            self.coins = DEFAULT_COINS

    def set_password(self, password: str):
        """Hash and set the user's password"""
        self.password = bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify the user's password"""
        if not self.password:
            return False
        return bcrypt.verify(password, self.password)

    def __repr__(self):
        return f'<User {self.username}>'

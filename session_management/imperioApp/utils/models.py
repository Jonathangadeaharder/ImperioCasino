from sqlalchemy import PickleType
from .. import db, login_manager  # Relative imports
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .constants import DEFAULT_COINS  # Import DEFAULT_COINS
from sqlalchemy.ext.mutable import MutableList

class BlackjackGameState(db.Model):
    __tablename__ = 'blackjack_game_state'
    __table_args__ = (
        db.Index('idx_user_game_state', 'user_id', 'game_over'),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    deck = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    dealer_hand = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    player_hand = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    player_second_hand = db.Column(MutableList.as_mutable(PickleType), nullable=True)
    player_coins = db.Column(db.Integer, nullable=False)
    current_wager = db.Column(db.Integer, nullable=False)
    game_over = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(255), default='')
    player_stood = db.Column(db.Boolean, default=False)
    double_down = db.Column(db.Boolean, default=False)
    split = db.Column(db.Boolean, default=False)
    current_hand = db.Column(db.String(10), default='first')
    dealer_value = db.Column(db.Integer, nullable=True)  # **New Column Added**

    def to_dict(self):
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
            'dealer_value': self.dealer_value,  # Ensure this is included
            'can_double_down': can_double_down,
            'can_split': can_split
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('idx_username', 'username'),
        db.Index('idx_email', 'email'),
    )
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=True)
    coins = db.Column(db.Integer, nullable=False)  # Remove default here

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.coins is None:
            self.coins = DEFAULT_COINS  # Use DEFAULT_COINS here

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

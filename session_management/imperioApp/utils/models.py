from sqlalchemy import PickleType

from .. import db, login_manager  # Relative imports
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .constants import DEFAULT_COINS  # Import DEFAULT_COINS
from sqlalchemy.ext.mutable import MutableList

class BlackjackGameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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

    def to_dict(self):
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
            'current_hand': self.current_hand
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    coins = db.Column(db.Integer, nullable=False)  # Remove default here

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.coins is None:
            self.coins = DEFAULT_COINS  # Use DEFAULT_COINS here

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from .. import db, login_manager  # Relative imports
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .constants import DEFAULT_COINS  # Import DEFAULT_COINS

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

from .models import User
from .. import db
import logging

logging.basicConfig(level=logging.DEBUG)

def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        logging.warning(f"User {username} not found in database")
    else:
        logging.debug(f"User {username} retrieved successfully from database")
    return user
def create_user(username, email, password, starting_coins=None):
    user = User(
        username=username,
        email=email,
        coins=starting_coins  # This can be None; User.__init__ will handle it
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user

def update_user_coins(user, coins):
    user.coins = coins
    db.session.commit()

def increase_user_coins(user, amount):
    user.coins += amount
    db.session.commit()

def reduce_user_coins(user, amount):
    increase_user_coins(user, -amount)


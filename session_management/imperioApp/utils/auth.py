import jwt
from datetime import datetime, timedelta, timezone
from flask import session, current_app
from functools import wraps
from flask import request, jsonify
from .models import User

def generate_token(user_id):
    token = jwt.encode(
        {'user_id': user_id, 'exp': datetime.now(timezone.utc) + timedelta(hours=12)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token

def decode_token(token):
    return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])

def login_user_session(user, remember=False):
    from flask_login import login_user
    login_user(user, remember=remember)
    token = generate_token(user.username)
    session['token'] = token
    session['username'] = user.username

def logout_user_session():
    from flask_login import logout_user
    logout_user()
    session.pop('token', None)
    session.pop('username', None)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Retrieve the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            decoded_token = decode_token(token)
            current_user = User.query.filter_by(username=decoded_token['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found'}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

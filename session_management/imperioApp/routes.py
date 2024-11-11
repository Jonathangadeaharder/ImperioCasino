import random

from flask import render_template, flash, redirect, url_for, request, jsonify, session
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from . import app, db
from .forms import LoginForm, RegistrationForm
from .models import User
import jwt
import datetime
import logging
from .cherrycharm import endgame,segment_to_fruit
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)

        # Generate JWT token
        token = jwt.encode(
            {'user_id': user.username, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        # Store token in session
        session['token'] = token
        session['username'] = user.username

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    session.pop('token', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or email already exists')
            return redirect(url_for('signup'))

        # Create new user with starting coins
        user = User(
            username=form.username.data,
            email=form.email.data,
            coins=100  # Assign starting coins here
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Register', form=form)

@app.route('/redirect-imperio')
@login_required
def redirect_to_imperio():
    username = current_user.username
    token = session.get('token')
    if not token:
        # Generate a new token if not present
        token = jwt.encode(
            {'user_id': current_user.username, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=12)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        session['token'] = token
    return redirect(f"{app.config['CHERRY_CHARM_URL']}/?username={username}&token={token}")

@app.route('/verify-token', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get('token')
    username = data.get('username')

    if not token or not username:
        return jsonify({'message': 'Token and username are required'}), 400

    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.filter_by(username=decoded_token['user_id']).first()

        if user:
            return jsonify({'message': 'Token is valid'}), 200
        else:
            return jsonify({'message': 'Invalid token or username'}), 401

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/getCoins', methods=['GET'])
def get_coins():
    user_id = request.args.get('userId')
    logging.debug("Received getCoins request for user_id: %s", user_id)
    token = request.headers.get('Authorization').split(" ")[1] if request.headers.get('Authorization') else None

    if not user_id or not token:
        logging.warning("User ID or token is missing in getCoins request.")
        return jsonify({'message': 'User ID and token are required'}), 400

    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        if str(decoded_token['user_id']) != user_id:
            logging.debug(decoded_token['user_id'])
            logging.warning("Unauthorized access attempt for user_id: %s", user_id)
            return jsonify({'message': 'Unauthorized access'}), 401

        user = User.query.filter_by(username=user_id).first()
        if not user:
            logging.error("User not found for user_id: %s", user_id)
            return jsonify({'message': 'User not found'}), 404

        logging.info("Successfully retrieved coins for user_id: %s", user_id)
        return jsonify({'coins': user.coins}), 200

    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired for user_id: %s", user_id)
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        logging.error("Invalid token received for user_id: %s", user_id)
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/updateCoins', methods=['POST'])
def update_coins():
    data = request.get_json()
    user_id = data.get('userId')
    coins = data.get('coins')
    logging.debug("Received updateCoins request for user_id: %s with coins: %s", user_id, coins)
    token = request.headers.get('Authorization').split(" ")[1] if request.headers.get('Authorization') else None

    if not user_id or coins is None or not token:
        logging.warning("User ID, coins, or token is missing in updateCoins request.")
        return jsonify({'message': 'User ID, coins, and token are required'}), 400

    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        if str(decoded_token['user_id']) != user_id:
            logging.warning("Unauthorized update attempt for user_id: %s", user_id)
            return jsonify({'message': 'Unauthorized access'}), 401

        user = User.query.filter_by(username=user_id).first()
        if not user:
            logging.error("User not found for user_id: %s", user_id)
            return jsonify({'message': 'User not found'}), 404

        user.coins = coins
        db.session.commit()
        logging.info("Coins successfully updated for user_id: %s to %s coins", user_id, coins)
        return jsonify({'message': 'Coins updated successfully'}), 200

    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired for user_id: %s", user_id)
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        logging.error("Invalid token received for user_id: %s", user_id)
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/spin', methods=['POST'])
def spin():
    data = request.get_json()
    user_id = data.get('userId')
    logging.debug("Received spin request for user_id: %s", user_id)

    # Retrieve the token from the Authorization header
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(" ")[1] if auth_header else None

    if not user_id or not token:
        logging.warning("User ID or token is missing in spin request.")
        return jsonify({'message': 'User ID and token are required'}), 400

    try:
        # Decode and verify the JWT token
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])

        # Check if the token's user_id matches the provided user_id
        if str(decoded_token['user_id']) != user_id:
            logging.warning("Unauthorized spin attempt for user_id: %s", user_id)
            return jsonify({'message': 'Unauthorized access'}), 401

        # Fetch the user from the database
        user = User.query.filter_by(username=user_id).first()
        if not user:
            logging.error("User not found for user_id: %s", user_id)
            return jsonify({'message': 'User not found'}), 404

        # Check if the user has enough coins to spin
        # Each spin costs 1 coin
        if user.coins < 1:
            logging.warning("User %s does not have enough coins to spin.", user_id)
            return jsonify({'message': 'Not enough coins to spin'}), 400

        # Deduct a coin for spinning
        user.coins -= 1
        db.session.commit()
        logging.info("User %s has spun the slot machine. Coins left: %s", user_id, user.coins)

        # Generate random stop segments between 15 and 30 inclusive
        MIN_SEGMENT = 15
        MAX_SEGMENT = 30
        stop_segments = [random.randint(MIN_SEGMENT, MAX_SEGMENT) for _ in range(3)]
        logging.info("Generated stop segments for user %s: %s", user_id, stop_segments)

        # Convert stop_segments to fruits
        fruits = [segment_to_fruit(reel, segment) for reel, segment in enumerate(stop_segments)]
        logging.info("Fruits for user %s: %s", user_id, fruits)

        # Compute winnings
        winnings = endgame(*fruits)
        logging.info("User %s won: %s coins", user_id, winnings)

        # Add winnings to user's coins
        user.coins += winnings
        db.session.commit()
        logging.info("User %s new coin balance: %s", user_id, user.coins)

        # Prepare the response data
        response_data = {
            'stopSegments': stop_segments,
            'totalCoins': user.coins
        }

        return jsonify(response_data), 200

    except jwt.ExpiredSignatureError:
        logging.warning("Token has expired for user_id: %s", user_id)
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        logging.error("Invalid token received for user_id: %s", user_id)
        return jsonify({'message': 'Invalid token'}), 401
    except Exception as e:
        logging.error("An error occurred during spin for user_id: %s. Error: %s", user_id, str(e))
        return jsonify({'message': 'An internal error occurred'}), 500
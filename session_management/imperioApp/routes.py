import jwt
from flask import render_template, flash, redirect, url_for, request, jsonify, session
from flask_login import current_user, login_required
from urllib.parse import urlparse
from . import app
from .utils.forms import LoginForm, RegistrationForm
from .utils.models import User
import logging

# Import the new modules
from .utils.auth import generate_token, login_user_session, logout_user_session, token_required
from .utils.services import (
    get_user_by_username,
    create_user,
    update_user_coins
)
from .game_logic.cherrycharm import executeSpin
from .game_logic.blackjack import start_game, player_action

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
        user = get_user_by_username(form.username.data)
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user_session(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user_session()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = get_user_by_username(form.username.data)
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_user or existing_email:
            flash('Username or email already exists')
            return redirect(url_for('signup'))

        create_user(form.username.data, form.email.data, form.password.data)
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Register', form=form)

@app.route('/redirect-imperio')
@login_required
def redirect_to_imperio():
    username = current_user.username
    token = session.get('token')
    if not token:
        token = generate_token(current_user.username)
        session['token'] = token
    return redirect(f"{app.config['CHERRY_CHARM_URL']}/?username={username}&token={token}")

@app.route('/verify-token', methods=['POST'])
def verify_token():
    from session_management.imperioApp.utils.auth import decode_token
    data = request.get_json()
    token = data.get('token')
    username = data.get('username')

    if not token or not username:
        return jsonify({'message': 'Token and username are required'}), 400

    try:
        decoded_token = decode_token(token)
        user = get_user_by_username(decoded_token['user_id'])

        if user:
            return jsonify({'message': 'Token is valid'}), 200
        else:
            return jsonify({'message': 'Invalid token or username'}), 401

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

@app.route('/getCoins', methods=['GET'])
@token_required
def get_coins(current_user):
    logging.debug("Received getCoins request for user_id: %s", current_user.username)
    return jsonify({'coins': current_user.coins}), 200

@app.route('/updateCoins', methods=['POST'])
@token_required
def update_coins(current_user):
    data = request.get_json()
    coins = data.get('coins')
    logging.debug("Received updateCoins request for user_id: %s with coins: %s", current_user.username, coins)

    if coins is None:
        logging.warning("Coins are missing in updateCoins request.")
        return jsonify({'message': 'Coins are required'}), 400

    update_user_coins(current_user, coins)
    logging.info("Coins successfully updated for user_id: %s to %s coins", current_user.username, coins)
    return jsonify({'message': 'Coins updated successfully'}), 200

@app.route('/spin', methods=['POST'])
@token_required
def spin(spin_user):
    return executeSpin(spin_user)

@app.route('/blackjack', methods=['GET'])
@login_required
def blackjack():
    # Generate a token for the user
    token = session.get('token')
    if not token:
        token = generate_token(current_user.username)
        session['token'] = token
    return render_template('blackjack.html', title='Blackjack', token=token)

@app.route('/blackjack/action', methods=['POST'])
@token_required
def blackjack_action(current_user):
    data = request.get_json()
    action = data.get('action')
    wager = data.get('wager', 0)  # Get wager amount if provided

    if action == 'start':
        response = start_game(current_user, wager)
    elif action in ['hit', 'stand', 'double_down', 'split']:
        response = player_action(current_user, action)
    else:
        return jsonify({'message': 'Invalid action'}), 400

    return jsonify(response)

from flask import render_template, flash, redirect, url_for, request, jsonify, session
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from . import app, db
from .forms import LoginForm, RegistrationForm
from .models import User
import jwt
import datetime
import requests

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
            {'user_id': user.id, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
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

        # Generate JWT token for the new user
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        # Make external API call to create user
        headers = {'Authorization': f'Bearer {token}'}
        try:
            response = requests.post(
                app.config['EXTERNAL_API_URL'],
                json={'userId': user.username},
                headers=headers,
                timeout=5  # Set a timeout to prevent hanging
            )
        except requests.exceptions.RequestException as e:
            db.session.delete(user)
            db.session.commit()
            flash(f"Error connecting to external API: {str(e)}")
            return redirect(url_for('signup'))
        if response.status_code != 201:
            try:
                error_message = response.json().get('error', 'Unknown error')
            except ValueError:
                error_message = f"Non-JSON response: {response.text}"
            db.session.delete(user)
            db.session.commit()
            flash(f"Error creating user on backend: {error_message}")
            return redirect(url_for('signup'))

        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Register', form=form)

@app.route('/updateCoins', methods=['POST'])
@login_required
def update_coins():
    data = request.get_json()
    if not data or 'coins' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        coins = int(data['coins'])
        if coins < 0:
            return jsonify({'error': 'Coins cannot be negative'}), 400

        current_user.coins = coins
        db.session.commit()
        return jsonify({'message': 'Coins updated successfully'}), 200
    except ValueError:
        return jsonify({'error': 'Coins must be an integer'}), 400
    except Exception as e:
        app.logger.error(f'Error updating coins: {e}')
        return jsonify({'error': 'An error occurred while updating coins'}), 500

@app.route('/getCoins', methods=['GET'])
@login_required
def get_coins():
    try:
        return jsonify({'coins': current_user.coins}), 200
    except Exception as e:
        app.logger.error(f'Error retrieving coins: {e}')
        return jsonify({'error': 'An error occurred while retrieving coins'}), 500

@app.route('/redirect-imperio')
@login_required
def redirect_to_imperio():
    username = current_user.username
    token = session.get('token')
    if not token:
        # Generate a new token if not present
        token = jwt.encode(
            {'user_id': current_user.id, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        session['token'] = token
    return redirect(f"http://13.60.215.133:5173/?username={username}&token={token}")

@app.route('/verify-token', methods=['POST'])
def verify_token():
    data = request.get_json()
    token = data.get('token')
    username = data.get('username')

    if not token or not username:
        return jsonify({'message': 'Token and username are required'}), 400

    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user = User.query.filter_by(id=decoded_token['user_id']).first()

        if user and user.username == username:
            return jsonify({'message': 'Token is valid'}), 200
        else:
            return jsonify({'message': 'Invalid token or username'}), 401

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401

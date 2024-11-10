from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from . import app, db  # Relative imports
from .forms import LoginForm, RegistrationForm
from .models import User

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
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    validate_form = form.validate_on_submit()
    if validate_form:
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

# Route to update coins
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

# Route to get coins
@app.route('/getCoins', methods=['GET'])
@login_required
def get_coins():
    try:
        return jsonify({'coins': current_user.coins}), 200
    except Exception as e:
        app.logger.error(f'Error retrieving coins: {e}')
        return jsonify({'error': 'An error occurred while retrieving coins'}), 500

from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return 'Username already taken. Please choose a different username.'

        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        
        try:
            # Add the new user to the local database
            db.session.add(new_user)
            db.session.commit()

            # Call the backend to create a user with 100 starting coins
            response = requests.post('http://localhost:3001/createUser', json={'userId': new_user.username})
            
            # Log the full response for debugging
            print('Response status code:', response.status_code)
            print('Response content:', response.content)

            if response.status_code != 201:
                try:
                    error_message = response.json().get('error', 'Unknown error')
                except ValueError:
                    error_message = f"Non-JSON response: {response.text}"

                return f"Error creating user on backend: {error_message}"

            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}"

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return 'Welcome to your dashboard'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables within the application context
    app.run(debug=True)


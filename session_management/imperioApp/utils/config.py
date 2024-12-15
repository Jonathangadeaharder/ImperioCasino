import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'  # Replace with a secure random value
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CHERRY_CHARM_URL = 'http://localhost:5173'
    BLACK_JACK_URL = 'http://localhost:5174'
    ROULETTE_URL = 'http://localhost:5175'
    SESSION_TYPE = 'filesystem'  # Store sessions on the server
    SESSION_PERMANENT = True


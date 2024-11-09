# === config.py ===

class Config:
    SECRET_KEY = 'your-secret-key'  # Replace with a secure random value
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .utils.config import Config  # Use relative import
import logging
import os
from flask_cors import CORS
from flask_session import Session  # Import Flask-Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

app = Flask(__name__)
app.config.from_object(Config)

# Set up logging based on environment
log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(
    level=log_level,
    format='%(asctime)s %(levelname)s %(name)s : %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Reduce verbose logging from werkzeug in production
if app.config.get('LOG_LEVEL') != 'DEBUG':
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

Session(app)  # Initialize Flask-Session

# Configure CORS with specific origins
CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}}, supports_credentials=True)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Migrate
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from . import routes  # Use relative imports
from .utils import models

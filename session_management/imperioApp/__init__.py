from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config  # Use relative import
import logging
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s',
                    handlers=[
                        logging.FileHandler("app_debug.log"),
                        logging.StreamHandler()
                    ])

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/*": {"origins": "*"}})

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Migrate
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from . import routes, models  # Use relative imports

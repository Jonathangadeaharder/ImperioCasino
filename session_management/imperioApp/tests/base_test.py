import unittest
from .. import app, db
from ..utils.config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # In-memory database for testing
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False  # Disable CSRF protection in tests

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestConfig)
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

import unittest
from .. import app, db
from ..models import User
from werkzeug.security import generate_password_hash

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        # Create a test user
        u = User(username='testuser', email='test@example.com')
        u.set_password('testpass')
        db.session.add(u)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login(self):
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        self.assertIn(b'Welcome, testuser!', response.data)

if __name__ == '__main__':
    unittest.main()

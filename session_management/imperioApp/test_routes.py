import unittest
from . import app, db
from .models import User
from flask import url_for

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_user(self, username, email, password, password2):
        return self.app.post('/signup', data={
            'username': username,
            'email': email,
            'password': password,
            'password2': password2
        }, follow_redirects=True)

    def login_user(self, username, password):
        return self.app.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_signup(self):
        response = self.register_user('newuser', 'new@example.com', 'newpass', 'newpass')
        self.assertIn(b'Congratulations, you are now a registered user!', response.data)
        # Verify user exists in the database with default coins
        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.coins, 100)

    def test_duplicate_signup(self):
        # First registration
        self.register_user('newuser', 'new@example.com', 'newpass', 'newpass')
        # Attempt to register the same user again
        response = self.register_user('newuser', 'new@example.com', 'newpass', 'newpass')
        self.assertIn(b'Username or email already exists', response.data)

    def test_login(self):
        # First, register a user
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        # Then, log in
        response = self.login_user('testuser', 'testpass')
        self.assertIn(b'Welcome, testuser!', response.data)

    def test_invalid_login(self):
        response = self.login_user('nonexistent', 'wrongpass')
        self.assertIn(b'Invalid username or password', response.data)

    def test_dashboard_access(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Access dashboard
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Welcome, testuser!', response.data)
        self.assertIn(b'You have 100 coins.', response.data)

    def test_logout(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Log out
        response = self.app.get('/logout', follow_redirects=True)
        self.assertIn(b'Sign In', response.data)

    def test_update_coins(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Update coins
        response = self.app.post('/updateCoins', json={'coins': 200}, follow_redirects=True)
        self.assertIn(b'Coins updated successfully', response.data)
        # Verify coins have been updated
        user = User.query.filter_by(username='testuser').first()
        self.assertEqual(user.coins, 200)

    def test_get_coins(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Get coins
        response = self.app.get('/getCoins', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"coins": 100', response.data)

    def test_update_coins_unauthenticated(self):
        # Try to update coins without logging in
        response = self.app.post('/updateCoins', json={'coins': 200}, follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

    def test_get_coins_unauthenticated(self):
        # Try to get coins without logging in
        response = self.app.get('/getCoins', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

    def test_update_coins_invalid_input(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Attempt to update coins with invalid data
        response = self.app.post('/updateCoins', json={'coins': 'invalid'}, follow_redirects=True)
        self.assertIn(b'Coins must be an integer', response.data)

    def test_update_coins_negative_value(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Attempt to update coins with negative value
        response = self.app.post('/updateCoins', json={'coins': -50}, follow_redirects=True)
        self.assertIn(b'Coins cannot be negative', response.data)

if __name__ == '__main__':
    unittest.main()

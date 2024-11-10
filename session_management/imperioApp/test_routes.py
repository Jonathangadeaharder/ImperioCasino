import unittest
from . import app, db
from .models import User
from flask import url_for

import unittest
from unittest.mock import patch
from . import app, db
from .models import User
from flask import url_for, session
import jwt
import datetime
from urllib.parse import urlparse, parse_qs

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
        data = response.get_json()
        self.assertEqual(data['coins'], 100)

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

    def test_verify_token_valid(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        login_response = self.login_user('testuser', 'testpass')
        # Retrieve the token from the session cookie
        with self.app as client:
            with client.session_transaction() as sess:
                token = sess['token']
        # Prepare the data
        data = {
            'token': token,
            'username': 'testuser'
        }
        # Send POST request to /verify-token
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"message": "Token is valid"', response.data)

    def test_verify_token_invalid_token(self):
        # Prepare invalid token data
        data = {
            'token': 'invalidtoken',
            'username': 'testuser'
        }
        # Send POST request to /verify-token
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'"message": "Invalid token"', response.data)

    def test_verify_token_expired_token(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        # Manually generate an expired token
        import jwt
        expired_token = jwt.encode(
            {'user_id': 1, 'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        data = {
            'token': expired_token,
            'username': 'testuser'
        }
        # Send POST request to /verify-token
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'"message": "Token has expired"', response.data)

    def test_verify_token_username_mismatch(self):
        # Register and log in as testuser
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Retrieve the token
        with self.app as client:
            with client.session_transaction() as sess:
                token = sess['token']
        # Prepare data with a different username
        data = {
            'token': token,
            'username': 'otheruser'
        }
        # Send POST request to /verify-token
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'"message": "Invalid token or username"', response.data)

    def test_verify_token_missing_fields(self):
        # Missing token
        data = {'username': 'testuser'}
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'"message": "Token and username are required"', response.data)

        # Missing username
        data = {'token': 'sometoken'}
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'"message": "Token and username are required"', response.data)

    def test_redirect_to_imperio_authenticated(self):
        # Register and log in
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.login_user('testuser', 'testpass')
        # Access the redirect route
        response = self.app.get('/redirect-imperio', follow_redirects=False)
        self.assertEqual(response.status_code, 302)  # Should redirect
        # Check the Location header for the correct redirection URL
        redirect_location = response.headers.get('Location')
        self.assertIsNotNone(redirect_location)
        # The URL should contain the username and token as query parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(redirect_location)
        self.assertEqual(parsed_url.netloc, '13.60.215.133:5173')
        query_params = parse_qs(parsed_url.query)
        self.assertEqual(query_params.get('username'), ['testuser'])
        self.assertIn('token', query_params)
        # Optionally, verify the token
        token = query_params['token'][0]
        import jwt
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        self.assertEqual(decoded_token['user_id'], 1)  # Assuming this is the first user

    def test_redirect_to_imperio_unauthenticated(self):
        # Try to access the redirect route without logging in
        response = self.app.get('/redirect-imperio', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

if __name__ == '__main__':
    unittest.main()

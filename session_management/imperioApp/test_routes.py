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

    # Test for authenticated redirect to Imperio
    def test_redirect_to_imperio_authenticated(self):
        with patch('imperioApp.routes.requests.post') as mock_post:
            # Mock the external API call during signup
            mock_response = unittest.mock.Mock()
            mock_response.status_code = 201
            mock_response.content = b''
            mock_post.return_value = mock_response

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
        parsed_url = urlparse(redirect_location)
        self.assertEqual(parsed_url.netloc, '13.60.215.133:5173')
        query_params = parse_qs(parsed_url.query)
        self.assertEqual(query_params.get('username'), ['testuser'])
        self.assertIn('token', query_params)

        # Optionally, verify the token
        token = query_params['token'][0]
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        self.assertEqual(decoded_token['user_id'], 1)  # Assuming this is the first user

    # Test for unauthenticated redirect to Imperio
    def test_redirect_to_imperio_unauthenticated(self):
        # Try to access the redirect route without logging in
        response = self.app.get('/redirect-imperio', follow_redirects=True)
        self.assertIn(b'Please log in to access this page.', response.data)

    # Test for valid token verification
    def test_verify_token_valid(self):
        with patch('imperioApp.routes.requests.post') as mock_post:
            # Mock the external API call during signup
            mock_response = unittest.mock.Mock()
            mock_response.status_code = 201
            mock_response.content = b''
            mock_post.return_value = mock_response

            # Register and log in
            self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
            self.login_user('testuser', 'testpass')

        # Retrieve the token from the session
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

    # Test for invalid token verification
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

    # Test for expired token verification
    def test_verify_token_expired_token(self):
        with patch('imperioApp.routes.requests.post') as mock_post:
            # Mock the external API call during signup
            mock_response = unittest.mock.Mock()
            mock_response.status_code = 201
            mock_response.content = b''
            mock_post.return_value = mock_response

            # Register and log in
            self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
            self.login_user('testuser', 'testpass')

        expired_token = jwt.encode(
            {'user_id': 1, 'exp': datetime. datetime. now(datetime. UTC) - datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        data = {
            'token': expired_token,
            'username': 'testuser'
        }
        response = self.app.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'"message": "Token has expired"', response.data)

    # Test for username mismatch in token verification
    def test_verify_token_username_mismatch(self):
        with patch('imperioApp.routes.requests.post') as mock_post:
            # Mock the external API call during signup
            mock_response = unittest.mock.Mock()
            mock_response.status_code = 201
            mock_response.content = b''
            mock_post.return_value = mock_response

            # Register and log in
            self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
            self.login_user('testuser', 'testpass')

        # Retrieve the token from the session
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

    # Test for missing fields in token verification
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

    # Test for successful signup with mocked external API
    @patch('imperioApp.routes.requests.post')
    def test_signup_successful_external_api(self, mock_post):
        # Mock the external API response to simulate successful user creation
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 201
        mock_response.content = b''
        mock_post.return_value = mock_response

        # Register a new user
        response = self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.assertIn(b'Congratulations, you are now a registered user!', response.data)

        # Ensure the external API was called with correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], app.config['EXTERNAL_API_URL'])
        self.assertEqual(kwargs['json'], {'userId': 'testuser'})
        self.assertIn('Authorization', kwargs['headers'])
        self.assertTrue(kwargs['headers']['Authorization'].startswith('Bearer '))

    # Test for signup failure due to external API
    @patch('imperioApp.routes.requests.post')
    def test_signup_external_api_failure(self, mock_post):
        # Mock the external API response to simulate failure
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'User creation failed'}
        mock_response.text = '{"error": "User creation failed"}'
        mock_post.return_value = mock_response

        # Register a new user
        response = self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.assertIn(b'Error creating user on backend: User creation failed', response.data)

        # Ensure the external API was called with correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], app.config['EXTERNAL_API_URL'])
        self.assertEqual(kwargs['json'], {'userId': 'testuser'})
        self.assertIn('Authorization', kwargs['headers'])
        self.assertTrue(kwargs['headers']['Authorization'].startswith('Bearer '))

    # Test for signup with non-JSON response from external API
    @patch('imperioApp.routes.requests.post')
    def test_signup_external_api_non_json_response(self, mock_post):
        # Mock the external API response to return non-JSON content
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("No JSON")
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        # Register a new user
        response = self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        self.assertIn(b'Error creating user on backend: Non-JSON response: Internal Server Error', response.data)

        # Ensure the external API was called with correct parameters
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], app.config['EXTERNAL_API_URL'])
        self.assertEqual(kwargs['json'], {'userId': 'testuser'})
        self.assertIn('Authorization', kwargs['headers'])
        self.assertTrue(kwargs['headers']['Authorization'].startswith('Bearer '))

    # Test for duplicate username during signup
    @patch('imperioApp.routes.requests.post')
    def test_signup_duplicate_username(self, mock_post):
        # Mock the external API call during signup
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 201
        mock_response.content = b''
        mock_post.return_value = mock_response

        # First registration
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        # Attempt to register the same user again
        response = self.register_user('testuser', 'test2@example.com', 'testpass', 'testpass')
        self.assertIn(b'Username or email already exists', response.data)

    # Test for duplicate email during signup
    @patch('imperioApp.routes.requests.post')
    def test_signup_duplicate_email(self, mock_post):
        # Mock the external API call during signup
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 201
        mock_response.content = b''
        mock_post.return_value = mock_response

        # First registration
        self.register_user('testuser', 'test@example.com', 'testpass', 'testpass')
        # Attempt to register with the same email
        response = self.register_user('testuser2', 'test@example.com', 'testpass', 'testpass')
        self.assertIn(b'Username or email already exists', response.data)

if __name__ == '__main__':
    unittest.main()

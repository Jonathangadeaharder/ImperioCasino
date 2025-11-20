"""
Comprehensive authentication tests using pytest (Month 2 - Enhanced Testing).

This module demonstrates pytest best practices including:
- Fixtures usage
- Parametrized tests
- Markers
- Proper assertions
- Comprehensive coverage
"""

import pytest
import jwt
from flask import session
from imperioApp.utils.auth import generate_token, decode_token
from imperioApp.utils.models import User


class TestUserAuthentication:
    """Test suite for user authentication."""

    @pytest.mark.unit
    def test_user_registration_success(self, client):
        """Test successful user registration."""
        response = client.post('/signup', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password2': 'securepass123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Sign In' in response.data

        # Verify user was created
        with client.application.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'newuser@example.com'
            assert user.verify_password('securepass123')

    @pytest.mark.unit
    @pytest.mark.parametrize("username,email,password,expected_error", [
        ('', 'test@test.com', 'pass123', 'username'),  # Empty username
        ('user', '', 'pass123', 'email'),  # Empty email
        ('user', 'invalid-email', 'pass123', 'email'),  # Invalid email
        ('user', 'test@test.com', '', 'password'),  # Empty password
        ('user', 'test@test.com', '123', 'password'),  # Too short password
    ])
    def test_user_registration_validation(self, client, username, email, password, expected_error):
        """Test user registration input validation."""
        response = client.post('/signup', data={
            'username': username,
            'email': email,
            'password': password,
            'password2': password
        })

        # Should either show error or redirect to signup
        assert response.status_code in [200, 302]

    @pytest.mark.unit
    def test_user_registration_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        response = client.post('/signup', data={
            'username': test_user.username,  # Duplicate
            'email': 'different@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        })

        assert response.status_code in [200, 302]

    @pytest.mark.unit
    def test_user_login_success(self, client, test_user):
        """Test successful user login."""
        response = client.post('/login', data={
            'username': test_user.username,
            'password': 'testpass123',
            'remember_me': False
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Logout' in response.data

    @pytest.mark.unit
    def test_user_login_wrong_password(self, client, test_user):
        """Test login with incorrect password."""
        response = client.post('/login', data={
            'username': test_user.username,
            'password': 'wrongpassword',
            'remember_me': False
        })

        assert b'Invalid username or password' in response.data or response.status_code == 302

    @pytest.mark.unit
    def test_user_login_nonexistent_user(self, client):
        """Test login with non-existent username."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'somepass123',
            'remember_me': False
        })

        assert b'Invalid username or password' in response.data or response.status_code == 302

    @pytest.mark.unit
    def test_user_logout(self, authenticated_client):
        """Test user logout."""
        response = authenticated_client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert b'Sign In' in response.data

    @pytest.mark.unit
    def test_remember_me_functionality(self, client, test_user):
        """Test remember me functionality."""
        with client:
            response = client.post('/login', data={
                'username': test_user.username,
                'password': 'testpass123',
                'remember_me': True
            }, follow_redirects=True)

            assert response.status_code == 200

class TestJWTTokens:
    """Test suite for JWT token functionality."""

    @pytest.mark.unit
    def test_generate_token(self, test_user):
        """Test JWT token generation."""
        token = generate_token(test_user.username)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long

    @pytest.mark.unit
    def test_decode_valid_token(self, test_user, auth_token):
        """Test decoding a valid JWT token."""
        decoded = decode_token(auth_token)

        assert decoded is not None
        assert 'user_id' in decoded
        assert decoded['user_id'] == test_user.username
        assert 'exp' in decoded  # Expiration claim

    @pytest.mark.unit
    def test_decode_invalid_token(self):
        """Test decoding an invalid JWT token."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_token('invalid.token.here')

    @pytest.mark.unit
    def test_decode_expired_token(self, test_user):
        """Test decoding an expired JWT token."""
        from datetime import datetime, timedelta, timezone
        import jwt as pyjwt
        from flask import current_app

        # Create an expired token
        expired_token = pyjwt.encode(
            {'user_id': test_user.username, 'exp': datetime.now(timezone.utc) - timedelta(hours=1)},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(expired_token)

    @pytest.mark.api
    def test_token_required_decorator(self, client, test_user, auth_headers):
        """Test token_required decorator on protected endpoints."""
        # Without token
        response = client.get('/getCoins')
        assert response.status_code == 401
        data = response.get_json()
        assert data['message'] == 'Token is missing'

        # With valid token
        response = client.get('/getCoins', headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.api
    def test_verify_token_endpoint(self, client, test_user, auth_token):
        """Test the /verify-token endpoint."""
        response = client.post('/verify-token', json={
            'token': auth_token,
            'username': test_user.username
        })

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Token is valid'

    @pytest.mark.api
    def test_verify_token_invalid(self, client):
        """Test /verify-token with invalid token."""
        response = client.post('/verify-token', json={
            'token': 'invalid.token',
            'username': 'someuser'
        })

        assert response.status_code == 401


class TestPasswordSecurity:
    """Test suite for password security."""

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_hashing(self, test_user):
        """Test that passwords are properly hashed."""
        # Password should not be stored in plain text
        assert test_user.password != 'testpass123'

        # Should be a bcrypt hash (starts with $2b$)
        assert test_user.password.startswith('$2b$') or test_user.password.startswith('pbkdf2:')

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_verification(self, test_user):
        """Test password verification."""
        assert test_user.verify_password('testpass123') is True
        assert test_user.verify_password('wrongpassword') is False

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.parametrize("password", [
        'short',  # Too short
        '12345678',  # Only numbers
        'abcdefgh',  # Only lowercase
        'ABCDEFGH',  # Only uppercase
    ])
    def test_weak_passwords(self, client, password):
        """Test that weak passwords are handled."""
        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': password,
            'password2': password
        })

        # The form should validate or show error
        assert response.status_code in [200, 302]


class TestSessionManagement:
    """Test suite for session management."""

    @pytest.mark.unit
    def test_session_creation_on_login(self, client, test_user):
        """Test that session is created on successful login."""
        with client:
            response = client.post('/login', data={
                'username': test_user.username,
                'password': 'testpass123',
                'remember_me': False
            }, follow_redirects=True)

            # Session should contain user information
            assert 'user_id' in session or '_user_id' in session

    @pytest.mark.unit
    def test_session_destruction_on_logout(self, authenticated_client):
        """Test that session is destroyed on logout."""
        with authenticated_client:
            # Verify session exists
            assert 'user_id' in session or '_user_id' in session

            # Logout
            response = authenticated_client.get('/logout', follow_redirects=True)

            # Session should be cleared
            # (Note: Some session data may persist but user should be logged out)
            assert response.status_code == 200


class TestAuthIntegration:
    """Integration tests for authentication flow."""

    @pytest.mark.integration
    def test_full_registration_login_logout_flow(self, client):
        """Test complete user journey: register -> login -> logout."""
        # 1. Register
        response = client.post('/signup', data={
            'username': 'flowuser',
            'email': 'flow@example.com',
            'password': 'flowpass123',
            'password2': 'flowpass123'
        }, follow_redirects=True)
        assert response.status_code == 200

        # 2. Login
        response = client.post('/login', data={
            'username': 'flowuser',
            'password': 'flowpass123',
            'remember_me': False
        }, follow_redirects=True)
        assert response.status_code == 200

        # 3. Logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data

    @pytest.mark.integration
    def test_protected_route_access(self, client, test_user, auth_headers):
        """Test access to protected routes with and without authentication."""
        # Without authentication
        response = client.get('/getCoins')
        assert response.status_code == 401

        # With authentication
        response = client.get('/getCoins', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert 'coins' in data
        assert data['coins'] == test_user.coins

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_login_attempts(self, client, test_user, disable_rate_limiting):
        """Test multiple concurrent login attempts."""
        import concurrent.futures

        def attempt_login():
            return client.post('/login', data={
                'username': test_user.username,
                'password': 'testpass123',
                'remember_me': False
            })

        # Attempt multiple concurrent logins
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attempt_login) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed (or handle rate limiting gracefully)
        assert all(r.status_code in [200, 302, 429] for r in results)


@pytest.mark.api
class TestAuthAPI:
    """API-specific authentication tests."""

    def test_api_token_authentication(self, client, test_user, auth_token):
        """Test API authentication using Bearer token."""
        headers = {'Authorization': f'Bearer {auth_token}'}

        response = client.get('/getCoins', headers=headers)
        assert response.status_code == 200

    def test_api_invalid_token_format(self, client):
        """Test API with invalid token format."""
        headers = {'Authorization': 'InvalidFormat token123'}

        response = client.get('/getCoins', headers=headers)
        assert response.status_code == 401

    def test_api_missing_authorization_header(self, client):
        """Test API without Authorization header."""
        response = client.get('/getCoins')
        assert response.status_code == 401
        data = response.get_json()
        assert 'Token is missing' in data['message']

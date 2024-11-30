from datetime import datetime, timezone
from ..utils.auth import generate_token, decode_token, login_user_session, logout_user_session
from ..utils.models import User
from .. import db
from .base_test import BaseTestCase
from flask import session
from flask_login import current_user

class AuthTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('testpassword')
        db.session.add(self.user)
        db.session.commit()

    def test_generate_decode_token(self):
        token = generate_token(self.user.username)
        self.assertIsNotNone(token)
        decoded = decode_token(token)
        self.assertEqual(decoded['user_id'], self.user.username)
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        self.assertTrue(exp > now)

    def test_login_logout_user_session(self):
        with self.app.test_request_context():
            # Initialize session
            session['init'] = True
            # Call login_user_session
            login_user_session(self.user)
            self.assertIn('token', session)
            self.assertIn('username', session)
            self.assertEqual(session['username'], self.user.username)
            self.assertTrue(current_user.is_authenticated)
            self.assertEqual(current_user.username, self.user.username)
            # Call logout_user_session
            logout_user_session()
            self.assertNotIn('token', session)
            self.assertNotIn('username', session)
            self.assertFalse(current_user.is_authenticated)

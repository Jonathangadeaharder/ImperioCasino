import unittest
from ..utils.models import User
from .base_test import BaseTestCase
from ..utils.constants import DEFAULT_COINS  # Import DEFAULT_COINS
from .. import db

class UserModelTestCase(BaseTestCase):
    def test_password_hashing(self):
        u = User(username='testuser')
        u.set_password('cat')
        self.assertFalse(u.verify_password('dog'))
        self.assertTrue(u.verify_password('cat'))

    def test_no_password_getter(self):
        u = User(username='testuser')
        u.set_password('cat')
        with self.assertRaises(AttributeError):
            password = u.password

    def test_user_representation(self):
        u = User(username='testuser')
        self.assertEqual(repr(u), '<User testuser>')

    def test_coins_default(self):
        u = User(username='testuser')
        self.assertEqual(u.coins, DEFAULT_COINS)  # Use DEFAULT_COINS

    def test_create_user(self):
        u = User(username='testuser', email='test@example.com')
        u.set_password('test')
        db.session.add(u)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        u2 = User.query.filter_by(username='testuser').first()
        self.assertEqual(u2.email, 'test@example.com')
        self.assertTrue(u2.verify_password('test'))
        self.assertEqual(u2.coins, DEFAULT_COINS)  # Use DEFAULT_COINS

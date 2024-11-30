from ..utils.services import get_user_by_username, create_user, update_user_coins, adjust_user_coins
from .base_test import BaseTestCase


class ServicesTestCase(BaseTestCase):
    def test_create_user(self):
        user = create_user('testuser', 'test@example.com', 'testpassword')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.verify_password('testpassword'))
        self.assertEqual(user.coins, 100)

    def test_get_user_by_username(self):
        create_user('testuser', 'test@example.com', 'testpassword')
        user = get_user_by_username('testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_update_user_coins(self):
        user = create_user('testuser', 'test@example.com', 'testpassword')
        update_user_coins(user, 200)
        self.assertEqual(user.coins, 200)

    def test_adjust_user_coins(self):
        user = create_user('testuser', 'test@example.com', 'testpassword')
        adjust_user_coins(user, -50)
        self.assertEqual(user.coins, 50)
        adjust_user_coins(user, 25)
        self.assertEqual(user.coins, 75)

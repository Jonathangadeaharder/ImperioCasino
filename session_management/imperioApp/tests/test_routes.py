from ..utils.services import create_user
from .. import db
from .base_test import BaseTestCase
from flask import session

class RoutesTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = create_user('testuser', 'test@example.com', 'testpassword')

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Sign In', response.data)

    def test_login(self):
        response = self.login('testuser', 'testpassword')
        self.assertIn(b'Welcome, testuser!', response.data)

    def test_login_invalid(self):
        response = self.login('testuser', 'wrongpassword')
        self.assertIn(b'Invalid username or password', response.data)

    def test_signup(self):
        response = self.client.post('/signup', data=dict(
            username='newuser',
            email='new@example.com',
            password='newpassword',
            password2='newpassword'
        ), follow_redirects=True)
        self.assertIn(b'Congratulations, you are now a registered user!', response.data)

    def test_logout(self):
        self.login('testuser', 'testpassword')
        response = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'Sign In', response.data)

    def test_get_coins(self):
        with self.client:
            self.login('testuser', 'testpassword')
            token = session['token']
            headers = {'Authorization': f'Bearer {token}'}
            response = self.client.get('/getCoins', headers=headers)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('coins', data)
            self.assertEqual(data['coins'], 100)

    def test_spin(self):
        with self.client:
            self.login('testuser', 'testpassword')
            token = session['token']
            headers = {'Authorization': f'Bearer {token}'}
            response = self.client.post('/spin', headers=headers)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('stopSegments', data)
            self.assertIn('totalCoins', data)

    def test_spin_not_enough_coins(self):
        self.user.coins = 0
        db.session.commit()
        with self.client:
            self.login('testuser', 'testpassword')
            token = session['token']
            headers = {'Authorization': f'Bearer {token}'}
            response = self.client.post('/spin', headers=headers)
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertEqual(data['message'], 'Not enough coins to spin')

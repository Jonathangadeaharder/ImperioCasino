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

        # Tests for /verify-token
    def test_verify_token_valid(self):
        # Login to get a valid token
        with self.client:
            self.login('testuser', 'testpassword')
            token = session.get('token')
            data = {
                'token': token,
                'username': 'testuser'
            }
            response = self.client.post('/verify-token', json=data)
            self.assertEqual(response.status_code, 200)
            resp_data = response.get_json()
            self.assertEqual(resp_data['message'], 'Token is valid')

    def test_verify_token_invalid_token(self):
        data = {
            'token': 'invalidtoken',
            'username': 'testuser'
        }
        response = self.client.post('/verify-token', json=data)
        self.assertEqual(response.status_code, 401)
        resp_data = response.get_json()
        self.assertIn('Invalid token', resp_data['message'])

    def test_verify_token_missing_fields(self):
        response = self.client.post('/verify-token', json={'token': 'sometoken'})
        self.assertEqual(response.status_code, 400)
        resp_data = response.get_json()
        self.assertIn('are required', resp_data['message'])

    # Tests for /updateCoins
    def test_update_coins_valid(self):
        with self.client:
            self.login('testuser', 'testpassword')
            token = session.get('token')
            headers = {'Authorization': f'Bearer {token}'}
            response = self.client.post('/updateCoins', headers=headers, json={'coins': 200})
            self.assertEqual(response.status_code, 200)
            resp_data = response.get_json()
            self.assertEqual(resp_data['message'], 'Coins updated successfully')
            self.assertEqual(self.user.coins, 200)

    def test_update_coins_missing_field(self):
        with self.client:
            self.login('testuser', 'testpassword')
            token = session.get('token')
            headers = {'Authorization': f'Bearer {token}'}
            response = self.client.post('/updateCoins', headers=headers, json={})
            self.assertEqual(response.status_code, 400)
            resp_data = response.get_json()
            self.assertIn('Coins are required', resp_data['message'])

    def test_update_coins_unauthorized(self):
        # No token provided
        response = self.client.post('/updateCoins', json={'coins': 200})
        self.assertEqual(response.status_code, 401)
        resp_data = response.get_json()
        self.assertIn('Token is missing', resp_data['message'])

    # Tests for redirect routes
    def test_redirect_imperio(self):
        self.login('testuser', 'testpassword')
        response = self.client.get('/redirect-imperio', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        location = response.headers.get('Location')
        self.assertIn('http://localhost:5173/?username=testuser&token=', location)

    def test_redirect_blackjack(self):
        self.login('testuser', 'testpassword')
        response = self.client.get('/redirect-blackjack', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        location = response.headers.get('Location')
        self.assertIn('http://localhost:5174/?username=testuser&token=', location)

    def test_redirect_roulette(self):
        self.login('testuser', 'testpassword')
        response = self.client.get('/redirect-roulette', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        location = response.headers.get('Location')
        self.assertIn('http://localhost:5175/?username=testuser&token=', location)

    def test_redirect_requires_login(self):
        # Attempt to access redirect-imperio without logging in
        response = self.client.get('/redirect-imperio', follow_redirects=True)
        self.assertIn(b'Sign In', response.data)

from .base_test import BaseTestCase
from ..utils.services import create_user, update_user_coins
from flask import session
import json
from unittest.mock import patch

class RouletteTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = create_user('roulette_user', 'roulette@example.com', 'roulettepass')
        self.login_user()

    def login_user(self):
        with self.client:
            response = self.client.post('/login', data=dict(
                username='roulette_user',
                password='roulettepass'
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.token = session.get('token')
            self.assertIsNotNone(self.token)

    def make_request(self, bet_info):
        headers = {'Authorization': f'Bearer {self.token}'}
        return self.client.post(
            '/roulette/action',
            data=json.dumps({'bet': bet_info}),
            headers=headers,
            content_type='application/json'
        )

    def test_roulette_no_bet_provided(self):
        """Test that not providing bets returns an error."""
        response = self.make_request(None)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Bet details are required')

    def test_roulette_invalid_bet_amount(self):
        """Test that an invalid bet amount returns an error."""
        bet_info = [{'numbers': '1', 'odds': 35, 'amt': 0}]
        response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['message'], 'Invalid bet amount')

    def test_roulette_insufficient_coins(self):
        """Test betting more coins than the user has."""
        update_user_coins(self.user, 10)
        bet_info = [{'numbers': '1', 'odds': 35, 'amt': 20}]
        response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['message'], 'Not enough coins')

    def test_roulette_single_number_win(self):
        """
        Test a single-number bet scenario where the winning number is known.
        With odds = 35, a correct guess should return player's original bet + odds*bet.
        Example: Bet 10 on number 17, if 17 hits, player should get (35*10)+10 = 360.
        """
        initial_coins = self.user.coins
        bet_info = [{'numbers': '17', 'odds': 35, 'amt': 10}]
        # Mock random.choice to return a known winning number (17)
        with patch('random.choice', return_value=17):
            response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('winning_number', data)
        self.assertEqual(data['winning_number'], 17)
        self.assertEqual(data['total_bet'], 10)
        self.assertEqual(data['total_win'], 360)
        self.assertEqual(data['new_coins'], initial_coins - 10 + 360)

    def test_roulette_single_number_loss(self):
        """
        Test a single-number bet scenario where the player loses.
        Example: Bet 10 on number 17, winning number is 5, no payout.
        """
        initial_coins = self.user.coins
        bet_info = [{'numbers': '17', 'odds': 35, 'amt': 10}]
        with patch('random.choice', return_value=5):
            response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['winning_number'], 5)
        self.assertEqual(data['total_bet'], 10)
        self.assertEqual(data['total_win'], 0)
        # Player should lose the bet amount
        self.assertEqual(data['new_coins'], initial_coins - 10)

    def test_roulette_multiple_bets_mixed_outcomes(self):
        """
        Test multiple bets:
        - Bet 10 on number '5' with odds 35
        - Bet 20 on numbers '1,2,3' with odds 11 (like a street bet)
        Winning number = 2
        For the first bet (5), no win.
        For the second bet (1,2,3), player wins: (odds * amt) + amt = (11*20)+20 = 240
        Total bet = 10+20=30
        Net = initial_coins -30 +240 = initial_coins +210
        """
        initial_coins = self.user.coins
        bet_info = [
            {'numbers': '5', 'odds': 35, 'amt': 10},
            {'numbers': '1,2,3', 'odds': 11, 'amt': 20}
        ]
        with patch('random.choice', return_value=2):
            response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['winning_number'], 2)
        self.assertEqual(data['total_bet'], 30)
        self.assertEqual(data['total_win'], 240)
        self.assertEqual(data['new_coins'], initial_coins - 30 + 240)

    def test_roulette_invalid_numbers_format(self):
        """
        Test that providing invalid numbers format (like 'abc' or empty string)
        returns a proper error message.
        """
        bet_info = [{'numbers': 'abc', 'odds': 35, 'amt': 10}]
        response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data['message'], 'Invalid bet numbers')

        bet_info = [{'numbers': '', 'odds': 35, 'amt': 10}]
        response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)  # No numbers means no win scenario
        data = response.get_json()
        # If empty numbers is considered valid but no hits, just a loss
        self.assertEqual(data['total_win'], 0)

    def test_roulette_multiple_bets_all_lost(self):
        """
        Test multiple bets where none hit:
        Bet 10 on '1' odds 35
        Bet 20 on '2,3' odds 17
        Winning number = 4 (not in any bet)
        Total bet = 30
        total_win = 0
        """
        initial_coins = self.user.coins
        bet_info = [
            {'numbers': '1', 'odds': 35, 'amt': 10},
            {'numbers': '2,3', 'odds': 17, 'amt': 20}
        ]
        with patch('random.choice', return_value=4):
            response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total_bet'], 30)
        self.assertEqual(data['total_win'], 0)
        self.assertEqual(data['new_coins'], initial_coins - 30)

    def test_roulette_edge_number_zero(self):
        """
        Test a bet on '0' which is a valid number on the wheel.
        Bet 10 on '0' odds 35
        Winning number = 0 means a win of 360
        """
        initial_coins = self.user.coins
        bet_info = [{'numbers': '0', 'odds': 35, 'amt': 10}]
        with patch('random.choice', return_value=0):
            response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['winning_number'], 0)
        self.assertEqual(data['total_bet'], 10)
        self.assertEqual(data['total_win'], 360)
        self.assertEqual(data['new_coins'], initial_coins - 10 + 360)

    def test_roulette_large_multiple_bets(self):
        """
        Test a scenario with multiple bets and a large coverage:
        Bet 10 on '1,2,3,4,5,6' odds 5 (example only)
        Bet 15 on '10,11,12' odds 11
        Bet 5 on '20' odds 35
        Winning number = 11
        The second bet wins: payout = 15*(11) + 15 = 180
        Total bet = 10+15+5=30
        Net = initial_coins -30 +180 = initial_coins +150
        """
        initial_coins = self.user.coins
        bet_info = [
            {'numbers': '1,2,3,4,5,6', 'odds': 5, 'amt': 10},
            {'numbers': '10,11,12', 'odds': 11, 'amt': 15},
            {'numbers': '20', 'odds': 35, 'amt': 5}
        ]
        with patch('random.choice', return_value=11):
            response = self.make_request(bet_info)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['winning_number'], 11)
        self.assertEqual(data['total_bet'], 30)
        self.assertEqual(data['total_win'], 180)
        self.assertEqual(data['new_coins'], initial_coins - 30 + 180)

    def test_roulette_token_required(self):
        """
        Test that calling roulette action without a token returns 401.
        """
        response = self.client.post('/roulette/action', json={'bet': [{'numbers': '1', 'odds': 35, 'amt': 10}]})
        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertEqual(data['message'], 'Token is missing')

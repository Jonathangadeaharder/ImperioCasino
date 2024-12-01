from ..game_logic.blackjack import (
    start_game, player_action, calculate_hand_value,
    dealer_turn, determine_winner, compare_hands
)
from ..utils.services import create_user
from ..utils.models import BlackjackGameState
from .. import db
from .base_test import BaseTestCase

class BlackjackTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create a test user with sufficient coins
        self.user = create_user('testuser', 'test@example.com', 'testpassword')
        self.user.coins = 500
        db.session.commit()

    def test_start_game_valid_wager(self):
        # Test starting a game with a valid wager
        wager = 50
        response, status_code = start_game(self.user, wager)
        self.assertEqual(status_code, 200)
        self.assertFalse(response['game_over'])
        self.assertEqual(len(response['player_hand']), 2)
        # Adjusted to match game logic where dealer starts with 2 cards
        self.assertEqual(len(response['dealer_hand']), 2)
        self.assertEqual(response['current_wager'], wager)
        self.assertEqual(response['player_coins'], self.user.coins)
        self.assertEqual(self.user.coins, 500 - wager)

    def test_start_game_invalid_wager(self):
        # Test starting a game with an invalid wager (zero or negative)
        wager = -10
        response, status_code = start_game(self.user, wager)
        self.assertEqual(status_code, 400)
        self.assertTrue(response['game_over'])
        self.assertEqual(response['message'], 'Invalid wager amount')

    def test_start_game_insufficient_coins(self):
        # Test starting a game when user has insufficient coins
        self.user.coins = 20
        db.session.commit()
        wager = 50
        response, status_code = start_game(self.user, wager)
        self.assertEqual(status_code, 400)
        self.assertTrue(response['game_over'])
        self.assertEqual(response['message'], 'Insufficient coins')

    def test_player_hit(self):
        # Start a game and perform a hit action
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand to prevent bust
        game_state.player_hand.clear()
        game_state.player_hand.append({'suit': 'hearts', 'name': '2', 'value': 2})
        game_state.player_hand.append({'suit': 'diamonds', 'name': '3', 'value': 3})
        # Ensure the next card won't cause bust
        game_state.deck.insert(0, {'suit': 'clubs', 'name': '5', 'value': 5})
        db.session.commit()
        initial_hand_size = len(game_state.player_hand)
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)
        db.session.refresh(game_state)
        self.assertEqual(len(game_state.player_hand), initial_hand_size + 1)
        self.assertFalse(game_state.game_over)


    def test_player_hit_bust(self):
        # Force player hand to bust after hit
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand to have high value
        game_state.player_hand.clear()
        game_state.player_hand.append({'suit': 'hearts', 'name': 'King', 'value': 10})
        game_state.player_hand.append({'suit': 'diamonds', 'name': 'Queen', 'value': 10})
        # Set next card to cause bust
        game_state.deck.append({'suit': 'clubs', 'name': 'Jack', 'value': 10})
        db.session.commit()
        response, status_code = player_action(self.user, 'hit')
        db.session.refresh(game_state)
        self.assertEqual(status_code, 200)
        self.assertTrue(game_state.game_over)
        self.assertEqual(game_state.message,  'You lost.')

    def test_player_hit_blackjack(self):
        # Test hitting to reach 21
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand
        game_state.player_hand.clear()
        game_state.player_hand.append({'suit': 'hearts', 'name': '9', 'value': 9})
        game_state.player_hand.append({'suit': 'diamonds', 'name': '2', 'value': 2})
        # Set next card to reach 21
        game_state.deck.append({'suit': 'clubs', 'name': 'Queen', 'value': 10})
        db.session.commit()
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)
        # Adjusted expected message
        self.assertEqual(game_state.message, 'You won!')


    def test_player_stand(self):
        # Start a game and perform a stand action
        start_game(self.user, 50)
        response, status_code = player_action(self.user, 'stand')
        self.assertEqual(status_code, 200)
        self.assertIn(response['message'], ['You won!', 'You lost.', "It's a tie."])

    def test_player_double_down(self):
        # Start a game and perform a double-down action
        start_game(self.user, 50)
        initial_coins = self.user.coins  # Should be 450 after initial wager
        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 200)
        # Since the game ends immediately after double-down, update expected coins
        expected_coins = initial_coins - 50 + (200 if self.user.coins > initial_coins else 0)
        self.assertEqual(self.user.coins, expected_coins)


    def test_player_double_down_insufficient_coins(self):
        # Test double down with insufficient coins
        self.user.coins = 50
        db.session.commit()
        start_game(self.user, 50)
        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Insufficient coins to double down')

    def test_player_split(self):
        # Start a game
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Ensure the object is attached to the session
        db.session.add(game_state)
        db.session.commit()
        # Modify player_hand in-place
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': '8', 'value': 8},
            {'suit': 'diamonds', 'name': '8', 'value': 8},
        ])
        db.session.flush()  # Ensure session is aware of changes
        initial_coins = self.user.coins
        response, status_code = player_action(self.user, 'split')
        self.assertEqual(status_code, 200)
        db.session.refresh(game_state)  # Refresh from the database
        self.assertTrue(game_state.split)
        self.assertEqual(len(game_state.player_hand), 1)
        self.assertEqual(len(game_state.player_second_hand), 1)
        self.assertEqual(self.user.coins, initial_coins - 50)


    def test_player_split_invalid(self):
        # Test split action with invalid hand
        start_game(self.user, 50)
        response, status_code = player_action(self.user, 'split')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Cannot split: Cards do not have the same value')

    def test_dealer_turn(self):
        # Test dealer's turn logic
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        dealer_turn(game_state)
        dealer_value = calculate_hand_value(game_state.dealer_hand)
        self.assertTrue(dealer_value >= 17)

    def test_determine_winner_player_win(self):
        # Test determine winner when player wins
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control hands
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '9', 'value': 9},
        ])
        game_state.dealer_hand.clear()
        game_state.dealer_hand.extend([
            {'suit': 'clubs', 'name': '7', 'value': 7},
            {'suit': 'spades', 'name': '8', 'value': 8},
        ])
        db.session.commit()
        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, 'You won!')
        self.assertEqual(self.user.coins, 550)

    def test_determine_winner_tie(self):
        # Test determine winner when it's a tie
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control hands
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '7', 'value': 7},
        ])
        game_state.dealer_hand.clear()
        game_state.dealer_hand.extend([
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '8', 'value': 8},
        ])
        db.session.commit()
        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, "It's a tie.")
        self.assertEqual(self.user.coins, 500)  # Wager returned

    def test_compare_hands(self):
        # Test compare_hands function
        self.assertEqual(compare_hands(22, 18), 'lose')  # Player bust
        self.assertEqual(compare_hands(20, 22), 'win')   # Dealer bust
        self.assertEqual(compare_hands(19, 18), 'win')
        self.assertEqual(compare_hands(18, 19), 'lose')
        self.assertEqual(compare_hands(20, 20), 'tie')

    def test_player_action_invalid(self):
        # Test invalid player action
        start_game(self.user, 50)
        response, status_code = player_action(self.user, 'invalid_action')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Invalid action')

    def test_player_action_no_active_game(self):
        # Test player action when there is no active game
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 400)
        self.assertIn('No active game', response.get('message', ''))

    def test_double_down_win(self):
        # Test double down and win
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand
        game_state.player_hand.clear()
        game_state.player_hand.append({'suit': 'hearts', 'name': '5', 'value': 5})
        game_state.player_hand.append({'suit': 'diamonds', 'name': '6', 'value': 6})
        # Set next card to reach 21
        game_state.deck.append({'suit': 'spades', 'name': 'King', 'value': 10})
        db.session.commit()

        # Refresh user to get updated coins after starting the game
        db.session.refresh(self.user)
        initial_coins = self.user.coins  # Should be 450 after initial wager

        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 200)

        # Refresh user to get updated coins after game action
        db.session.refresh(self.user)
        # Correct expected coins calculation
        expected_coins = initial_coins - 50 + 200  # 450 - 50 + 200 = 600
        self.assertEqual(self.user.coins, expected_coins)



    def test_player_hit_after_double_down(self):
        # Ensure player cannot hit after double down
        start_game(self.user, 50)
        response, status_code = player_action(self.user, 'double_down')
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'No active game')

    def test_player_cannot_double_down_after_hit(self):
        # Ensure player cannot double down after hitting
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand to avoid busting
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': '2', 'value': 2},
            {'suit': 'diamonds', 'name': '3', 'value': 3},
        ])
        # Set next card
        game_state.deck.append({'suit': 'clubs', 'name': '4', 'value': 4})
        db.session.commit()
        response, status_code = player_action(self.user, 'hit')
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        if game_state and not game_state.game_over:
            response, status_code = player_action(self.user, 'double_down')
            self.assertEqual(status_code, 400)
            self.assertEqual(response['message'], 'Cannot double down at this stage')
        else:
            self.fail('Game ended unexpectedly after hit.')


    def test_player_cannot_split_after_hit(self):
        # Ensure player cannot split after hitting
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand to avoid busting
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': '6', 'value': 6},
            {'suit': 'diamonds', 'name': '7', 'value': 7},
        ])
        # Set next card
        game_state.deck.append({'suit': 'clubs', 'name': '2', 'value': 2})
        db.session.commit()
        response, status_code = player_action(self.user, 'hit')
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        if game_state and not game_state.game_over:
            response, status_code = player_action(self.user, 'split')
            self.assertEqual(status_code, 400)
            self.assertEqual(response['message'], 'Cannot split: Hand does not contain exactly two cards')


    def test_player_hit_with_multiple_aces(self):
        # Test player hand value with multiple aces
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Set player's hand with multiple aces
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': 'Ace', 'value': 11},
            {'suit': 'diamonds', 'name': 'Ace', 'value': 11},
            {'suit': 'clubs', 'name': 'Ace', 'value': 11},
        ])
        db.session.commit()
        player_value = calculate_hand_value(game_state.player_hand)
        self.assertEqual(player_value, 13)

    def test_dealer_busts(self):
        # Test scenario where dealer busts
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control dealer's hand to bust
        game_state.dealer_hand.clear()
        game_state.dealer_hand.extend([
            {'suit': 'hearts', 'name': 'King', 'value': 10},
            {'suit': 'diamonds', 'name': 'Queen', 'value': 10},
            {'suit': 'clubs', 'name': '3', 'value': 3},
        ])
        db.session.commit()
        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, 'You won!')
        self.assertEqual(self.user.coins, 550)

    def test_player_busts(self):
        # Test scenario where player busts
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Control player's hand to bust
        game_state.player_hand.clear()
        game_state.player_hand.extend([
            {'suit': 'hearts', 'name': 'King', 'value': 10},
            {'suit': 'diamonds', 'name': 'Queen', 'value': 10},
            {'suit': 'clubs', 'name': '3', 'value': 3},
        ])
        db.session.commit()
        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, 'You lost.')
        self.assertEqual(self.user.coins, 450)

    def test_game_cleanup_after_completion(self):
        # Ensure game state is cleaned up after game over
        start_game(self.user, 50)
        response, status_code = player_action(self.user, 'stand')
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()
        # Since we are no longer deleting game_state, it should still exist
        self.assertIsNotNone(game_state)
        self.assertTrue(game_state.game_over)

    def test_player_hits_21(self):
        # Start the game with a wager
        start_game(self.user, 50)
        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()

        # Set player's initial hand to sum to 19
        game_state.player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '9', 'value': 9}
        ]

        # Set dealer's hand to sum to 16 (so dealer must hit and won't reach 21)
        game_state.dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]

        # Control the deck so that the player will draw a 2 to reach 21
        game_state.deck = [
            {'suit': 'spades', 'name': '3', 'value': 3},  # Additional card for the dealer
            {'suit': 'hearts', 'name': '2', 'value': 2},

        ]

        db.session.commit()

        # Perform hit action for player to reach 21
        player_action(self.user, 'hit')

        # Refresh game state to get updated data
        db.session.refresh(game_state)

        # Debug information
        print(f"Game over: {game_state.game_over}")
        print(f"Message: {game_state.message}")
        print(f"Player hand: {game_state.player_hand}")
        print(f"Player hand value: {calculate_hand_value(game_state.player_hand)}")

        # Assert that the game is over and the player won
        self.assertTrue(game_state.game_over, "Game should be over when player hits 21")
        self.assertEqual(game_state.message, 'You won!')


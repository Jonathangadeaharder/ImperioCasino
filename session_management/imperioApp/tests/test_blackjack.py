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

    def set_game_state(
            self,
            wager,
            player_hand=None,
            dealer_hand=None,
            deck=None,
            split=False,
            player_second_hand=None,
            game_over=False,
            message=''
    ):
        """
        Helper method to set up the game state deterministically.
        Assumes the deck is a stack where the last element is the next card to be drawn.
        """
        # Start the game with the specified wager
        response, status_code = start_game(self.user, wager)
        self.assertEqual(status_code, 200)
        self.assertFalse(response['game_over'])
        self.assertEqual(response['current_wager'], wager)

        game_state = BlackjackGameState.query.filter_by(user_id=self.user.id).first()

        # Set player hand if provided
        if player_hand is not None:
            game_state.player_hand = player_hand

        # Set dealer hand if provided
        if dealer_hand is not None:
            game_state.dealer_hand = dealer_hand

        # Set deck if provided
        if deck is not None:
            # Ensure the last element is the next card to draw
            game_state.deck = deck.copy()

        # Set split status and second hand if provided
        game_state.split = split
        if player_second_hand is not None:
            game_state.player_second_hand = player_second_hand

        # Set game_over status and message
        game_state.game_over = game_over
        game_state.message = message

        db.session.commit()
        return game_state

    def test_start_game_valid_wager(self):
        # Test starting a game with a valid wager
        wager = 50
        response, status_code = start_game(self.user, wager)
        self.assertEqual(status_code, 200)
        self.assertFalse(response['game_over'])
        self.assertEqual(len(response['player_hand']), 2)
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
        """
        Test performing a 'hit' action.
        Player should receive a specific card without busting.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '2', 'value': 2},
            {'suit': 'diamonds', 'name': '3', 'value': 3}
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup: Next card is '5' for player hit, followed by extra cards for dealer if needed
        deck = [
            {'suit': 'diamonds', 'name': '6', 'value': 6},  # Additional buffer
            {'suit': 'hearts', 'name': '4', 'value': 4},     # Extra for dealer
            {'suit': 'clubs', 'name': '5', 'value': 5}       # Player's hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        initial_hand_size = len(game_state.player_hand)
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)
        self.assertEqual(len(game_state.player_hand), initial_hand_size + 1)
        # Verify that the player received the '5' card
        self.assertEqual(game_state.player_hand[-1], {'suit': 'clubs', 'name': '5', 'value': 5})
        self.assertFalse(game_state.game_over)

    def test_player_hit_bust(self):
        """
        Test performing a 'hit' action that causes the player to bust.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': 'King', 'value': 10},
            {'suit': 'diamonds', 'name': 'Queen', 'value': 10}
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup: Next card is 'Jack' causing bust
        deck = [
            {'suit': 'diamonds', 'name': '3', 'value': 3},   # Additional buffer
            {'suit': 'hearts', 'name': '2', 'value': 2},      # Extra buffer
            {'suit': 'clubs', 'name': 'Jack', 'value': 10}    # Player's hit causing bust (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)
        self.assertTrue(game_state.game_over)
        self.assertEqual(game_state.message, 'Perdiste.')
        # Player's coins should remain at 500 - wager = 450
        self.assertEqual(self.user.coins, 500 - wager)

    def test_player_hit_blackjack(self):
        """
        Test performing a 'hit' action that brings the player's hand to Blackjack (21).
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '9', 'value': 9},
            {'suit': 'diamonds', 'name': '2', 'value': 2}
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup:
        # Player's hit: 'Queen' to reach 21
        # Dealer's hits: '4' and '4' to reach 20
        deck = [
            {'suit': 'diamonds', 'name': '4', 'value': 4},   # Dealer's second hit
            {'suit': 'hearts', 'name': '4', 'value': 4},     # Dealer's first hit
            {'suit': 'clubs', 'name': 'Queen', 'value': 10}  # Player's hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)

        # Assertions
        self.assertTrue(game_state.game_over)
        self.assertEqual(game_state.message, 'Ganaste!')
        self.assertEqual(len(game_state.player_hand), 3)
        self.assertEqual(game_state.player_hand[-1], {'suit': 'clubs', 'name': 'Queen', 'value': 10})
        self.assertEqual(len(game_state.dealer_hand), 4)
        self.assertEqual(game_state.dealer_hand[2], {'suit': 'hearts', 'name': '4', 'value': 4})
        self.assertEqual(game_state.dealer_hand[3], {'suit': 'diamonds', 'name': '4', 'value': 4})
        dealer_total = calculate_hand_value(game_state.dealer_hand)
        self.assertEqual(dealer_total, 20)
        # Player wins: coins increase by the wager amount (assuming double payout)
        self.assertEqual(self.user.coins, 500 - wager + wager * 2)  # 500 - 50 + 100 = 550

    def test_player_stand(self):
        """
        Test performing a 'stand' action.
        Dealer draws a card to reach a total of 18, player has 17.
        Dealer should win.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '7', 'value': 7}
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup:
        # Dealer's hit: '2' to reach 18
        # Extra cards to prevent deck exhaustion
        deck = [
            {'suit': 'clubs', 'name': '4', 'value': 4},       # Additional buffer
            {'suit': 'diamonds', 'name': '3', 'value': 3},    # Extra buffer
            {'suit': 'hearts', 'name': '2', 'value': 2}       # Dealer's hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        response, status_code = player_action(self.user, 'stand')
        self.assertEqual(status_code, 200)

        # After dealer's turn:
        # Dealer's initial total: 16 (9 + 7)
        # Dealer hits and gets '2', total becomes 18
        # Player's total: 17
        # Dealer wins
        self.assertEqual(response['message'], 'Perdiste.')
        # Player's coins should remain at 500 - wager = 450
        self.assertEqual(self.user.coins, 500 - wager)

    def test_player_double_down(self):
        """
        Test performing a 'double_down' action.
        Player doubles the wager, receives one additional card, and stands.
        Dealer's turn is simulated to determine the outcome.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '5', 'value': 5},
            {'suit': 'diamonds', 'name': '6', 'value': 6}
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup:
        # Player's double_down hit: 'King' to reach 21
        # Dealer's potential hits: '3' to reach 19
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},     # Additional buffer
            {'suit': 'hearts', 'name': '3', 'value': 3},       # Dealer's hit
            {'suit': 'spades', 'name': 'King', 'value': 10}    # Player's double_down hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        initial_coins = self.user.coins  # 500 - 50 = 450

        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)
        db.session.refresh(self.user)

        # After double down:
        # Player's wager is doubled to 100
        # Player's total becomes 21 (5 + 6 + 10)
        # Dealer's total is 16, must hit and reach 19 (9 + 7 + 3)
        self.assertTrue(game_state.game_over)
        self.assertEqual(game_state.message, 'Ganaste!')
        # Player's coins should increase by double the wager
        self.assertEqual(self.user.coins, initial_coins - wager + wager * 4)  # 450 - 50 + 200 = 600

    def test_player_double_down_insufficient_coins(self):
        """
        Test performing a 'double_down' action with insufficient coins.
        """
        self.user.coins = 50
        db.session.commit()
        wager = 50
        # Setup game state without specifying hands and deck
        game_state = self.set_game_state(wager)

        # Attempt to double down, which requires an additional 50 coins
        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Insufficient coins to double down')

    def test_player_split(self):
        """
        Test performing a 'split' action.
        Player splits two identical cards into two separate hands.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '8', 'value': 8},
            {'suit': 'diamonds', 'name': '8', 'value': 8},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup:
        # First split hand draws '3', second split hand draws '4'
        # Extra cards to prevent deck exhaustion
        deck = [
            {'suit': 'clubs', 'name': '5', 'value': 5},       # Additional buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},    # Second split hand's new card
            {'suit': 'hearts', 'name': '3', 'value': 3}       # First split hand's new card (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        initial_coins = self.user.coins  # 500 - 50 = 450

        response, status_code = player_action(self.user, 'split')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)
        self.assertTrue(game_state.split)
        self.assertEqual(len(game_state.player_hand), 1)
        self.assertEqual(len(game_state.player_second_hand), 1)
        # Player's coins should be deducted by an additional wager for the split
        self.assertEqual(self.user.coins, initial_coins - wager)  # 450 - 50 = 400

    def test_player_split_invalid(self):
        """
        Test attempting to perform a 'split' action with non-identical cards.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '8', 'value': 8},
            {'suit': 'diamonds', 'name': '9', 'value': 9},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Deck setup (doesn't matter in this case as split should fail before drawing)
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},     # Additional buffer
            {'suit': 'hearts', 'name': '3', 'value': 3},       # Extra buffer
            {'suit': 'spades', 'name': '5', 'value': 5}        # Additional buffer
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        response, status_code = player_action(self.user, 'split')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Cannot split: Cards do not have the same value')

    def test_dealer_turn(self):
        """
        Test the dealer's turn logic.
        Dealer should hit until reaching at least 17.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '7', 'value': 7}
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '6', 'value': 6},
            {'suit': 'spades', 'name': '7', 'value': 7}
        ]
        # Dealer's initial total: 13
        # Dealer hits and draws '4' to reach 17
        # Deck setup:
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Additional buffer
            {'suit': 'diamonds', 'name': '3', 'value': 3},     # Extra buffer
            {'suit': 'hearts', 'name': '4', 'value': 4}        # Dealer's hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        dealer_turn(game_state)
        dealer_value = calculate_hand_value(game_state.dealer_hand)
        self.assertTrue(dealer_value >= 17)
        self.assertFalse(game_state.game_over)  # Game should not be over until player stands or busts

    def test_determine_winner_player_win(self):
        """
        Test determining the winner when the player wins.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '9', 'value': 9},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '7', 'value': 7},
            {'suit': 'spades', 'name': '8', 'value': 8},
        ]
        # Dealer's total: 15
        # Assuming dealer stands or busts after their turn
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '3', 'value': 3},     # Additional buffer
            {'suit': 'hearts', 'name': '4', 'value': 4}        # Extra buffer
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, 'Ganaste!')
        self.assertEqual(self.user.coins, 500 - wager + wager * 2)  # 500 - 50 + 100 = 550

    def test_determine_winner_tie(self):
        """
        Test determining the winner when there's a tie.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '7', 'value': 7},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '8', 'value': 8},
        ]
        # Both player and dealer total to 17
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '3', 'value': 3},     # Additional buffer
            {'suit': 'hearts', 'name': '4', 'value': 4}        # Extra buffer
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, "It's a tie.")
        self.assertEqual(self.user.coins, 500)  # Wager returned

    def test_compare_hands(self):
        """
        Test the compare_hands function with various scenarios.
        """
        self.assertEqual(compare_hands(22, 18), 'lose')  # Player bust
        self.assertEqual(compare_hands(20, 22), 'win')   # Dealer bust
        self.assertEqual(compare_hands(19, 18), 'win')
        self.assertEqual(compare_hands(18, 19), 'lose')
        self.assertEqual(compare_hands(20, 20), 'tie')

    def test_player_action_invalid(self):
        """
        Test performing an invalid player action.
        """
        wager = 50
        self.set_game_state(wager)
        response, status_code = player_action(self.user, 'invalid_action')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Invalid action')

    def test_player_action_no_active_game(self):
        """
        Test performing a player action when there's no active game.
        """
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 400)
        self.assertIn('No active game', response.get('message', ''))

    def test_double_down_win(self):
        """
        Test performing a 'double_down' action that results in a win.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '5', 'value': 5},
            {'suit': 'diamonds', 'name': '6', 'value': 6},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup:
        # Player's double_down hit: 'King' to reach 21
        # Dealer's potential hit: '3' to reach 19
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},     # Additional buffer
            {'suit': 'hearts', 'name': '3', 'value': 3},       # Dealer's hit
            {'suit': 'spades', 'name': 'King', 'value': 10}    # Player's double_down hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        initial_coins = self.user.coins  # 500 - 50 = 450

        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)
        db.session.refresh(self.user)

        # After double down:
        # Player's total becomes 21 (5 + 6 + 10)
        # Dealer's total is 19 (9 + 7 + 3)
        # Player wins
        self.assertTrue(game_state.game_over)
        self.assertEqual(game_state.message, 'Ganaste!')
        self.assertEqual(self.user.coins, initial_coins - wager + wager * 4)  # 450 - 50 + 200 = 600

    def test_player_hit_after_double_down(self):
        """
        Ensure that the player cannot perform a 'hit' action after doubling down.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '5', 'value': 5},
            {'suit': 'diamonds', 'name': '6', 'value': 6},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup:
        # Player's double_down hit: 'King' to reach 21
        # Dealer's potential hit: '3' to reach 19
        # Extra buffer cards
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},     # Additional buffer
            {'suit': 'hearts', 'name': '3', 'value': 3},       # Dealer's hit
            {'suit': 'spades', 'name': 'King', 'value': 10}    # Player's double_down hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        # Perform double_down
        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 200)

        # Attempt to hit after double_down
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'No active game')

    def test_player_cannot_double_down_after_hit(self):
        """
        Ensure that the player cannot perform a 'double_down' action after hitting.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '2', 'value': 2},
            {'suit': 'diamonds', 'name': '3', 'value': 3},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup:
        # Player's hit: '4' to reach 6
        # Dealer's potential hit: '5' to reach 14
        # Extra buffer cards
        deck = [
            {'suit': 'clubs', 'name': '2', 'value': 2},        # Further buffer
            {'suit': 'diamonds', 'name': '6', 'value': 6},     # Additional buffer
            {'suit': 'hearts', 'name': '5', 'value': 5},       # Dealer's hit
            {'suit': 'clubs', 'name': '4', 'value': 4}         # Player's hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        # Perform hit
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)

        # Attempt to double_down after hit
        response, status_code = player_action(self.user, 'double_down')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Cannot double down at this stage')

    def test_player_cannot_split_after_hit(self):
        """
        Ensure that the player cannot perform a 'split' action after hitting.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '6', 'value': 6},
            {'suit': 'diamonds', 'name': '7', 'value': 7},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup:
        # Player's hit: '2' to reach 8
        # Dealer's potential hit: '3' to reach 8
        # Extra buffer cards
        deck = [
            {'suit': 'clubs', 'name': '5', 'value': 5},        # Further buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},     # Additional buffer
            {'suit': 'hearts', 'name': '3', 'value': 3},       # Dealer's hit
            {'suit': 'clubs', 'name': '2', 'value': 2}         # Player's hit (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        # Perform hit
        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)

        # Attempt to split after hit
        response, status_code = player_action(self.user, 'split')
        self.assertEqual(status_code, 400)
        self.assertEqual(response['message'], 'Cannot split: Hand does not contain exactly two cards')

    def test_player_hit_with_multiple_aces(self):
        """
        Test handling of multiple aces in the player's hand.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': 'Ace', 'value': 11},
            {'suit': 'diamonds', 'name': 'Ace', 'value': 11},
            {'suit': 'clubs', 'name': 'Ace', 'value': 11},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup: No hits required, but include extra cards
        deck = [
            {'suit': 'clubs', 'name': '4', 'value': 4},        # Additional buffer
            {'suit': 'diamonds', 'name': '3', 'value': 3},     # Additional buffer
            {'suit': 'hearts', 'name': '2', 'value': 2},       # Extra buffer
            {'suit': 'spades', 'name': '5', 'value': 5}        # Further buffer
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        db.session.refresh(game_state)
        player_value = calculate_hand_value(game_state.player_hand)
        self.assertEqual(player_value, 13)  # Adjusted for multiple aces

    def test_dealer_busts(self):
        """
        Test scenario where the dealer busts.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '9', 'value': 9},
        ]
        dealer_hand = [
            {'suit': 'hearts', 'name': 'King', 'value': 10},
            {'suit': 'diamonds', 'name': 'Queen', 'value': 10},
            {'suit': 'clubs', 'name': '3', 'value': 3},  # Dealer's total: 23 (bust)
        ]
        # Deck setup: Dealer already has a bust
        deck = [
            {'suit': 'clubs', 'name': '6', 'value': 6},        # Further buffer
            {'suit': 'diamonds', 'name': '5', 'value': 5},     # Additional buffer
            {'suit': 'hearts', 'name': '4', 'value': 4}        # Extra buffer
        ]
        game_state = self.set_game_state(
            wager, player_hand, dealer_hand, deck, game_over=True, message='Ganaste!'
        )

        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, 'Ganaste!')
        self.assertEqual(self.user.coins, 500 - wager + wager * 2)  # 500 - 50 + 100 = 550

    def test_player_busts(self):
        """
        Test scenario where the player busts.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': 'King', 'value': 10},
            {'suit': 'diamonds', 'name': 'Queen', 'value': 10},
            {'suit': 'clubs', 'name': '3', 'value': 3},  # Player's total: 23 (bust)
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '5', 'value': 5},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup: Dealer's turn won't matter as player already busts
        deck = [
            {'suit': 'clubs', 'name': '6', 'value': 6},        # Further buffer
            {'suit': 'diamonds', 'name': '5', 'value': 5},     # Additional buffer
            {'suit': 'hearts', 'name': '4', 'value': 4}        # Extra buffer
        ]
        game_state = self.set_game_state(
            wager, player_hand, dealer_hand, deck, game_over=True, message='Perdiste.'
        )

        determine_winner(game_state, self.user)
        self.assertEqual(game_state.message, 'Perdiste.')
        self.assertEqual(self.user.coins, 500 - wager)  # 500 - 50 = 450

    def test_player_hits_21(self):
        """
        Test performing a 'hit' action that brings the player's hand to exactly 21.
        """
        wager = 50
        player_hand = [
            {'suit': 'hearts', 'name': '10', 'value': 10},
            {'suit': 'diamonds', 'name': '9', 'value': 9},
        ]
        dealer_hand = [
            {'suit': 'clubs', 'name': '9', 'value': 9},
            {'suit': 'spades', 'name': '7', 'value': 7},
        ]
        # Deck setup:
        # Player's hit: '2' to reach 21
        # Dealer's potential hit: '3' to reach 19
        # Extra buffer cards
        deck = [
            {'suit': 'clubs', 'name': '5', 'value': 5},        # Further buffer
            {'suit': 'diamonds', 'name': '4', 'value': 4},     # Additional buffer
            {'suit': 'spades', 'name': '3', 'value': 3},       # Dealer's hit
            {'suit': 'hearts', 'name': '2', 'value': 2}        # Player's hit to reach 21 (last element)
        ]
        game_state = self.set_game_state(wager, player_hand, dealer_hand, deck)

        response, status_code = player_action(self.user, 'hit')
        self.assertEqual(status_code, 200)

        db.session.refresh(game_state)

        # Assertions
        self.assertTrue(game_state.game_over, "Game should be over when player hits 21")
        self.assertEqual(game_state.message, 'Ganaste!')
        self.assertEqual(len(game_state.player_hand), 3)
        self.assertEqual(game_state.player_hand[-1], {'suit': 'hearts', 'name': '2', 'value': 2})
        # Player's coins should increase by the wager amount (assuming double payout)
        self.assertEqual(self.user.coins, 500 - wager + wager * 2)  # 500 - 50 + 100 = 550

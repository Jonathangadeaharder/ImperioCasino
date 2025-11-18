# game_logic/blackjack.py

import random
from ..utils.models import BlackjackGameState
from ..utils.services import update_user_coins
from .. import db
import logging

# Define the card deck
deck = [
    {'suit': suit, 'name': name, 'value': value}
    for suit in ['hearts', 'diamond', 'clubs', 'spades']
    for name, value in [
        ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6),
        ('7', 7), ('8', 8), ('9', 9), ('10', 10),
        ('Jack', 10), ('Queen', 10), ('King', 10), ('Ace', 11)
    ]
]

def shuffle_deck():
    return random.sample(deck * 6, len(deck) * 6)  # Using 6 decks

def calculate_hand_value(hand):
    value = sum(card['value'] for card in hand)
    aces = sum(1 for card in hand if card['name'] == 'Ace')
    while value > 21 and aces:
        value -= 10  # Convert an ace from 11 to 1
        aces -= 1
    return value

def start_game(user, wager):
    # Validate wager
    if wager <= 0:
        return {'message': 'Invalid wager amount', 'game_over': True}, 400

    # Lock user row for update to prevent race conditions
    from sqlalchemy.orm import with_for_update
    from ..utils.models import User
    locked_user = db.session.query(User).with_for_update().filter_by(id=user.id).first()

    if not locked_user:
        return {'message': 'User not found', 'game_over': True}, 404

    if locked_user.coins < wager:
        return {'message': 'Insufficient coins', 'game_over': True}, 400

    # Terminate any existing active games for the user
    active_games = BlackjackGameState.query.filter_by(user_id=user.id, game_over=False).all()
    for game in active_games:
        game.game_over = True
    db.session.commit()

    # Deduct initial wager from user's coins
    locked_user.coins -= wager
    db.session.commit()

    # Initialize a new game state
    game_state = BlackjackGameState(
        user_id=locked_user.id,
        deck=shuffle_deck(),
        dealer_hand=[],
        player_hand=[],
        player_coins=locked_user.coins,
        current_wager=wager,
        game_over=False,
        message='',
        player_stood=False,
        double_down=False,
        split=False,
        player_second_hand=[],
        current_hand='first'
    )

    # Deal initial cards
    game_state.player_hand.append(game_state.deck.pop())
    game_state.dealer_hand.append(game_state.deck.pop())
    game_state.player_hand.append(game_state.deck.pop())
    game_state.dealer_hand.append(game_state.deck.pop())

    db.session.add(game_state)
    db.session.commit()

    return game_state.to_dict(), 200

def player_action(user, action):
    game_state = BlackjackGameState.query.filter_by(user_id=user.id, game_over=False).first()
    if not game_state:
        return {'message': 'No active game'}, 400

    if action == 'hit':
        return player_hit(user, game_state)
    elif action == 'stand':
        return player_stand(game_state, user)
    elif action == 'double_down':
        return player_double_down(game_state, user)
    elif action == 'split':
        # Capture both response and status code
        response, status_code = player_split(game_state, user)
        return response, status_code
    else:
        return {'message': 'Invalid action'}, 400


def player_hit(user, game_state):
    if game_state.split:
        hand = game_state.player_second_hand if game_state.current_hand == 'second' else game_state.player_hand
    else:
        hand = game_state.player_hand

    hand.append(game_state.deck.pop())
    player_value = calculate_hand_value(hand)

    logging.debug(f"Player hit. Hand value: {player_value}")

    if player_value > 21:
        if game_state.split and game_state.current_hand == 'first':
            game_state.current_hand = 'second'
            game_state.player_stood = False
        else:
            game_state.game_over = True
            dealer_turn(game_state)
            determine_winner(game_state, user)
    elif player_value == 21:
        game_state.player_stood = True
        game_state.game_over = True
        dealer_turn(game_state)
        determine_winner(game_state, user)
    elif game_state.split and game_state.current_hand == 'first':
        # If split and first hand, switch to second hand
        game_state.current_hand = 'second'
        game_state.player_stood = False

    db.session.commit()
    return game_state.to_dict(), 200


def player_stand(game_state, user):
    if game_state.split and game_state.current_hand == 'first':
        game_state.current_hand = 'second'
        game_state.player_stood = False
    else:
        # Dealer's turn
        dealer_turn(game_state)
        determine_winner(game_state, user)
        game_state.game_over = True

    db.session.commit()
    return game_state.to_dict(), 200


def player_double_down(game_state, user):
    if len(game_state.player_hand) > 2 or game_state.double_down or game_state.split or game_state.player_stood:
        return {'message': 'Cannot double down at this stage'}, 400

    if user.coins < game_state.current_wager:
        return {'message': 'Insufficient coins to double down'}, 400

    user.coins -= game_state.current_wager
    update_user_coins(user, user.coins)
    game_state.current_wager *= 2
    game_state.player_coins = user.coins
    game_state.double_down = True

    game_state.player_hand.append(game_state.deck.pop())
    player_value = calculate_hand_value(game_state.player_hand)

    if player_value > 21:
        game_state.message = 'Bust! You exceeded 21.'
        game_state.game_over = True
    else:
        game_state.player_stood = True
        dealer_turn(game_state)
        # Determine outcome
        determine_winner(game_state, user)

    db.session.commit()
    return game_state.to_dict(), 200

def player_split(game_state, user):
    hand = game_state.player_hand
    # Check if hand has exactly two cards
    if len(hand) != 2:
        return {'message': 'Cannot split: Hand does not contain exactly two cards'}, 400
    # Check if both cards have the same value
    if hand[0]['value'] != hand[1]['value']:
        return {'message': 'Cannot split: Cards do not have the same value'}, 400
    # Check if user has enough coins
    if user.coins < game_state.current_wager:
        return {'message': 'Cannot split: Insufficient coins'}, 400

    user.coins -= game_state.current_wager
    update_user_coins(user, user.coins)
    game_state.player_coins = user.coins
    game_state.split = True

    # Move one card to player_second_hand
    card_to_move = game_state.player_hand.pop()
    if game_state.player_second_hand is None:
        game_state.player_second_hand = []
    game_state.player_second_hand.append(card_to_move)

    db.session.commit()
    return game_state.to_dict(), 200



def dealer_turn(game_state):
    dealer_value = calculate_hand_value(game_state.dealer_hand)
    while dealer_value < 17:
        # Dealer hits
        game_state.dealer_hand.append(game_state.deck.pop())
        dealer_value = calculate_hand_value(game_state.dealer_hand)
    logging.debug(f"Dealer's final hand: {game_state.dealer_hand} with value: {dealer_value}")

def determine_winner(game_state, user):
    dealer_value = calculate_hand_value(game_state.dealer_hand)
    game_state.dealer_value = dealer_value

    if game_state.split:
        outcomes = []
        for hand_attr in ['player_hand', 'player_second_hand']:
            hand = getattr(game_state, hand_attr)
            player_value = calculate_hand_value(hand)
            outcome = compare_hands(player_value, dealer_value)
            outcomes.append(outcome)
            if outcome == 'win':
                user.coins += game_state.current_wager * 2
            elif outcome == 'tie':
                user.coins += game_state.current_wager

        update_user_coins(user, user.coins)
        game_state.player_coins = user.coins
        game_state.message = f'First hand: {outcomes[0]}, Second hand: {outcomes[1]}'
    else:
        player_value = calculate_hand_value(game_state.player_hand)
        outcome = compare_hands(player_value, dealer_value)

        if outcome == 'win':
            user.coins += game_state.current_wager * 2
            game_state.message = 'Ganaste!'
        elif outcome == 'tie':
            user.coins += game_state.current_wager
            game_state.message = 'It\'s a tie.'
        else:
            game_state.message = 'Perdiste.'

        update_user_coins(user, user.coins)
        game_state.player_coins = user.coins

    game_state.game_over = True
    db.session.commit()

def compare_hands(player_value, dealer_value):
    if player_value > 21:
        return 'lose'
    elif dealer_value > 21:
        return 'win'
    elif player_value > dealer_value:
        return 'win'
    elif player_value == dealer_value:
        return 'tie'
    else:
        return 'lose'

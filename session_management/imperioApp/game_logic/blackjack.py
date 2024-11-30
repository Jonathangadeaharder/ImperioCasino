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
        return {'message': 'Invalid wager amount', 'game_over': True}
    if user.coins < wager:
        return {'message': 'Insufficient coins', 'game_over': True}

    # Deduct initial wager from user's coins
    user.coins -= wager
    update_user_coins(user, user.coins)

    game_state = BlackjackGameState(
        user_id=user.id,
        deck=shuffle_deck(),
        dealer_hand=[],
        player_hand=[],
        player_coins=user.coins,
        current_wager=wager,
        game_over=False,
        message='',
        player_stood=False,
        double_down=False,
        split=False,
        player_second_hand=[],
        current_hand='first'
    )

    game_state.player_hand.append(game_state.deck.pop())
    game_state.dealer_hand.append(game_state.deck.pop())
    game_state.player_hand.append(game_state.deck.pop())
    game_state.dealer_hand.append(game_state.deck.pop())

    db.session.add(game_state)
    db.session.commit()

    return game_state.to_dict()

def player_action(user, action):
    logging.info(f"User: {user}, User ID: {user.username}")
    game_state = BlackjackGameState.query.filter_by(user_id=user.id, game_over=False).first()
    if not game_state:
        return {'message': 'No active game', 'game_over': True}

    if action == 'hit':
        return player_hit(game_state)
    elif action == 'stand':
        return player_stand(game_state, user)
    elif action == 'double_down':
        return player_double_down(game_state, user)
    elif action == 'split':
        return player_split(game_state, user)
    else:
        return {'message': 'Invalid action'}, 400

def player_hit(game_state):
    hand = game_state.player_second_hand if game_state.split and game_state.current_hand == 'second' else game_state.player_hand
    hand.append(game_state.deck.pop())
    player_value = calculate_hand_value(hand)

    if player_value > 21:
        game_state.message = 'Bust! You exceeded 21.'
        game_state.game_over = True
    elif player_value == 21:
        game_state.message = 'You hit 21!'
        game_state.player_stood = True
        dealer_turn(game_state)

    db.session.commit()
    return game_state.to_dict()

def player_stand(game_state, user):
    game_state.player_stood = True

    if game_state.split and game_state.current_hand == 'first':
        game_state.current_hand = 'second'
        game_state.player_stood = False
    else:
        # Dealer's turn
        dealer_turn(game_state)
        determine_winner(game_state, user)

    db.session.commit()
    return game_state.to_dict()

def player_double_down(game_state, user):
    if user.coins < game_state.current_wager:
        return {'message': 'Insufficient coins to double down'}

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
    return game_state.to_dict()

def player_split(game_state, user):
    hand = game_state.player_hand
    if len(hand) != 2 or hand[0]['value'] != hand[1]['value'] or user.coins < game_state.current_wager:
        return {'message': 'Cannot split these cards or insufficient coins'}

    user.coins -= game_state.current_wager
    update_user_coins(user, user.coins)
    game_state.player_coins = user.coins
    game_state.split = True

    game_state.player_second_hand = [hand.pop()]
    hand.append(game_state.deck.pop())
    game_state.player_second_hand.append(game_state.deck.pop())

    db.session.commit()
    return game_state.to_dict()

def dealer_turn(game_state):
    dealer_hand = game_state.dealer_hand
    dealer_value = calculate_hand_value(dealer_hand)

    while dealer_value < 17:
        dealer_hand.append(game_state.deck.pop())
        dealer_value = calculate_hand_value(dealer_hand)

    game_state.dealer_value = dealer_value

def determine_winner(game_state, user):
    dealer_value = calculate_hand_value(game_state.dealer_hand)
    game_state.dealer_value = dealer_value

    if game_state.split:
        outcomes = []
        for hand in ['player_hand', 'player_second_hand']:
            player_value = calculate_hand_value(game_state[hand])
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
            game_state.message = 'You won!'
        elif outcome == 'tie':
            user.coins += game_state.current_wager
            game_state.message = 'It\'s a tie.'
        else:
            game_state.message = 'You lost.'

        update_user_coins(user, user.coins)
        game_state.player_coins = user.coins

    game_state.game_over = True
    db.session.commit()

    # Clean up the game state from the database
    db.session.delete(game_state)
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

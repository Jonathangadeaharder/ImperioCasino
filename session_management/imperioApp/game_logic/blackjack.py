# game_logic/blackjack.py

import random
from flask import session
from ..utils.services import update_user_coins

# Define the card deck
deck = [
    {'suit': suit, 'name': name, 'value': value}
    for suit in ['hearts', 'diamonds', 'clubs', 'spades']
    for name, value in [
        ('2', 2), ('3', 3), ('4', 4), ('5', 5), ('6', 6),
        ('7', 7), ('8', 8), ('9', 9), ('10', 10),
        ('jack', 10), ('queen', 10), ('king', 10), ('ace', 11)
    ]
]

def shuffle_deck():
    return random.sample(deck * 6, len(deck) * 6)  # Using 6 decks

def calculate_hand_value(hand):
    value = sum(card['value'] for card in hand)
    aces = sum(1 for card in hand if card['name'] == 'ace')
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

    # Initialize game state
    game_state = {
        'deck': shuffle_deck(),
        'dealer_hand': [],
        'player_hand': [],
        'player_coins': user.coins,
        'current_wager': wager,
        'game_over': False,
        'message': '',
        'player_stood': False,
        'double_down': False,
        'split': False,
        'player_second_hand': [],
        'current_hand': 'first',  # 'first' or 'second' for split hands
    }

    # Deal initial cards
    game_state['player_hand'].append(game_state['deck'].pop())
    game_state['dealer_hand'].append(game_state['deck'].pop())
    game_state['player_hand'].append(game_state['deck'].pop())
    game_state['dealer_hand'].append(game_state['deck'].pop())

    # Save game state in session
    session['blackjack_state'] = game_state

    return game_state

def player_action(user, action):
    # Retrieve game state
    game_state = session.get('blackjack_state')

    if not game_state or game_state.get('game_over'):
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
    if game_state['split'] and game_state['current_hand'] == 'second':
        hand = game_state['player_second_hand']
    else:
        hand = game_state['player_hand']

    hand.append(game_state['deck'].pop())
    player_value = calculate_hand_value(hand)

    if player_value > 21:
        game_state['message'] = 'Bust! You exceeded 21.'
        game_state['game_over'] = True
    elif player_value == 21:
        game_state['message'] = 'You hit 21!'
        game_state['player_stood'] = True
        dealer_turn(game_state)

    session['blackjack_state'] = game_state
    return game_state

def player_stand(game_state, user):
    game_state['player_stood'] = True

    if game_state['split'] and game_state['current_hand'] == 'first':
        # Move to second hand
        game_state['current_hand'] = 'second'
        game_state['player_stood'] = False
    else:
        # Dealer's turn
        dealer_turn(game_state)
        # Determine outcome
        determine_winner(game_state, user)

    session['blackjack_state'] = game_state
    return game_state

def player_double_down(game_state, user):
    # Double the wager
    if user.coins < game_state['current_wager']:
        return {'message': 'Insufficient coins to double down'}

    user.coins -= game_state['current_wager']
    update_user_coins(user, user.coins)
    game_state['current_wager'] *= 2
    game_state['player_coins'] = user.coins
    game_state['double_down'] = True

    # Player gets one more card and then stands
    game_state['player_hand'].append(game_state['deck'].pop())
    player_value = calculate_hand_value(game_state['player_hand'])

    if player_value > 21:
        game_state['message'] = 'Bust! You exceeded 21.'
        game_state['game_over'] = True
    else:
        game_state['player_stood'] = True
        # Dealer's turn
        dealer_turn(game_state)
        # Determine outcome
        determine_winner(game_state, user)

    session['blackjack_state'] = game_state
    return game_state

def player_split(game_state, user):
    # Validate that player can split
    hand = game_state['player_hand']
    if len(hand) != 2 or hand[0]['value'] != hand[1]['value']:
        return {'message': 'Cannot split these cards'}

    if user.coins < game_state['current_wager']:
        return {'message': 'Insufficient coins to split'}

    user.coins -= game_state['current_wager']
    update_user_coins(user, user.coins)
    game_state['player_coins'] = user.coins
    game_state['split'] = True

    # Split the hand
    game_state['player_second_hand'] = [hand.pop()]
    hand.append(game_state['deck'].pop())  # Draw card for first hand
    game_state['player_second_hand'].append(game_state['deck'].pop())  # Draw card for second hand

    session['blackjack_state'] = game_state
    return game_state

def dealer_turn(game_state):
    dealer_hand = game_state['dealer_hand']
    dealer_value = calculate_hand_value(dealer_hand)

    while dealer_value < 17:
        dealer_hand.append(game_state['deck'].pop())
        dealer_value = calculate_hand_value(dealer_hand)

    game_state['dealer_value'] = dealer_value

def determine_winner(game_state, user):
    dealer_value = calculate_hand_value(game_state['dealer_hand'])
    game_state['dealer_value'] = dealer_value

    if game_state['split']:
        # Evaluate both hands
        outcomes = []
        for hand in ['player_hand', 'player_second_hand']:
            player_value = calculate_hand_value(game_state[hand])
            outcome = compare_hands(player_value, dealer_value)
            outcomes.append(outcome)
            # Update coins
            if outcome == 'win':
                winnings = game_state['current_wager'] * 2
                user.coins += winnings
            elif outcome == 'tie':
                user.coins += game_state['current_wager']

        update_user_coins(user, user.coins)
        game_state['player_coins'] = user.coins
        game_state['message'] = f'First hand: {outcomes[0]}, Second hand: {outcomes[1]}'
    else:
        player_value = calculate_hand_value(game_state['player_hand'])
        outcome = compare_hands(player_value, dealer_value)

        if outcome == 'win':
            winnings = game_state['current_wager'] * 2
            user.coins += winnings
            game_state['message'] = 'You won!'
        elif outcome == 'tie':
            user.coins += game_state['current_wager']
            game_state['message'] = 'It\'s a tie.'
        else:
            game_state['message'] = 'You lost.'

        update_user_coins(user, user.coins)
        game_state['player_coins'] = user.coins

    game_state['game_over'] = True

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

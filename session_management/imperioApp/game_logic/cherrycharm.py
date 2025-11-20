import logging
import random
from enum import Enum

from flask import jsonify

from ..utils.services import increase_user_coins, reduce_user_coins


def spin_reels():
    min_segment = 15
    max_segment = 30
    return [random.randint(min_segment, max_segment) for _ in range(3)]

def get_fruits(stop_segments):
    return [segment_to_fruit(reel, segment) for reel, segment in enumerate(stop_segments)]

def calculate_winnings(fruits):
    return endgame(*fruits)

def ceildiv(a, b):
    return -(a // -b)

class Fruit(Enum):
    CHERRY = "CHERRY"
    LEMON = "LEMON"
    BANANA = "BANANA"
    APPLE = "APPLE"

def segment_to_fruit(reel_index: int, reel_segment: int) -> Fruit:

    reel_segment = ceildiv(reel_segment, 2)
    # Define the mapping for each reel
    fruit_mappings = {
        0: {
            8: Fruit.CHERRY,
            9: Fruit.LEMON,
            10: Fruit.LEMON,
            11: Fruit.BANANA,
            12: Fruit.BANANA,
            13: Fruit.LEMON,
            14: Fruit.APPLE,
            15: Fruit.LEMON,
        },
        1: {
            8: Fruit.LEMON,
            9: Fruit.LEMON,
            10: Fruit.BANANA,
            11: Fruit.APPLE,
            12: Fruit.CHERRY,
            13: Fruit.LEMON,
            14: Fruit.LEMON,
            15: Fruit.APPLE,
        },
        2: {
            8: Fruit.LEMON,
            9: Fruit.LEMON,
            10: Fruit.BANANA,
            11: Fruit.LEMON,
            12: Fruit.CHERRY,
            13: Fruit.APPLE,
            14: Fruit.LEMON,
            15: Fruit.APPLE,
        },
    }

    # Retrieve the fruit based on reel_index and reel_segment
    fruit = fruit_mappings.get(reel_index, {}).get(reel_segment, None)

    if fruit is None:
        print(f"Warning: Unhandled segment {reel_segment} for reel {reel_index}")
        return None

    return fruit


def endgame(fruit0: Fruit, fruit1: Fruit, fruit2: Fruit) -> int:
    """
    Determines the number of coins won based on the combination of fruits.

    Args:
        fruit0 (Fruit): Fruit from reel 0.
        fruit1 (Fruit): Fruit from reel 1.
        fruit2 (Fruit): Fruit from reel 2.

    Returns:
        int: Number of coins won.
    """
    coins = 0

    # Check for 3 cherries
    if fruit0 == Fruit.CHERRY and fruit1 == Fruit.CHERRY and fruit2 == Fruit.CHERRY:
        coins = 50
    # Check for 2 cherries
    elif fruit0 == Fruit.CHERRY and fruit1 == Fruit.CHERRY:
        coins = 40
    # Check for 3 apples
    elif fruit0 == Fruit.APPLE and fruit1 == Fruit.APPLE and fruit2 == Fruit.APPLE:
        coins = 20
    # Check for 2 apples
    elif fruit0 == Fruit.APPLE and fruit1 == Fruit.APPLE:
        coins = 10
    # Check for 3 bananas
    elif fruit0 == Fruit.BANANA and fruit1 == Fruit.BANANA and fruit2 == Fruit.BANANA:
        coins = 15
    # Check for 2 bananas
    elif fruit0 == Fruit.BANANA and fruit1 == Fruit.BANANA:
        coins = 5
    # Check for 3 lemons
    elif fruit0 == Fruit.LEMON and fruit1 == Fruit.LEMON and fruit2 == Fruit.LEMON:
        coins = 3

    return coins


def cherryAction(spin_user):
    from .. import db
    from ..utils.models import User, Transaction, TransactionType, GameType
    import uuid

    logging.debug("Received spin request for user_id: %s", spin_user.username)

    # Lock user row for update to prevent race conditions
    locked_user = db.session.query(User).with_for_update().filter_by(id=spin_user.id).first()

    if not locked_user:
        return jsonify({'message': 'User not found'}), 404

    # Check if the user has enough coins to spin
    if locked_user.coins < 1:
        logging.warning("User %s does not have enough coins to spin.", locked_user.username)
        return jsonify({'message': 'Not enough coins to spin'}), 400

    # Generate reference ID for linking bet and win transactions
    reference_id = str(uuid.uuid4())

    # Deduct a coin for spinning (BET)
    bet_amount = 1
    locked_user.coins -= bet_amount
    logging.info("User %s has spun the slot machine. Coins left: %s", locked_user.username, locked_user.coins)

    # Record BET transaction
    Transaction.create_transaction(
        user=locked_user,
        transaction_type=TransactionType.BET,
        amount=-bet_amount,
        game_type=GameType.SLOTS,
        description=f"Slot machine spin bet",
        reference_id=reference_id
    )

    # Generate stop segments and fruits
    stop_segments = spin_reels()
    logging.info("Generated stop segments for user %s: %s", locked_user.username, stop_segments)
    fruits = get_fruits(stop_segments)
    logging.info("Fruits for user %s: %s", locked_user.username, fruits)

    # Compute winnings
    winnings = calculate_winnings(fruits)
    logging.info("User %s won: %s coins", locked_user.username, winnings)

    # Add winnings to user's coins
    if winnings > 0:
        locked_user.coins += winnings
        logging.info("User %s new coin balance: %s", locked_user.username, locked_user.coins)

        # Record WIN transaction
        Transaction.create_transaction(
            user=locked_user,
            transaction_type=TransactionType.WIN,
            amount=winnings,
            game_type=GameType.SLOTS,
            description=f"Slot machine win: {[f.value for f in fruits]}",
            extra_data={
                'fruits': [f.value for f in fruits],
                'stop_segments': stop_segments,
                'payout': winnings
            },
            reference_id=reference_id
        )

    # Check and unlock achievements
    from ..utils.achievement_service import (
        check_achievements,
        check_single_bet_achievements,
        check_single_win_achievements,
        check_winning_streak
    )

    # Check bet-based achievements
    check_single_bet_achievements(locked_user, bet_amount)

    # Check win-based achievements
    if winnings > 0:
        check_single_win_achievements(locked_user, winnings)

    # Check general achievements (total spins, wins, etc.)
    check_achievements(locked_user)

    # Check winning streak
    check_winning_streak(locked_user)

    db.session.commit()

    # Real-time features (Month 5) - Broadcast updates via SocketIO
    from ..socketio_events import broadcast_big_win, broadcast_leaderboard_update

    # Broadcast big win if significant
    if winnings >= 500:
        broadcast_big_win(locked_user, winnings, 'slots')

    # Broadcast leaderboard update (all metrics, all timeframes)
    for metric in ['coins', 'net_profit', 'total_wins']:
        for timeframe in ['daily', 'weekly', 'all_time']:
            broadcast_leaderboard_update(locked_user, metric, timeframe)

    # Prepare the response data
    response_data = {
        'stopSegments': stop_segments,
        'totalCoins': locked_user.coins
    }
    return jsonify(response_data), 200

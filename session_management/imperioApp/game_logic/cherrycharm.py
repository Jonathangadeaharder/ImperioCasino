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
    logging.debug("Received spin request for user_id: %s", spin_user.username)
    # Check if the user has enough coins to spin
    if spin_user.coins < 1:
        logging.warning("User %s does not have enough coins to spin.", spin_user.username)
        return jsonify({'message': 'Not enough coins to spin'}), 400
    # Deduct a coin for spinning
    reduce_user_coins(spin_user, 1)
    logging.info("User %s has spun the slot machine. Coins left: %s", spin_user.username, spin_user.coins)
    # Generate stop segments and fruits
    stop_segments = spin_reels()
    logging.info("Generated stop segments for user %s: %s", spin_user.username, stop_segments)
    fruits = get_fruits(stop_segments)
    logging.info("Fruits for user %s: %s", spin_user.username, fruits)
    # Compute winnings
    winnings = calculate_winnings(fruits)
    logging.info("User %s won: %s coins", spin_user.username, winnings)
    # Add winnings to user's coins
    increase_user_coins(spin_user, winnings)
    logging.info("User %s new coin balance: %s", spin_user.username, spin_user.coins)
    # Prepare the response data
    response_data = {
        'stopSegments': stop_segments,
        'totalCoins': spin_user.coins
    }
    return jsonify(response_data), 200

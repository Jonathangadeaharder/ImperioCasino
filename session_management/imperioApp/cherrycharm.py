# cherrycharm.py

from enum import Enum

from enum import Enum

class Fruit(Enum):
    CHERRY = "CHERRY"
    LEMON = "LEMON"
    BANANA = "BANANA"
    APPLE = "APPLE"
    UNKNOWN = "UNKNOWN"

def segment_to_fruit(reel: int, segment: int) -> Fruit:
    mapped_segment = segment % 16
    if mapped_segment < 8:
        return Fruit.UNKNOWN

    mappings = {
        0: {
            8: Fruit.CHERRY,
            9: Fruit.LEMON,
            10: Fruit.LEMON,
            11: Fruit.BANANA,
            12: Fruit.BANANA,
            13: Fruit.LEMON,
            14: Fruit.APPLE,
            15: Fruit.LEMON
        },
        1: {
            8: Fruit.LEMON,
            9: Fruit.LEMON,
            10: Fruit.BANANA,
            11: Fruit.APPLE,
            12: Fruit.CHERRY,
            13: Fruit.LEMON,
            14: Fruit.LEMON,
            15: Fruit.APPLE
        },
        2: {
            8: Fruit.LEMON,
            9: Fruit.LEMON,
            10: Fruit.BANANA,
            11: Fruit.LEMON,
            12: Fruit.CHERRY,
            13: Fruit.APPLE,
            14: Fruit.LEMON,
            15: Fruit.APPLE
        }
    }

    return mappings.get(reel, {}).get(mapped_segment, Fruit.UNKNOWN)

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

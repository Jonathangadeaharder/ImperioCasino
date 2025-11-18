import logging
import random
from ..utils.services import increase_user_coins, reduce_user_coins

def rouletteAction(current_user, data):
    ROULETTE_NUMBERS = list(range(0, 37))

    bet_info = data.get('bet')
    if not bet_info or not isinstance(bet_info, list):
        return {"message": "Bet details are required"}, 400

    if len(bet_info) == 0:
        return {"message": "At least one bet is required"}, 400

    total_bet = 0

    # First validate all bets before deducting any coins
    for bet in bet_info:
        amt = bet.get("amt")
        if amt is None or not isinstance(amt, (int, float)) or amt <= 0:
            return {"message": "Invalid bet amount"}, 400

        # Validate odds
        odds = bet.get("odds")
        if odds is None or not isinstance(odds, (int, float)) or odds < 0:
            return {"message": "Invalid odds"}, 400

        total_bet += amt

    # Check if user has enough coins for all bets
    if current_user.coins < total_bet:
        return {"message": "Not enough coins for all bets"}, 400

    # Deduct the coins for all bets now
    for bet in bet_info:
        amt = bet.get("amt")
        reduce_user_coins(current_user, amt)

    # Perform the spin
    winning_number = random.choice(ROULETTE_NUMBERS)
    total_win = 0

    for bet in bet_info:
        numbers_str = bet.get("numbers", "")
        odds = bet.get("odds", 0)
        amt = bet.get("amt")

        # Attempt to parse numbers
        if numbers_str.strip() == "":
            # If empty string, consider it as no numbers chosen, no error.
            bet_numbers = []
        else:
            # Non-empty string that should represent numbers
            raw_numbers = [x.strip() for x in numbers_str.split(",")]
            # Validate that all entries are digits
            if any(not n.isdigit() for n in raw_numbers):
                # Invalid format like 'abc' found
                return {"message": "Invalid bet numbers"}, 400
            bet_numbers = [int(x) for x in raw_numbers]

            # Validate that all numbers are in valid range
            if any(num < 0 or num > 36 for num in bet_numbers):
                return {"message": "Bet numbers must be between 0 and 36"}, 400

        # With bet_numbers parsed, if empty and originally empty, it's valid but no win scenario
        # If originally empty: bet_numbers = []
        # This is allowed and not an error.

        # Check if this bet wins
        if winning_number in bet_numbers:
            payout = (odds * amt) + amt
            total_win += payout

    # Increase user coins if won
    if total_win > 0:
        increase_user_coins(current_user, total_win)

    return {
        "winning_number": winning_number,
        "total_bet": total_bet,
        "total_win": total_win,
        "new_coins": current_user.coins
    }, 200

import logging
import random
from ..utils.services import increase_user_coins, reduce_user_coins


def rouletteAction(current_user, data):
    ROULETTE_NUMBERS = list(range(0, 37))

    bet_info = data.get('bet')
    if not bet_info:
        return {"message": "Bet details are required"}, 400

    amt = bet_info.get("amt")
    if amt is None or amt <= 0:
        return {"message": "Invalid bet amount"}, 400

    if current_user["coins"] < amt:
        return {"message": "Not enough coins"}, 400

    # Deduct coins for the bet
    reduce_user_coins(current_user, amt)
    # Perform the spin
    winning_number = random.choice(ROULETTE_NUMBERS)
    numbers_str = bet_info.get("numbers", "")
    try:
        bet_numbers = [int(x.strip()) for x in numbers_str.split(",")]
    except ValueError:
        return {"message": "Invalid bet numbers"}, 400

    odds = bet_info.get("odds", 0)
    total_bet = amt
    total_win = 0

    # Check if the bet wins
    if winning_number in bet_numbers:
        # Player wins (odds * amt) + original amt
        total_win = (odds * amt) + amt
        increase_user_coins(current_user, total_win)

    current_user["previous_roulette_spins"].append(winning_number)

    logging.debug(
        "Roulette spin result for user %s: Winning number %s. Total Bet: %d, Total Win: %d, New coin balance: %d",
        current_user["username"], winning_number, total_bet, total_win, current_user["coins"]
    )

    return {
        "winning_number": winning_number,
        "total_bet": total_bet,
        "total_win": total_win,
        "new_coins": current_user["coins"],
        "previous_spins": current_user["previous_roulette_spins"]
    }

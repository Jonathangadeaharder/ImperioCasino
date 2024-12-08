import logging
import random
from ..utils.services import increase_user_coins, reduce_user_coins

def rouletteAction(current_user, data):
    ROULETTE_NUMBERS = list(range(0, 37))

    bet_info = data.get('bet')
    if not bet_info or not isinstance(bet_info, list):
        return {"message": "Bet details are required"}, 400

    total_bet = 0

    # First, validate and check if user has enough coins for all bets
    for bet in bet_info:
        amt = bet.get("amt")
        if amt is None or amt <= 0:
            return {"message": "Invalid bet amount"}, 400

        # Check user's coin balance for each bet
        if current_user.coins < amt:
            return {"message": "Not enough coins"}, 400

    # Deduct coins for all bets now that they are validated
    for bet in bet_info:
        amt = bet.get("amt")
        reduce_user_coins(current_user, amt)
        total_bet += amt

    # Perform the spin
    winning_number = random.choice(ROULETTE_NUMBERS)
    total_win = 0

    # Evaluate each bet
    for bet in bet_info:
        numbers_str = bet.get("numbers", "")
        odds = bet.get("odds", 0)
        amt = bet.get("amt")

        try:
            bet_numbers = [int(x.strip()) for x in numbers_str.split(",") if x.strip().isdigit()]
        except ValueError:
            return {"message": "Invalid bet numbers"}, 400

        # Check if this bet wins
        if winning_number in bet_numbers:
            # Payout = (odds * amt) + original bet
            payout = (odds * amt) + amt
            total_win += payout

    # Increase user coins if any bet won
    if total_win > 0:
        increase_user_coins(current_user, total_win)

    logging.debug(
        "Roulette spin result for user %s: Winning number %s. Total Bet: %d, Total Win: %d, New coin balance: %d",
        current_user, winning_number, total_bet, total_win, current_user.coins
    )

    return {
        "winning_number": winning_number,
        "total_bet": total_bet,
        "total_win": total_win,
        "new_coins": current_user.coins    }, 200

import logging
import random
import uuid
from ..utils.services import increase_user_coins, reduce_user_coins

def rouletteAction(current_user, data):
    from .. import db
    from ..utils.models import User, Transaction, TransactionType, GameType

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

    # Lock user row for update to prevent race conditions
    locked_user = db.session.query(User).with_for_update().filter_by(id=current_user.id).first()

    if not locked_user:
        return {"message": "User not found"}, 404

    # Check if user has enough coins for all bets
    if locked_user.coins < total_bet:
        return {"message": "Not enough coins for all bets"}, 400

    # Generate reference ID for linking all bet and win transactions in this spin
    reference_id = str(uuid.uuid4())

    # Deduct the coins for all bets now
    locked_user.coins -= total_bet

    # Record BET transaction for total bet amount
    Transaction.create_transaction(
        user=locked_user,
        transaction_type=TransactionType.BET,
        amount=-total_bet,
        game_type=GameType.ROULETTE,
        description=f"Roulette spin: {len(bet_info)} bet(s) totaling {total_bet} coins",
        extra_data={
            'num_bets': len(bet_info),
            'bets': [
                {
                    'amount': b.get('amt'),
                    'numbers': b.get('numbers', ''),
                    'odds': b.get('odds')
                } for b in bet_info
            ]
        },
        reference_id=reference_id
    )

    # Perform the spin
    winning_number = random.choice(ROULETTE_NUMBERS)
    total_win = 0
    winning_bets = []

    for i, bet in enumerate(bet_info):
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

        # Check if this bet wins
        if winning_number in bet_numbers:
            payout = (odds * amt) + amt
            total_win += payout
            winning_bets.append({
                'bet_index': i,
                'amount': amt,
                'numbers': bet_numbers,
                'odds': odds,
                'payout': payout
            })

    # Add winnings to user coins
    if total_win > 0:
        locked_user.coins += total_win

        # Record WIN transaction
        Transaction.create_transaction(
            user=locked_user,
            transaction_type=TransactionType.WIN,
            amount=total_win,
            game_type=GameType.ROULETTE,
            description=f"Roulette win: {total_win} coins on number {winning_number}",
            extra_data={
                'winning_number': winning_number,
                'total_payout': total_win,
                'winning_bets': winning_bets,
                'num_winning_bets': len(winning_bets)
            },
            reference_id=reference_id
        )

    db.session.commit()

    return {
        "winning_number": winning_number,
        "total_bet": total_bet,
        "total_win": total_win,
        "new_coins": locked_user.coins
    }, 200

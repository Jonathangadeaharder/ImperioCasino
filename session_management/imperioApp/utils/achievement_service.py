"""
Achievement service for checking and unlocking user achievements.

This module handles:
- Checking if users meet achievement criteria
- Unlocking achievements and awarding coins
- Creating notifications for achievement unlocks
"""

from datetime import datetime, timedelta
from . import db
from .models import (
    User, Achievement, UserAchievement, Transaction, Notification,
    AchievementType, TransactionType, GameType, NotificationType
)
from sqlalchemy import func
import structlog

log = structlog.get_logger()


# Achievement definitions with unlock criteria
ACHIEVEMENT_DEFINITIONS = {
    AchievementType.FIRST_SPIN: {
        'name': 'First Spin',
        'description': 'Place your first bet in any game',
        'icon': '🎰',
        'reward_coins': 10
    },
    AchievementType.FIRST_WIN: {
        'name': 'First Win',
        'description': 'Win your first game',
        'icon': '🏆',
        'reward_coins': 25
    },
    AchievementType.TOTAL_SPINS_10: {
        'name': 'Getting Started',
        'description': 'Play 10 games',
        'icon': '🎮',
        'reward_coins': 50
    },
    AchievementType.TOTAL_SPINS_100: {
        'name': 'Dedicated Player',
        'description': 'Play 100 games',
        'icon': '🎯',
        'reward_coins': 200
    },
    AchievementType.TOTAL_SPINS_1000: {
        'name': 'Casino Legend',
        'description': 'Play 1000 games',
        'icon': '👑',
        'reward_coins': 1000
    },
    AchievementType.BIG_WIN_100: {
        'name': 'Big Winner',
        'description': 'Win 100+ coins in a single game',
        'icon': '💰',
        'reward_coins': 100
    },
    AchievementType.BIG_WIN_500: {
        'name': 'Jackpot',
        'description': 'Win 500+ coins in a single game',
        'icon': '💎',
        'reward_coins': 500
    },
    AchievementType.WINNING_STREAK_3: {
        'name': 'Hot Streak',
        'description': 'Win 3 games in a row',
        'icon': '🔥',
        'reward_coins': 150
    },
    AchievementType.WINNING_STREAK_5: {
        'name': 'Unstoppable',
        'description': 'Win 5 games in a row',
        'icon': '⚡',
        'reward_coins': 300
    },
    AchievementType.NET_PROFIT_1000: {
        'name': 'Profitable Gambler',
        'description': 'Reach 1000 coins net profit',
        'icon': '📈',
        'reward_coins': 250
    },
    AchievementType.NET_PROFIT_5000: {
        'name': 'High Roller',
        'description': 'Reach 5000 coins net profit',
        'icon': '💵',
        'reward_coins': 1000
    },
    AchievementType.BLACKJACK_MASTER_10: {
        'name': 'Blackjack Master',
        'description': 'Win 10 blackjack games',
        'icon': '♠️',
        'reward_coins': 200
    },
    AchievementType.ROULETTE_MASTER_10: {
        'name': 'Roulette Master',
        'description': 'Win 10 roulette games',
        'icon': '🎡',
        'reward_coins': 200
    },
    AchievementType.SLOTS_MASTER_10: {
        'name': 'Slots Master',
        'description': 'Win 10 slots games',
        'icon': '🍒',
        'reward_coins': 200
    },
    AchievementType.LUCKY_DAY: {
        'name': 'Lucky Day',
        'description': 'Win 10 times in one day',
        'icon': '🍀',
        'reward_coins': 300
    },
    AchievementType.HIGH_ROLLER: {
        'name': 'High Roller',
        'description': 'Bet 1000+ coins in a single game',
        'icon': '🎩',
        'reward_coins': 500
    },
}


def initialize_achievements():
    """
    Initialize all achievement definitions in the database.
    Should be called once during setup or migration.
    """
    for achievement_type, definition in ACHIEVEMENT_DEFINITIONS.items():
        existing = Achievement.query.filter_by(achievement_type=achievement_type).first()
        if not existing:
            achievement = Achievement(
                achievement_type=achievement_type,
                name=definition['name'],
                description=definition['description'],
                icon=definition['icon'],
                reward_coins=definition['reward_coins']
            )
            db.session.add(achievement)
            log.info("achievement_created", type=achievement_type.value)

    db.session.commit()
    log.info("achievements_initialized")


def has_achievement(user_id, achievement_type):
    """Check if user already has an achievement."""
    achievement = Achievement.query.filter_by(achievement_type=achievement_type).first()
    if not achievement:
        return False

    return UserAchievement.query.filter_by(
        user_id=user_id,
        achievement_id=achievement.id
    ).first() is not None


def unlock_achievement(user, achievement_type):
    """
    Unlock an achievement for a user.

    Args:
        user: User object
        achievement_type: AchievementType enum

    Returns:
        UserAchievement: The unlocked achievement, or None if already unlocked
    """
    # Check if already unlocked
    if has_achievement(user.id, achievement_type):
        return None

    # Get achievement definition
    achievement = Achievement.query.filter_by(achievement_type=achievement_type).first()
    if not achievement:
        log.error("achievement_not_found", type=achievement_type.value)
        return None

    # Create user achievement
    user_achievement = UserAchievement(
        user_id=user.id,
        achievement_id=achievement.id,
        unlocked_at=datetime.utcnow(),
        seen=False
    )
    db.session.add(user_achievement)

    # Award coins
    if achievement.reward_coins > 0:
        user.coins += achievement.reward_coins
        log.info("achievement_reward_awarded",
                user_id=user.id,
                achievement=achievement_type.value,
                reward=achievement.reward_coins)

        # Record transaction for reward
        from .models import Transaction
        Transaction.create_transaction(
            user=user,
            transaction_type=TransactionType.BONUS,
            amount=achievement.reward_coins,
            game_type=GameType.NONE,
            description=f"Achievement reward: {achievement.name}",
            metadata={'achievement_type': achievement_type.value}
        )

    # Create notification
    Notification.create_notification(
        user=user,
        notification_type=NotificationType.ACHIEVEMENT_UNLOCKED,
        title=f"Achievement Unlocked: {achievement.name}",
        message=f"{achievement.description} +{achievement.reward_coins} coins!",
        icon=achievement.icon,
        metadata={'achievement_id': achievement.id, 'achievement_type': achievement_type.value}
    )

    db.session.commit()

    log.info("achievement_unlocked",
            user_id=user.id,
            achievement=achievement_type.value,
            reward=achievement.reward_coins)

    return user_achievement


def check_achievements(user):
    """
    Check all possible achievements for a user and unlock any that are met.

    Args:
        user: User object

    Returns:
        list: List of newly unlocked achievements
    """
    newly_unlocked = []

    # Get user stats
    stats = Transaction.get_user_statistics(user.id)

    # Check FIRST_SPIN
    if stats['total_bets_count'] >= 1:
        result = unlock_achievement(user, AchievementType.FIRST_SPIN)
        if result:
            newly_unlocked.append(result)

    # Check FIRST_WIN
    if stats['total_wins_count'] >= 1:
        result = unlock_achievement(user, AchievementType.FIRST_WIN)
        if result:
            newly_unlocked.append(result)

    # Check total spins milestones
    if stats['total_bets_count'] >= 10:
        result = unlock_achievement(user, AchievementType.TOTAL_SPINS_10)
        if result:
            newly_unlocked.append(result)

    if stats['total_bets_count'] >= 100:
        result = unlock_achievement(user, AchievementType.TOTAL_SPINS_100)
        if result:
            newly_unlocked.append(result)

    if stats['total_bets_count'] >= 1000:
        result = unlock_achievement(user, AchievementType.TOTAL_SPINS_1000)
        if result:
            newly_unlocked.append(result)

    # Check net profit milestones
    if stats['net_profit'] >= 1000:
        result = unlock_achievement(user, AchievementType.NET_PROFIT_1000)
        if result:
            newly_unlocked.append(result)

    if stats['net_profit'] >= 5000:
        result = unlock_achievement(user, AchievementType.NET_PROFIT_5000)
        if result:
            newly_unlocked.append(result)

    # Check game-specific master achievements
    for game_stat in stats['wins_by_game']:
        if game_stat['game'] == 'blackjack' and game_stat['count'] >= 10:
            result = unlock_achievement(user, AchievementType.BLACKJACK_MASTER_10)
            if result:
                newly_unlocked.append(result)

        if game_stat['game'] == 'roulette' and game_stat['count'] >= 10:
            result = unlock_achievement(user, AchievementType.ROULETTE_MASTER_10)
            if result:
                newly_unlocked.append(result)

        if game_stat['game'] == 'slots' and game_stat['count'] >= 10:
            result = unlock_achievement(user, AchievementType.SLOTS_MASTER_10)
            if result:
                newly_unlocked.append(result)

    # Check LUCKY_DAY (10 wins in one day)
    today = datetime.utcnow().date()
    wins_today = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type == TransactionType.WIN,
        func.date(Transaction.created_at) == today
    ).count()

    if wins_today >= 10:
        result = unlock_achievement(user, AchievementType.LUCKY_DAY)
        if result:
            newly_unlocked.append(result)

    return newly_unlocked


def check_single_win_achievements(user, win_amount):
    """
    Check achievements related to a single win amount.

    Args:
        user: User object
        win_amount: Amount won in the game

    Returns:
        list: List of newly unlocked achievements
    """
    newly_unlocked = []

    # Check big win achievements
    if win_amount >= 100:
        result = unlock_achievement(user, AchievementType.BIG_WIN_100)
        if result:
            newly_unlocked.append(result)

    if win_amount >= 500:
        result = unlock_achievement(user, AchievementType.BIG_WIN_500)
        if result:
            newly_unlocked.append(result)

    return newly_unlocked


def check_single_bet_achievements(user, bet_amount):
    """
    Check achievements related to a single bet amount.

    Args:
        user: User object
        bet_amount: Amount bet in the game

    Returns:
        list: List of newly unlocked achievements
    """
    newly_unlocked = []

    # Check high roller achievement
    if bet_amount >= 1000:
        result = unlock_achievement(user, AchievementType.HIGH_ROLLER)
        if result:
            newly_unlocked.append(result)

    return newly_unlocked


def check_winning_streak(user):
    """
    Check for winning streak achievements.

    Args:
        user: User object

    Returns:
        list: List of newly unlocked achievements
    """
    newly_unlocked = []

    # Get last 10 transactions (bets and wins)
    recent_transactions = Transaction.query.filter(
        Transaction.user_id == user.id,
        Transaction.transaction_type.in_([TransactionType.BET, TransactionType.WIN])
    ).order_by(Transaction.created_at.desc()).limit(20).all()

    # Group by reference_id to get game results
    games = {}
    for trans in reversed(recent_transactions):  # Process in chronological order
        if trans.reference_id:
            if trans.reference_id not in games:
                games[trans.reference_id] = {'bet': None, 'win': None}

            if trans.transaction_type == TransactionType.BET:
                games[trans.reference_id]['bet'] = trans
            elif trans.transaction_type == TransactionType.WIN:
                games[trans.reference_id]['win'] = trans

    # Calculate streak
    current_streak = 0
    for ref_id in reversed(list(games.keys())):  # Most recent first
        game = games[ref_id]
        if game['win']:  # Won this game
            current_streak += 1
        else:  # Lost this game
            break

    # Check streak achievements
    if current_streak >= 3:
        result = unlock_achievement(user, AchievementType.WINNING_STREAK_3)
        if result:
            newly_unlocked.append(result)

    if current_streak >= 5:
        result = unlock_achievement(user, AchievementType.WINNING_STREAK_5)
        if result:
            newly_unlocked.append(result)

    return newly_unlocked

from sqlalchemy import PickleType
from .. import db, login_manager  # Relative imports
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .constants import DEFAULT_COINS  # Import DEFAULT_COINS
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
import enum

class BlackjackGameState(db.Model):
    __tablename__ = 'blackjack_game_state'
    __table_args__ = (
        db.Index('idx_user_game_state', 'user_id', 'game_over'),
    )
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    deck = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    dealer_hand = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    player_hand = db.Column(MutableList.as_mutable(PickleType), nullable=False)
    player_second_hand = db.Column(MutableList.as_mutable(PickleType), nullable=True)
    player_coins = db.Column(db.Integer, nullable=False)
    current_wager = db.Column(db.Integer, nullable=False)
    game_over = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(255), default='')
    player_stood = db.Column(db.Boolean, default=False)
    double_down = db.Column(db.Boolean, default=False)
    split = db.Column(db.Boolean, default=False)
    current_hand = db.Column(db.String(10), default='first')
    dealer_value = db.Column(db.Integer, nullable=True)  # **New Column Added**

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'deck': self.deck,
            'dealer_hand': self.dealer_hand,
            'player_hand': self.player_hand,
            'player_coins': self.player_coins,
            'current_wager': self.current_wager,
            'game_over': self.game_over,
            'message': self.message,
            'player_stood': self.player_stood,
            'double_down': self.double_down,
            'split': self.split,
            'player_second_hand': self.player_second_hand,
            'current_hand': self.current_hand,
            'dealer_value': self.dealer_value  # Ensure this is included
        }


class TransactionType(enum.Enum):
    """Enumeration for transaction types."""
    BET = 'bet'
    WIN = 'win'
    LOSS = 'loss'
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    BONUS = 'bonus'
    REFUND = 'refund'
    ADJUSTMENT = 'adjustment'


class GameType(enum.Enum):
    """Enumeration for game types."""
    SLOTS = 'slots'
    BLACKJACK = 'blackjack'
    ROULETTE = 'roulette'
    NONE = 'none'


class Transaction(db.Model):
    """
    Transaction model for complete audit trail of all coin movements.

    This model tracks every financial operation in the system including:
    - Bets placed across all games
    - Winnings and losses
    - Deposits and withdrawals
    - Bonuses and refunds
    - Administrative adjustments

    Each transaction records the balance before and after, ensuring
    complete accountability and allowing for detailed financial reporting.
    """
    __tablename__ = 'transactions'
    __table_args__ = (
        db.Index('idx_user_transactions', 'user_id', 'created_at'),
        db.Index('idx_transaction_type', 'transaction_type'),
        db.Index('idx_game_type', 'game_type'),
        db.Index('idx_created_at', 'created_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Transaction details
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False, index=True)
    game_type = db.Column(db.Enum(GameType), nullable=True, index=True)
    amount = db.Column(db.Integer, nullable=False)  # Positive for credits, negative for debits

    # Balance tracking
    balance_before = db.Column(db.Integer, nullable=False)
    balance_after = db.Column(db.Integer, nullable=False)

    # Metadata
    description = db.Column(db.String(255), nullable=True)
    extra_data = db.Column(db.JSON, nullable=True)  # Additional game-specific data
    reference_id = db.Column(db.String(64), nullable=True, index=True)  # For linking related transactions

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship
    user = db.relationship('User', backref=db.backref('transactions', lazy='dynamic', order_by='Transaction.created_at.desc()'))

    def __repr__(self):
        return f'<Transaction {self.id}: {self.transaction_type.value} {self.amount} coins for user {self.user_id}>'

    def to_dict(self):
        """Convert transaction to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type.value,
            'game_type': self.game_type.value if self.game_type else None,
            'amount': self.amount,
            'balance_before': self.balance_before,
            'balance_after': self.balance_after,
            'description': self.description,
            'extra_data': self.extra_data,
            'reference_id': self.reference_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def create_transaction(user, transaction_type, amount, game_type=None,
                          description=None, extra_data=None, reference_id=None):
        """
        Create a new transaction record.

        Args:
            user: User object
            transaction_type: TransactionType enum
            amount: Transaction amount (positive for credits, negative for debits)
            game_type: GameType enum (optional)
            description: Human-readable description (optional)
            extra_data: Additional JSON data (optional)
            reference_id: Reference to link related transactions (optional)

        Returns:
            Transaction: Created transaction object
        """
        transaction = Transaction(
            user_id=user.id,
            transaction_type=transaction_type,
            game_type=game_type,
            amount=amount,
            balance_before=user.coins,
            balance_after=user.coins + amount,
            description=description,
            extra_data=extra_data,
            reference_id=reference_id
        )
        db.session.add(transaction)
        return transaction

    @staticmethod
    def get_user_transactions(user_id, limit=50, offset=0, transaction_type=None, game_type=None):
        """
        Get transactions for a specific user with optional filtering.

        Args:
            user_id: User ID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Filter by transaction type (optional)
            game_type: Filter by game type (optional)

        Returns:
            list: List of Transaction objects
        """
        query = Transaction.query.filter_by(user_id=user_id)

        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        if game_type:
            query = query.filter_by(game_type=game_type)

        return query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def get_user_statistics(user_id):
        """
        Get comprehensive statistics for a user's transactions.

        Args:
            user_id: User ID

        Returns:
            dict: Statistics including total bets, wins, losses, etc.
        """
        from sqlalchemy import func

        # Total bets by game
        bets_by_game = db.session.query(
            Transaction.game_type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.BET
        ).group_by(Transaction.game_type).all()

        # Total wins by game
        wins_by_game = db.session.query(
            Transaction.game_type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.WIN
        ).group_by(Transaction.game_type).all()

        # Overall statistics
        total_bets = db.session.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.BET
        ).first()

        total_wins = db.session.query(
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.WIN
        ).first()

        return {
            'bets_by_game': [
                {'game': g.value if g else 'none', 'count': c, 'total': abs(t or 0)}
                for g, c, t in bets_by_game
            ],
            'wins_by_game': [
                {'game': g.value if g else 'none', 'count': c, 'total': t or 0}
                for g, c, t in wins_by_game
            ],
            'total_bets_count': total_bets[0] or 0,
            'total_bets_amount': abs(total_bets[1] or 0),
            'total_wins_count': total_wins[0] or 0,
            'total_wins_amount': total_wins[1] or 0,
            'net_profit': (total_wins[1] or 0) + (total_bets[1] or 0)  # Bets are negative
        }


class AchievementType(enum.Enum):
    """Enumeration for achievement types."""
    FIRST_SPIN = 'first_spin'
    FIRST_WIN = 'first_win'
    TOTAL_SPINS_10 = 'total_spins_10'
    TOTAL_SPINS_100 = 'total_spins_100'
    TOTAL_SPINS_1000 = 'total_spins_1000'
    BIG_WIN_100 = 'big_win_100'
    BIG_WIN_500 = 'big_win_500'
    WINNING_STREAK_3 = 'winning_streak_3'
    WINNING_STREAK_5 = 'winning_streak_5'
    NET_PROFIT_1000 = 'net_profit_1000'
    NET_PROFIT_5000 = 'net_profit_5000'
    BLACKJACK_MASTER_10 = 'blackjack_master_10'
    ROULETTE_MASTER_10 = 'roulette_master_10'
    SLOTS_MASTER_10 = 'slots_master_10'
    LUCKY_DAY = 'lucky_day'  # Won 10 times in a day
    HIGH_ROLLER = 'high_roller'  # Bet 1000+ coins in single game


class Achievement(db.Model):
    """
    Achievement model for tracking player milestones and rewards.

    Achievements are unlocked based on player actions and statistics:
    - Game-specific achievements (slots/blackjack/roulette mastery)
    - Milestone achievements (total spins, wins, profits)
    - Special achievements (streaks, lucky days, etc.)
    """
    __tablename__ = 'achievements'
    __table_args__ = (
        db.Index('idx_achievement_type', 'achievement_type'),
        db.UniqueConstraint('achievement_type', name='unique_achievement_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    achievement_type = db.Column(db.Enum(AchievementType), nullable=False, unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(50), nullable=True)  # Emoji or icon identifier
    reward_coins = db.Column(db.Integer, default=0)  # Coin reward for unlocking

    def __repr__(self):
        return f'<Achievement {self.achievement_type.value}: {self.name}>'

    def to_dict(self):
        """Convert achievement to dictionary."""
        return {
            'id': self.id,
            'type': self.achievement_type.value,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'reward_coins': self.reward_coins
        }


class UserAchievement(db.Model):
    """
    Tracks which achievements users have unlocked.
    """
    __tablename__ = 'user_achievements'
    __table_args__ = (
        db.Index('idx_user_achievement', 'user_id', 'unlocked_at'),
        db.UniqueConstraint('user_id', 'achievement_id', name='unique_user_achievement'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    unlocked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    seen = db.Column(db.Boolean, default=False)  # Has user seen the achievement notification

    # Relationships
    user = db.relationship('User', backref=db.backref('user_achievements', lazy='dynamic'))
    achievement = db.relationship('Achievement', backref='unlocked_by')

    def __repr__(self):
        return f'<UserAchievement user={self.user_id} achievement={self.achievement_id}>'

    def to_dict(self):
        """Convert user achievement to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement': self.achievement.to_dict() if self.achievement else None,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
            'seen': self.seen
        }


class NotificationType(enum.Enum):
    """Enumeration for notification types."""
    ACHIEVEMENT_UNLOCKED = 'achievement_unlocked'
    BIG_WIN = 'big_win'
    LEVEL_UP = 'level_up'
    DAILY_BONUS = 'daily_bonus'
    SYSTEM_MESSAGE = 'system_message'
    PROMO = 'promo'


class Notification(db.Model):
    """
    Notification model for user notifications and alerts.

    Supports various notification types:
    - Achievement unlocks
    - Big wins
    - Daily bonuses
    - System messages
    - Promotional offers
    """
    __tablename__ = 'notifications'
    __table_args__ = (
        db.Index('idx_user_notifications', 'user_id', 'created_at'),
        db.Index('idx_unread_notifications', 'user_id', 'read'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notification_type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(50), nullable=True)  # Emoji or icon identifier
    extra_data = db.Column(db.JSON, nullable=True)  # Additional data (achievement_id, amount, etc.)
    read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationship
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', order_by='Notification.created_at.desc()'))

    def __repr__(self):
        return f'<Notification {self.id}: {self.notification_type.value} for user {self.user_id}>'

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.notification_type.value,
            'title': self.title,
            'message': self.message,
            'icon': self.icon,
            'extra_data': self.extra_data,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def create_notification(user, notification_type, title, message, icon=None, extra_data=None):
        """
        Create a new notification for a user and send real-time update via SocketIO.

        Args:
            user: User object
            notification_type: NotificationType enum
            title: Notification title
            message: Notification message
            icon: Optional icon/emoji
            extra_data: Optional additional data

        Returns:
            Notification: Created notification object
        """
        notification = Notification(
            user_id=user.id,
            notification_type=notification_type,
            title=title,
            message=message,
            icon=icon,
            extra_data=extra_data
        )
        db.session.add(notification)
        db.session.flush()  # Get notification ID

        # Send real-time notification via SocketIO (Month 5)
        try:
            from ..socketio_events import send_notification_to_user
            send_notification_to_user(user.id, notification.to_dict())
        except Exception as e:
            # Don't fail notification creation if SocketIO fails
            import logging
            logging.warning(f"Failed to send real-time notification: {e}")

        return notification


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('idx_username', 'username'),
        db.Index('idx_email', 'email'),
    )
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=True)
    coins = db.Column(db.Integer, nullable=False)  # Remove default here

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.coins is None:
            self.coins = DEFAULT_COINS  # Use DEFAULT_COINS here

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

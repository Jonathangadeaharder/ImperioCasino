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
    metadata = db.Column(db.JSON, nullable=True)  # Additional game-specific data
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
            'metadata': self.metadata,
            'reference_id': self.reference_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def create_transaction(user, transaction_type, amount, game_type=None,
                          description=None, metadata=None, reference_id=None):
        """
        Create a new transaction record.

        Args:
            user: User object
            transaction_type: TransactionType enum
            amount: Transaction amount (positive for credits, negative for debits)
            game_type: GameType enum (optional)
            description: Human-readable description (optional)
            metadata: Additional JSON data (optional)
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
            metadata=metadata,
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

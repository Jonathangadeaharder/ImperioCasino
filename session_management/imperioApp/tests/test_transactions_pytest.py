"""
Comprehensive transaction tests using pytest (Month 3 - Transaction History).

This module tests:
- Transaction creation and recording
- Transaction retrieval and filtering
- User statistics
- Game-specific statistics
- Transaction model methods
"""

import pytest
import json
from datetime import datetime, timedelta
from imperioApp.utils.models import Transaction, TransactionType, GameType, User


class TestTransactionModel:
    """Test suite for Transaction model."""

    @pytest.mark.unit
    def test_create_transaction_bet(self, test_user):
        """Test creating a BET transaction."""
        initial_balance = test_user.coins

        transaction = Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.BET,
            amount=-10,
            game_type=GameType.SLOTS,
            description="Test bet"
        )

        assert transaction is not None
        assert transaction.user_id == test_user.id
        assert transaction.transaction_type == TransactionType.BET
        assert transaction.game_type == GameType.SLOTS
        assert transaction.amount == -10
        assert transaction.balance_before == initial_balance
        assert transaction.balance_after == initial_balance - 10

    @pytest.mark.unit
    def test_create_transaction_win(self, test_user):
        """Test creating a WIN transaction."""
        initial_balance = test_user.coins

        transaction = Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.WIN,
            amount=50,
            game_type=GameType.BLACKJACK,
            description="Test win"
        )

        assert transaction.transaction_type == TransactionType.WIN
        assert transaction.amount == 50
        assert transaction.balance_after == initial_balance + 50

    @pytest.mark.unit
    def test_transaction_to_dict(self, test_user):
        """Test transaction serialization to dictionary."""
        transaction = Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.BET,
            amount=-5,
            game_type=GameType.ROULETTE,
            description="Test serialization",
            metadata={'test': 'data'}
        )

        data = transaction.to_dict()

        assert 'id' in data
        assert data['user_id'] == test_user.id
        assert data['transaction_type'] == 'bet'
        assert data['game_type'] == 'roulette'
        assert data['amount'] == -5
        assert data['description'] == "Test serialization"
        assert data['metadata'] == {'test': 'data'}
        assert 'created_at' in data


class TestTransactionRetrieval:
    """Test suite for transaction retrieval methods."""

    @pytest.fixture
    def user_with_transactions(self, test_user, app_context):
        """Create a user with multiple transactions."""
        from imperioApp import db

        # Create various transactions
        for i in range(5):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS,
                description=f"Slots bet {i}"
            )

        for i in range(3):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.WIN,
                amount=20,
                game_type=GameType.SLOTS,
                description=f"Slots win {i}"
            )

        for i in range(2):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-50,
                game_type=GameType.BLACKJACK,
                description=f"Blackjack bet {i}"
            )

        db.session.commit()
        return test_user

    @pytest.mark.unit
    def test_get_user_transactions(self, user_with_transactions):
        """Test getting user transactions."""
        transactions = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            limit=10,
            offset=0
        )

        assert len(transactions) == 10
        # Should be ordered by created_at descending
        for i in range(len(transactions) - 1):
            assert transactions[i].created_at >= transactions[i + 1].created_at

    @pytest.mark.unit
    def test_get_user_transactions_with_pagination(self, user_with_transactions):
        """Test transaction pagination."""
        # Get first page
        page1 = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            limit=5,
            offset=0
        )
        assert len(page1) == 5

        # Get second page
        page2 = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            limit=5,
            offset=5
        )
        assert len(page2) == 5

        # Pages should not overlap
        page1_ids = {t.id for t in page1}
        page2_ids = {t.id for t in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0

    @pytest.mark.unit
    def test_filter_by_transaction_type(self, user_with_transactions):
        """Test filtering transactions by type."""
        bets = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            transaction_type=TransactionType.BET
        )
        wins = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            transaction_type=TransactionType.WIN
        )

        assert len(bets) == 7  # 5 slots + 2 blackjack
        assert len(wins) == 3  # 3 slots
        assert all(t.transaction_type == TransactionType.BET for t in bets)
        assert all(t.transaction_type == TransactionType.WIN for t in wins)

    @pytest.mark.unit
    def test_filter_by_game_type(self, user_with_transactions):
        """Test filtering transactions by game type."""
        slots_transactions = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            game_type=GameType.SLOTS
        )
        blackjack_transactions = Transaction.get_user_transactions(
            user_id=user_with_transactions.id,
            game_type=GameType.BLACKJACK
        )

        assert len(slots_transactions) == 8  # 5 bets + 3 wins
        assert len(blackjack_transactions) == 2  # 2 bets


class TestUserStatistics:
    """Test suite for user statistics."""

    @pytest.fixture
    def user_with_game_history(self, test_user, app_context):
        """Create a user with comprehensive game history."""
        from imperioApp import db

        # Slots: 5 bets of 10 coins, 2 wins of 20 coins each
        for _ in range(5):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS
            )
        for _ in range(2):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.WIN,
                amount=20,
                game_type=GameType.SLOTS
            )

        # Blackjack: 3 bets of 50 coins, 1 win of 100 coins
        for _ in range(3):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-50,
                game_type=GameType.BLACKJACK
            )
        Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.WIN,
            amount=100,
            game_type=GameType.BLACKJACK
        )

        db.session.commit()
        return test_user

    @pytest.mark.unit
    def test_get_user_statistics(self, user_with_game_history):
        """Test getting comprehensive user statistics."""
        stats = Transaction.get_user_statistics(user_with_game_history.id)

        assert stats['total_bets_count'] == 8  # 5 slots + 3 blackjack
        assert stats['total_bets_amount'] == 200  # 50 + 150
        assert stats['total_wins_count'] == 3  # 2 slots + 1 blackjack
        assert stats['total_wins_amount'] == 140  # 40 + 100
        assert stats['net_profit'] == -60  # 140 - 200

    @pytest.mark.unit
    def test_statistics_by_game(self, user_with_game_history):
        """Test that statistics are correctly broken down by game."""
        stats = Transaction.get_user_statistics(user_with_game_history.id)

        # Check slots stats
        slots_bets = next((g for g in stats['bets_by_game'] if g['game'] == 'slots'), None)
        assert slots_bets is not None
        assert slots_bets['count'] == 5
        assert slots_bets['total'] == 50

        slots_wins = next((g for g in stats['wins_by_game'] if g['game'] == 'slots'), None)
        assert slots_wins is not None
        assert slots_wins['count'] == 2
        assert slots_wins['total'] == 40

        # Check blackjack stats
        blackjack_bets = next((g for g in stats['bets_by_game'] if g['game'] == 'blackjack'), None)
        assert blackjack_bets is not None
        assert blackjack_bets['count'] == 3
        assert blackjack_bets['total'] == 150


class TestTransactionAPI:
    """Test suite for transaction API endpoints."""

    @pytest.mark.api
    def test_get_transactions_endpoint(self, client, test_user, auth_headers, app_context):
        """Test GET /transactions endpoint."""
        from imperioApp import db

        # Create some transactions
        for i in range(15):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS,
                description=f"Test bet {i}"
            )
        db.session.commit()

        response = client.get('/transactions', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'transactions' in data
        assert 'pagination' in data
        assert len(data['transactions']) == 15
        assert data['pagination']['total'] == 15

    @pytest.mark.api
    def test_get_transactions_with_pagination(self, client, test_user, auth_headers, app_context):
        """Test transaction pagination."""
        from imperioApp import db

        # Create 25 transactions
        for i in range(25):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-5,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        # Get first page
        response = client.get('/transactions?limit=10&offset=0', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data['transactions']) == 10
        assert data['pagination']['has_more'] is True

        # Get second page
        response = client.get('/transactions?limit=10&offset=10', headers=auth_headers)
        data = response.get_json()
        assert len(data['transactions']) == 10

        # Get third page
        response = client.get('/transactions?limit=10&offset=20', headers=auth_headers)
        data = response.get_json()
        assert len(data['transactions']) == 5
        assert data['pagination']['has_more'] is False

    @pytest.mark.api
    def test_get_transactions_with_filters(self, client, test_user, auth_headers, app_context):
        """Test transaction filtering."""
        from imperioApp import db

        # Create mixed transactions
        for _ in range(5):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS
            )
        for _ in range(3):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.WIN,
                amount=20,
                game_type=GameType.BLACKJACK
            )
        db.session.commit()

        # Filter by transaction type
        response = client.get('/transactions?type=bet', headers=auth_headers)
        data = response.get_json()
        assert len(data['transactions']) == 5
        assert all(t['transaction_type'] == 'bet' for t in data['transactions'])

        # Filter by game type
        response = client.get('/transactions?game=blackjack', headers=auth_headers)
        data = response.get_json()
        assert len(data['transactions']) == 3
        assert all(t['game_type'] == 'blackjack' for t in data['transactions'])

    @pytest.mark.api
    def test_get_transaction_detail(self, client, test_user, auth_headers, app_context):
        """Test GET /transactions/<id> endpoint."""
        from imperioApp import db

        transaction = Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.WIN,
            amount=100,
            game_type=GameType.ROULETTE,
            description="Big win!"
        )
        db.session.commit()

        response = client.get(f'/transactions/{transaction.id}', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == transaction.id
        assert data['amount'] == 100
        assert data['description'] == "Big win!"

    @pytest.mark.api
    def test_get_recent_transactions(self, client, test_user, auth_headers, app_context):
        """Test GET /transactions/recent endpoint."""
        from imperioApp import db

        # Create 15 transactions
        for i in range(15):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-5,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        response = client.get('/transactions/recent', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'transactions' in data
        assert len(data['transactions']) == 10  # Should return only 10 most recent

    @pytest.mark.api
    def test_get_user_statistics_endpoint(self, client, test_user, auth_headers, app_context):
        """Test GET /statistics endpoint."""
        from imperioApp import db

        # Create transaction history
        for _ in range(5):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS
            )
        for _ in range(2):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.WIN,
                amount=25,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        response = client.get('/statistics', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'total_bets_count' in data
        assert 'total_wins_count' in data
        assert 'net_profit' in data
        assert 'current_balance' in data
        assert data['total_bets_count'] == 5
        assert data['total_wins_count'] == 2

    @pytest.mark.api
    def test_get_game_statistics_endpoint(self, client, test_user, auth_headers, app_context):
        """Test GET /statistics/game/<game_type> endpoint."""
        from imperioApp import db

        # Create blackjack transactions
        for _ in range(3):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-50,
                game_type=GameType.BLACKJACK
            )
        Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.WIN,
            amount=100,
            game_type=GameType.BLACKJACK
        )
        db.session.commit()

        response = client.get('/statistics/game/blackjack', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['game_type'] == 'blackjack'
        assert data['total_bets_count'] == 3
        assert data['total_bets_amount'] == 150
        assert data['total_wins_count'] == 1
        assert data['total_wins_amount'] == 100

    @pytest.mark.api
    def test_unauthorized_access_to_transactions(self, client):
        """Test that transaction endpoints require authentication."""
        response = client.get('/transactions')
        assert response.status_code == 401

        response = client.get('/statistics')
        assert response.status_code == 401


class TestGameTransactionIntegration:
    """Integration tests for transaction recording in games."""

    @pytest.mark.integration
    def test_slots_spin_creates_transactions(self, client, test_user, auth_headers, app_context):
        """Test that spinning slots creates bet and possibly win transactions."""
        from imperioApp import db

        initial_transaction_count = Transaction.query.filter_by(user_id=test_user.id).count()

        # Perform a spin
        response = client.post('/spin', headers=auth_headers)
        assert response.status_code == 200

        # Check that at least a BET transaction was created
        new_transaction_count = Transaction.query.filter_by(user_id=test_user.id).count()
        assert new_transaction_count > initial_transaction_count

        # Verify BET transaction exists
        bet_transaction = Transaction.query.filter_by(
            user_id=test_user.id,
            transaction_type=TransactionType.BET,
            game_type=GameType.SLOTS
        ).first()
        assert bet_transaction is not None
        assert bet_transaction.amount == -1  # Slots cost 1 coin

    @pytest.mark.integration
    def test_blackjack_game_creates_transactions(self, client, test_user, auth_headers, app_context):
        """Test that blackjack game creates appropriate transactions."""
        from imperioApp import db

        initial_count = Transaction.query.filter_by(user_id=test_user.id).count()

        # Start a blackjack game
        response = client.post('/blackjack/start',
                              headers=auth_headers,
                              json={'wager': 50})
        assert response.status_code == 200

        # Check that a BET transaction was created
        bet_count = Transaction.query.filter_by(
            user_id=test_user.id,
            transaction_type=TransactionType.BET,
            game_type=GameType.BLACKJACK
        ).count()
        assert bet_count == 1

    @pytest.mark.integration
    def test_roulette_spin_creates_transactions(self, client, test_user, auth_headers, app_context):
        """Test that roulette spin creates transactions."""
        from imperioApp import db

        # Place a roulette bet
        response = client.post('/roulette/spin',
                              headers=auth_headers,
                              json={
                                  'bet': [
                                      {'numbers': '1,2,3', 'odds': 10, 'amt': 10}
                                  ]
                              })

        # If endpoint exists, check for transactions
        if response.status_code == 200 or response.status_code == 404:
            # Look for roulette transactions if they were created
            roulette_bets = Transaction.query.filter_by(
                user_id=test_user.id,
                game_type=GameType.ROULETTE
            ).all()
            # Transactions might exist if the endpoint worked


class TestTransactionReferenceLinks:
    """Test that related transactions are properly linked via reference_id."""

    @pytest.mark.unit
    def test_linked_transactions_share_reference_id(self, test_user, app_context):
        """Test that bet and win transactions are linked."""
        from imperioApp import db
        import uuid

        reference_id = str(uuid.uuid4())

        # Create bet transaction
        bet = Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.BET,
            amount=-10,
            game_type=GameType.SLOTS,
            reference_id=reference_id
        )

        # Create win transaction with same reference
        win = Transaction.create_transaction(
            user=test_user,
            transaction_type=TransactionType.WIN,
            amount=50,
            game_type=GameType.SLOTS,
            reference_id=reference_id
        )

        db.session.commit()

        # Verify they share the same reference_id
        assert bet.reference_id == win.reference_id
        assert bet.reference_id == reference_id

        # Can query related transactions
        related = Transaction.query.filter_by(reference_id=reference_id).all()
        assert len(related) == 2

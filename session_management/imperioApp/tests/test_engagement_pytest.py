"""
Comprehensive engagement tests using pytest (Month 4 - User Engagement).

This module tests:
- Achievement model and unlocking logic
- User achievement tracking
- Notification creation and retrieval
- Leaderboard calculations
- User profile statistics
- Winning streak detection
- Game integration with achievements
"""

import pytest
import json
from datetime import datetime, timedelta
from imperioApp.utils.models import (
    User, Achievement, UserAchievement, Notification, Transaction,
    AchievementType, NotificationType, TransactionType, GameType
)
from imperioApp.utils.achievement_service import (
    initialize_achievements, unlock_achievement, has_achievement,
    check_achievements, check_single_bet_achievements,
    check_single_win_achievements, check_winning_streak
)


class TestAchievementModel:
    """Test suite for Achievement model."""

    @pytest.mark.unit
    def test_achievement_creation(self, app_context):
        """Test creating an achievement."""
        from imperioApp import db

        achievement = Achievement(
            achievement_type=AchievementType.FIRST_SPIN,
            name='First Spin',
            description='Place your first bet',
            icon='🎰',
            reward_coins=10
        )
        db.session.add(achievement)
        db.session.commit()

        assert achievement.id is not None
        assert achievement.achievement_type == AchievementType.FIRST_SPIN
        assert achievement.reward_coins == 10

    @pytest.mark.unit
    def test_achievement_to_dict(self, app_context):
        """Test achievement serialization."""
        from imperioApp import db

        achievement = Achievement(
            achievement_type=AchievementType.FIRST_WIN,
            name='First Win',
            description='Win your first game',
            icon='🏆',
            reward_coins=25
        )
        db.session.add(achievement)
        db.session.commit()

        data = achievement.to_dict()

        assert 'id' in data
        assert data['achievement_type'] == 'first_win'
        assert data['name'] == 'First Win'
        assert data['icon'] == '🏆'
        assert data['reward_coins'] == 25

    @pytest.mark.unit
    def test_initialize_achievements(self, app_context):
        """Test initializing all pre-defined achievements."""
        from imperioApp import db

        # Clear existing achievements
        Achievement.query.delete()
        db.session.commit()

        # Initialize achievements
        initialize_achievements()

        # Check that 16 achievements were created
        count = Achievement.query.count()
        assert count == 16

        # Verify specific achievements exist
        first_spin = Achievement.query.filter_by(
            achievement_type=AchievementType.FIRST_SPIN
        ).first()
        assert first_spin is not None
        assert first_spin.name == 'First Spin'
        assert first_spin.reward_coins == 10

        high_roller = Achievement.query.filter_by(
            achievement_type=AchievementType.HIGH_ROLLER
        ).first()
        assert high_roller is not None
        assert high_roller.reward_coins == 500


class TestUserAchievement:
    """Test suite for UserAchievement model."""

    @pytest.fixture
    def initialized_achievements(self, app_context):
        """Fixture to ensure achievements are initialized."""
        from imperioApp import db
        Achievement.query.delete()
        db.session.commit()
        initialize_achievements()
        return Achievement.query.all()

    @pytest.mark.unit
    def test_unlock_achievement(self, test_user, initialized_achievements, app_context):
        """Test unlocking an achievement for a user."""
        from imperioApp import db

        initial_coins = test_user.coins

        # Unlock achievement
        user_achievement = unlock_achievement(test_user, AchievementType.FIRST_SPIN)

        assert user_achievement is not None
        assert user_achievement.user_id == test_user.id
        assert user_achievement.seen is False

        # Check that coins were awarded
        db.session.refresh(test_user)
        assert test_user.coins == initial_coins + 10  # FIRST_SPIN gives 10 coins

        # Check that transaction was created
        bonus_transaction = Transaction.query.filter_by(
            user_id=test_user.id,
            transaction_type=TransactionType.BONUS
        ).first()
        assert bonus_transaction is not None
        assert bonus_transaction.amount == 10

    @pytest.mark.unit
    def test_duplicate_achievement_unlock(self, test_user, initialized_achievements, app_context):
        """Test that achievements cannot be unlocked twice."""
        # Unlock once
        first_unlock = unlock_achievement(test_user, AchievementType.FIRST_WIN)
        assert first_unlock is not None

        # Try to unlock again
        second_unlock = unlock_achievement(test_user, AchievementType.FIRST_WIN)
        assert second_unlock is None

    @pytest.mark.unit
    def test_has_achievement(self, test_user, initialized_achievements, app_context):
        """Test checking if user has achievement."""
        # Initially should not have it
        assert has_achievement(test_user.id, AchievementType.FIRST_SPIN) is False

        # Unlock achievement
        unlock_achievement(test_user, AchievementType.FIRST_SPIN)

        # Now should have it
        assert has_achievement(test_user.id, AchievementType.FIRST_SPIN) is True

    @pytest.mark.unit
    def test_user_achievement_to_dict(self, test_user, initialized_achievements, app_context):
        """Test user achievement serialization."""
        user_achievement = unlock_achievement(test_user, AchievementType.BIG_WIN_100)

        data = user_achievement.to_dict()

        assert 'id' in data
        assert 'achievement' in data
        assert data['achievement']['achievement_type'] == 'big_win_100'
        assert 'unlocked_at' in data
        assert data['seen'] is False


class TestNotificationModel:
    """Test suite for Notification model."""

    @pytest.mark.unit
    def test_create_notification(self, test_user, app_context):
        """Test creating a notification."""
        from imperioApp import db

        notification = Notification.create_notification(
            user=test_user,
            notification_type=NotificationType.SYSTEM,
            title="Test Notification",
            message="This is a test message",
            icon="📢"
        )

        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.notification_type == NotificationType.SYSTEM
        assert notification.title == "Test Notification"
        assert notification.read is False

    @pytest.mark.unit
    def test_notification_to_dict(self, test_user, app_context):
        """Test notification serialization."""
        notification = Notification.create_notification(
            user=test_user,
            notification_type=NotificationType.ACHIEVEMENT_UNLOCKED,
            title="Achievement Unlocked!",
            message="You unlocked First Spin",
            icon="🏆",
            extra_data={'achievement_type': 'first_spin'}
        )

        data = notification.to_dict()

        assert 'id' in data
        assert data['notification_type'] == 'achievement_unlocked'
        assert data['title'] == "Achievement Unlocked!"
        assert data['read'] is False
        assert data['extra_data']['achievement_type'] == 'first_spin'
        assert 'created_at' in data

    @pytest.mark.unit
    def test_notification_created_on_achievement_unlock(self, test_user, app_context):
        """Test that unlocking achievement creates notification."""
        from imperioApp import db

        # Initialize achievements
        Achievement.query.delete()
        db.session.commit()
        initialize_achievements()

        initial_notif_count = Notification.query.filter_by(user_id=test_user.id).count()

        # Unlock achievement
        unlock_achievement(test_user, AchievementType.FIRST_SPIN)

        # Check notification was created
        new_notif_count = Notification.query.filter_by(user_id=test_user.id).count()
        assert new_notif_count == initial_notif_count + 1

        # Verify notification details
        notification = Notification.query.filter_by(
            user_id=test_user.id,
            notification_type=NotificationType.ACHIEVEMENT_UNLOCKED
        ).first()
        assert notification is not None
        assert "Achievement Unlocked" in notification.title


class TestAchievementUnlocking:
    """Test suite for achievement unlocking logic."""

    @pytest.fixture
    def user_with_achievements_setup(self, test_user, app_context):
        """Setup user with initialized achievements."""
        from imperioApp import db
        Achievement.query.delete()
        db.session.commit()
        initialize_achievements()
        return test_user

    @pytest.mark.unit
    def test_first_spin_achievement(self, user_with_achievements_setup, app_context):
        """Test FIRST_SPIN achievement unlocks after first bet."""
        from imperioApp import db
        user = user_with_achievements_setup

        # Create first bet transaction
        Transaction.create_transaction(
            user=user,
            transaction_type=TransactionType.BET,
            amount=-10,
            game_type=GameType.SLOTS,
            description="First bet"
        )
        db.session.commit()

        # Check achievements
        check_achievements(user)

        # Verify FIRST_SPIN was unlocked
        assert has_achievement(user.id, AchievementType.FIRST_SPIN)

    @pytest.mark.unit
    def test_first_win_achievement(self, user_with_achievements_setup, app_context):
        """Test FIRST_WIN achievement unlocks after first win."""
        from imperioApp import db
        user = user_with_achievements_setup

        # Create first win transaction
        Transaction.create_transaction(
            user=user,
            transaction_type=TransactionType.WIN,
            amount=50,
            game_type=GameType.SLOTS,
            description="First win"
        )
        db.session.commit()

        # Check achievements
        check_achievements(user)

        # Verify FIRST_WIN was unlocked
        assert has_achievement(user.id, AchievementType.FIRST_WIN)

    @pytest.mark.unit
    def test_total_spins_achievements(self, user_with_achievements_setup, app_context):
        """Test total spins achievements unlock at milestones."""
        from imperioApp import db
        user = user_with_achievements_setup

        # Create 10 bet transactions
        for i in range(10):
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.BET,
                amount=-5,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        # Check achievements
        check_achievements(user)

        # Verify TOTAL_SPINS_10 was unlocked
        assert has_achievement(user.id, AchievementType.TOTAL_SPINS_10)
        # Should not have 100 spins yet
        assert not has_achievement(user.id, AchievementType.TOTAL_SPINS_100)

    @pytest.mark.unit
    def test_big_win_achievements(self, user_with_achievements_setup, app_context):
        """Test big win achievements unlock for large wins."""
        user = user_with_achievements_setup

        # Test BIG_WIN_100
        newly_unlocked = check_single_win_achievements(user, 150)
        assert any(ua.achievement.achievement_type == AchievementType.BIG_WIN_100
                  for ua in newly_unlocked if ua is not None)

        # Test BIG_WIN_500
        newly_unlocked = check_single_win_achievements(user, 600)
        assert any(ua.achievement.achievement_type == AchievementType.BIG_WIN_500
                  for ua in newly_unlocked if ua is not None)

    @pytest.mark.unit
    def test_high_roller_achievement(self, user_with_achievements_setup, app_context):
        """Test HIGH_ROLLER achievement unlocks for large bets."""
        user = user_with_achievements_setup

        # Place a large bet
        newly_unlocked = check_single_bet_achievements(user, 1500)

        # Verify HIGH_ROLLER was unlocked
        assert any(ua.achievement.achievement_type == AchievementType.HIGH_ROLLER
                  for ua in newly_unlocked if ua is not None)

    @pytest.mark.unit
    def test_net_profit_achievements(self, user_with_achievements_setup, app_context):
        """Test net profit achievements unlock at milestones."""
        from imperioApp import db
        user = user_with_achievements_setup

        # Create transactions with net profit of 1200
        Transaction.create_transaction(
            user=user,
            transaction_type=TransactionType.BET,
            amount=-100,
            game_type=GameType.SLOTS
        )
        Transaction.create_transaction(
            user=user,
            transaction_type=TransactionType.WIN,
            amount=1300,
            game_type=GameType.SLOTS
        )
        db.session.commit()

        # Check achievements
        check_achievements(user)

        # Should have NET_PROFIT_1000
        assert has_achievement(user.id, AchievementType.NET_PROFIT_1000)

    @pytest.mark.unit
    def test_game_master_achievements(self, user_with_achievements_setup, app_context):
        """Test game-specific master achievements."""
        from imperioApp import db
        user = user_with_achievements_setup

        # Create 10 slots wins
        for _ in range(10):
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.WIN,
                amount=10,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        # Check achievements
        check_achievements(user)

        # Should have SLOTS_MASTER_10
        assert has_achievement(user.id, AchievementType.SLOTS_MASTER_10)

    @pytest.mark.unit
    def test_lucky_day_achievement(self, user_with_achievements_setup, app_context):
        """Test LUCKY_DAY achievement for 10 wins in one day."""
        from imperioApp import db
        user = user_with_achievements_setup

        # Create 10 win transactions today
        for _ in range(10):
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.WIN,
                amount=10,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        # Check achievements
        check_achievements(user)

        # Should have LUCKY_DAY
        assert has_achievement(user.id, AchievementType.LUCKY_DAY)


class TestWinningStreak:
    """Test suite for winning streak detection."""

    @pytest.fixture
    def user_with_streaks_setup(self, test_user, app_context):
        """Setup user with initialized achievements."""
        from imperioApp import db
        Achievement.query.delete()
        db.session.commit()
        initialize_achievements()
        return test_user

    @pytest.mark.unit
    def test_winning_streak_3(self, user_with_streaks_setup, app_context):
        """Test 3-game winning streak."""
        from imperioApp import db
        import uuid
        user = user_with_streaks_setup

        # Create 3 winning games
        for i in range(3):
            ref_id = str(uuid.uuid4())
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS,
                reference_id=ref_id
            )
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.WIN,
                amount=20,
                game_type=GameType.SLOTS,
                reference_id=ref_id
            )
        db.session.commit()

        # Check winning streak
        check_winning_streak(user)

        # Should have WINNING_STREAK_3
        assert has_achievement(user.id, AchievementType.WINNING_STREAK_3)

    @pytest.mark.unit
    def test_winning_streak_5(self, user_with_streaks_setup, app_context):
        """Test 5-game winning streak."""
        from imperioApp import db
        import uuid
        user = user_with_streaks_setup

        # Create 5 winning games
        for i in range(5):
            ref_id = str(uuid.uuid4())
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS,
                reference_id=ref_id
            )
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.WIN,
                amount=20,
                game_type=GameType.SLOTS,
                reference_id=ref_id
            )
        db.session.commit()

        # Check winning streak
        check_winning_streak(user)

        # Should have both WINNING_STREAK_3 and WINNING_STREAK_5
        assert has_achievement(user.id, AchievementType.WINNING_STREAK_3)
        assert has_achievement(user.id, AchievementType.WINNING_STREAK_5)

    @pytest.mark.unit
    def test_streak_broken_by_loss(self, user_with_streaks_setup, app_context):
        """Test that losing breaks the streak."""
        from imperioApp import db
        import uuid
        user = user_with_streaks_setup

        # Create 2 wins
        for i in range(2):
            ref_id = str(uuid.uuid4())
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS,
                reference_id=ref_id
            )
            Transaction.create_transaction(
                user=user,
                transaction_type=TransactionType.WIN,
                amount=20,
                game_type=GameType.SLOTS,
                reference_id=ref_id
            )

        # Create 1 loss
        ref_id = str(uuid.uuid4())
        Transaction.create_transaction(
            user=user,
            transaction_type=TransactionType.BET,
            amount=-10,
            game_type=GameType.SLOTS,
            reference_id=ref_id
        )
        # No WIN transaction = loss

        db.session.commit()

        # Check winning streak
        check_winning_streak(user)

        # Should NOT have WINNING_STREAK_3
        assert not has_achievement(user.id, AchievementType.WINNING_STREAK_3)


class TestLeaderboardAPI:
    """Test suite for leaderboard API endpoints."""

    @pytest.fixture
    def multiple_users(self, app_context):
        """Create multiple users with different stats."""
        from imperioApp import db

        users = []
        for i in range(5):
            user = User(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                coins=1000 + (i * 100),
                password='hashed_password'
            )
            db.session.add(user)
            users.append(user)

        db.session.commit()

        # Create different transaction histories
        for i, user in enumerate(users):
            wins_amount = (i + 1) * 100
            for _ in range(i + 1):
                Transaction.create_transaction(
                    user=user,
                    transaction_type=TransactionType.WIN,
                    amount=wins_amount,
                    game_type=GameType.SLOTS
                )

        db.session.commit()
        return users

    @pytest.mark.api
    def test_get_leaderboard_default(self, client, multiple_users):
        """Test GET /leaderboard with default parameters."""
        response = client.get('/leaderboard')

        assert response.status_code == 200
        data = response.get_json()
        assert 'leaderboard' in data
        assert 'timeframe' in data
        assert 'metric' in data
        assert len(data['leaderboard']) > 0

    @pytest.mark.api
    def test_get_leaderboard_by_coins(self, client, multiple_users):
        """Test leaderboard sorted by coins."""
        response = client.get('/leaderboard?metric=coins')

        assert response.status_code == 200
        data = response.get_json()
        leaderboard = data['leaderboard']

        # Should be sorted by coins descending
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]['coins'] >= leaderboard[i + 1]['coins']

    @pytest.mark.api
    def test_get_leaderboard_by_net_profit(self, client, multiple_users):
        """Test leaderboard sorted by net profit."""
        response = client.get('/leaderboard?metric=net_profit')

        assert response.status_code == 200
        data = response.get_json()
        leaderboard = data['leaderboard']

        # Verify net_profit is included
        assert 'net_profit' in leaderboard[0]

    @pytest.mark.api
    def test_get_leaderboard_timeframe(self, client, multiple_users):
        """Test leaderboard with different timeframes."""
        # Test daily
        response = client.get('/leaderboard?timeframe=daily')
        assert response.status_code == 200
        data = response.get_json()
        assert data['timeframe'] == 'daily'

        # Test weekly
        response = client.get('/leaderboard?timeframe=weekly')
        assert response.status_code == 200
        data = response.get_json()
        assert data['timeframe'] == 'weekly'

    @pytest.mark.api
    def test_get_my_leaderboard_rank(self, client, test_user, auth_headers, app_context):
        """Test GET /leaderboard/me."""
        response = client.get('/leaderboard/me', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'rank' in data
        assert 'total_users' in data
        assert 'percentile' in data
        assert data['user']['username'] == test_user.username


class TestAchievementAPI:
    """Test suite for achievement API endpoints."""

    @pytest.fixture
    def initialized_achievements_api(self, app_context):
        """Initialize achievements for API tests."""
        from imperioApp import db
        Achievement.query.delete()
        db.session.commit()
        initialize_achievements()

    @pytest.mark.api
    def test_get_all_achievements(self, client, initialized_achievements_api):
        """Test GET /achievements."""
        response = client.get('/achievements')

        assert response.status_code == 200
        data = response.get_json()
        assert 'achievements' in data
        assert len(data['achievements']) == 16

    @pytest.mark.api
    def test_get_user_achievements(self, client, test_user, auth_headers, initialized_achievements_api, app_context):
        """Test GET /achievements/user."""
        from imperioApp import db

        # Unlock some achievements
        unlock_achievement(test_user, AchievementType.FIRST_SPIN)
        unlock_achievement(test_user, AchievementType.FIRST_WIN)
        db.session.commit()

        response = client.get('/achievements/user', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'unlocked' in data
        assert len(data['unlocked']) == 2

    @pytest.mark.api
    def test_get_achievement_progress(self, client, test_user, auth_headers, initialized_achievements_api, app_context):
        """Test GET /achievements/progress."""
        from imperioApp import db

        # Create some game activity
        for _ in range(5):
            Transaction.create_transaction(
                user=test_user,
                transaction_type=TransactionType.BET,
                amount=-10,
                game_type=GameType.SLOTS
            )
        db.session.commit()

        response = client.get('/achievements/progress', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'progress' in data
        assert len(data['progress']) > 0

        # Check that progress has expected fields
        first_progress = data['progress'][0]
        assert 'achievement' in first_progress
        assert 'progress_percentage' in first_progress
        assert 'unlocked' in first_progress

    @pytest.mark.api
    def test_mark_achievement_as_seen(self, client, test_user, auth_headers, initialized_achievements_api, app_context):
        """Test POST /achievements/<id>/seen."""
        from imperioApp import db

        # Unlock achievement
        user_achievement = unlock_achievement(test_user, AchievementType.FIRST_SPIN)
        db.session.commit()

        # Initially not seen
        assert user_achievement.seen is False

        # Mark as seen
        response = client.post(f'/achievements/{user_achievement.id}/seen', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Achievement marked as seen'

        # Verify it was marked
        db.session.refresh(user_achievement)
        assert user_achievement.seen is True


class TestNotificationAPI:
    """Test suite for notification API endpoints."""

    @pytest.mark.api
    def test_get_notifications(self, client, test_user, auth_headers, app_context):
        """Test GET /notifications."""
        from imperioApp import db

        # Create notifications
        for i in range(5):
            Notification.create_notification(
                user=test_user,
                notification_type=NotificationType.SYSTEM,
                title=f"Test {i}",
                message="Test message",
                icon="📢"
            )
        db.session.commit()

        response = client.get('/notifications', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'notifications' in data
        assert 'unread_count' in data
        assert len(data['notifications']) == 5
        assert data['unread_count'] == 5

    @pytest.mark.api
    def test_mark_notification_as_read(self, client, test_user, auth_headers, app_context):
        """Test POST /notifications/<id>/read."""
        from imperioApp import db

        notification = Notification.create_notification(
            user=test_user,
            notification_type=NotificationType.SYSTEM,
            title="Test",
            message="Test message",
            icon="📢"
        )
        db.session.commit()

        # Initially unread
        assert notification.read is False

        response = client.post(f'/notifications/{notification.id}/read', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Notification marked as read'

        # Verify it was marked
        db.session.refresh(notification)
        assert notification.read is True

    @pytest.mark.api
    def test_mark_all_notifications_read(self, client, test_user, auth_headers, app_context):
        """Test POST /notifications/read-all."""
        from imperioApp import db

        # Create multiple notifications
        for i in range(3):
            Notification.create_notification(
                user=test_user,
                notification_type=NotificationType.SYSTEM,
                title=f"Test {i}",
                message="Test message",
                icon="📢"
            )
        db.session.commit()

        response = client.post('/notifications/read-all', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['marked_count'] == 3

        # Verify all are marked
        unread_count = Notification.query.filter_by(
            user_id=test_user.id,
            read=False
        ).count()
        assert unread_count == 0


class TestProfileAPI:
    """Test suite for user profile API."""

    @pytest.mark.api
    def test_get_user_profile(self, client, test_user, auth_headers, app_context):
        """Test GET /profile."""
        from imperioApp import db

        # Initialize achievements
        Achievement.query.delete()
        db.session.commit()
        initialize_achievements()

        # Create some game activity
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

        response = client.get('/profile', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert 'statistics' in data
        assert 'achievements' in data
        assert 'recent_activity' in data
        assert 'rank' in data

        # Verify user data
        assert data['user']['username'] == test_user.username

        # Verify statistics
        stats = data['statistics']
        assert 'total_bets_count' in stats
        assert stats['total_bets_count'] == 5

    @pytest.mark.api
    def test_profile_requires_auth(self, client):
        """Test that profile endpoint requires authentication."""
        response = client.get('/profile')
        assert response.status_code == 401


class TestGameAchievementIntegration:
    """Integration tests for achievement checking in games."""

    @pytest.fixture
    def game_test_setup(self, test_user, app_context):
        """Setup for game integration tests."""
        from imperioApp import db
        Achievement.query.delete()
        UserAchievement.query.delete()
        Notification.query.delete()
        db.session.commit()
        initialize_achievements()
        return test_user

    @pytest.mark.integration
    def test_slots_spin_checks_achievements(self, client, game_test_setup, auth_headers, app_context):
        """Test that spinning slots checks and unlocks achievements."""
        from imperioApp import db
        user = game_test_setup

        # First spin should unlock FIRST_SPIN achievement
        response = client.post('/spin', headers=auth_headers)
        assert response.status_code == 200

        # Check that FIRST_SPIN was unlocked
        assert has_achievement(user.id, AchievementType.FIRST_SPIN)

        # Check that notification was created
        notification = Notification.query.filter_by(
            user_id=user.id,
            notification_type=NotificationType.ACHIEVEMENT_UNLOCKED
        ).first()
        assert notification is not None

    @pytest.mark.integration
    def test_blackjack_checks_achievements(self, client, game_test_setup, auth_headers, app_context):
        """Test that blackjack checks achievements."""
        user = game_test_setup

        # Set user coins high enough for bet
        user.coins = 2000
        from imperioApp import db
        db.session.commit()

        # Start blackjack game
        response = client.post('/blackjack/start',
                              headers=auth_headers,
                              json={'wager': 50})

        if response.status_code == 200:
            # Check that FIRST_SPIN was unlocked (bet placed)
            assert has_achievement(user.id, AchievementType.FIRST_SPIN)

    @pytest.mark.integration
    def test_high_roller_achievement_integration(self, client, game_test_setup, auth_headers, app_context):
        """Test HIGH_ROLLER achievement unlocks with large bet."""
        user = game_test_setup

        # Set user coins high enough
        user.coins = 10000
        from imperioApp import db
        db.session.commit()

        # Place large blackjack bet
        response = client.post('/blackjack/start',
                              headers=auth_headers,
                              json={'wager': 1000})

        if response.status_code == 200:
            # Should unlock HIGH_ROLLER
            assert has_achievement(user.id, AchievementType.HIGH_ROLLER)

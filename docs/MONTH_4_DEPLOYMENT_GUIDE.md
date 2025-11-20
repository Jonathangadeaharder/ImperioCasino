# Month 4 Deployment & Verification Guide

## Quick Start

This guide helps you deploy and verify the Month 4 User Engagement features in your environment.

## Prerequisites

- Python 3.9+ installed
- PostgreSQL database (for production) or SQLite (for testing)
- All dependencies from `requirements.txt` installed
- Month 3 (Transaction History) already deployed

## Installation Steps

### 1. Install Dependencies

No new dependencies required for Month 4. Ensure existing dependencies are installed:

```bash
cd session_management
pip install -r requirements.txt
```

### 2. Run Database Migration

```bash
# From the project root
python deployment/scripts/add_engagement_tables.py

# Check migration status
python deployment/scripts/add_engagement_tables.py --status

# Verify migration
python deployment/scripts/add_engagement_tables.py --verify
```

Expected output:
```
================================================================================
 ImperioCasino - Engagement Tables Migration (Month 4)
================================================================================

Starting migration: Adding engagement tables...
Creating achievements table...
✓ Achievements table created successfully!
Creating user_achievements table...
✓ User achievements table created successfully!
Creating notifications table...
✓ Notifications table created successfully!

Initializing achievements...
✓ Achievements initialized! Total achievements: 16

Verifying migration...
✓ achievements table exists
✓ user_achievements table exists
✓ notifications table exists
✓ All 16 achievements initialized
✓ User achievements table is queryable. Current count: 0
✓ Notifications table is queryable. Current count: 0

✓ All verification checks passed!

================================================================================
 Migration completed successfully!
================================================================================
```

### 3. Verify Game Integration

Start the application and test achievement unlocking:

#### Test First Spin Achievement

```bash
# User's first spin should unlock FIRST_SPIN achievement
curl -X POST http://localhost:5000/spin \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Check if achievement was unlocked
curl http://localhost:5000/achievements/user \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should show FIRST_SPIN achievement in unlocked list
# User should have received +10 coins as reward
```

#### Test First Win Achievement

```bash
# Keep spinning until you win (winnings > 0)
curl -X POST http://localhost:5000/spin \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check achievements again
curl http://localhost:5000/achievements/user \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should show FIRST_WIN achievement unlocked (+25 coins)
```

#### Test Notification Creation

```bash
# Check notifications (should include achievement notifications)
curl http://localhost:5000/notifications \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should return:
# {
#   "notifications": [
#     {
#       "notification_type": "achievement_unlocked",
#       "title": "Achievement Unlocked: First Spin",
#       "message": "Place your first bet in any game +10 coins!",
#       "icon": "🎰",
#       "read": false
#     }
#   ],
#   "unread_count": 2
# }
```

### 4. Test API Endpoints

#### Get All Achievements

```bash
curl http://localhost:5000/achievements

# Should return all 16 achievements
# [
#   {
#     "achievement_type": "first_spin",
#     "name": "First Spin",
#     "description": "Place your first bet in any game",
#     "icon": "🎰",
#     "reward_coins": 10
#   },
#   ...
# ]
```

#### Get User Achievements

```bash
curl http://localhost:5000/achievements/user \
  -H "Authorization: Bearer YOUR_TOKEN"

# Returns:
# {
#   "unlocked": [...],  # Achievements user has unlocked
#   "locked": [...]     # Achievements user hasn't unlocked yet
# }
```

#### Get Achievement Progress

```bash
curl http://localhost:5000/achievements/progress \
  -H "Authorization: Bearer YOUR_TOKEN"

# Returns:
# {
#   "progress": [
#     {
#       "achievement": {
#         "achievement_type": "total_spins_10",
#         "name": "Getting Started"
#       },
#       "progress_percentage": 30,
#       "current_value": 3,
#       "target_value": 10,
#       "unlocked": false
#     }
#   ]
# }
```

#### Get Leaderboard

```bash
# Get default leaderboard (coins, all-time)
curl http://localhost:5000/leaderboard

# Get daily leaderboard by net profit
curl "http://localhost:5000/leaderboard?metric=net_profit&timeframe=daily"

# Get weekly leaderboard by total wins
curl "http://localhost:5000/leaderboard?metric=total_wins&timeframe=weekly"

# Returns:
# {
#   "leaderboard": [
#     {
#       "rank": 1,
#       "username": "player1",
#       "coins": 5000,
#       "net_profit": 2000,
#       "total_wins": 150
#     }
#   ],
#   "timeframe": "all_time",
#   "metric": "coins"
# }
```

#### Get My Rank

```bash
curl http://localhost:5000/leaderboard/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Returns:
# {
#   "rank": 42,
#   "total_users": 1000,
#   "percentile": 95.8,
#   "user": {
#     "username": "player1",
#     "coins": 2500
#   }
# }
```

#### Get User Profile

```bash
curl http://localhost:5000/profile \
  -H "Authorization: Bearer YOUR_TOKEN"

# Returns comprehensive profile with:
# - User details
# - Statistics (bets, wins, net profit, win rate)
# - Achievement summary
# - Recent activity
# - Leaderboard rank
```

#### Notification Management

```bash
# Get notifications
curl http://localhost:5000/notifications \
  -H "Authorization: Bearer YOUR_TOKEN"

# Mark specific notification as read
curl -X POST http://localhost:5000/notifications/1/read \
  -H "Authorization: Bearer YOUR_TOKEN"

# Mark all notifications as read
curl -X POST http://localhost:5000/notifications/read-all \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Verification Checklist

### Database

- [ ] Achievements table exists with 16 records
- [ ] User_achievements table exists
- [ ] Notifications table exists
- [ ] All tables have proper indexes
- [ ] Foreign keys to users table work
- [ ] All 16 achievement types are present

### Achievement System

- [ ] First spin unlocks FIRST_SPIN achievement
- [ ] First win unlocks FIRST_WIN achievement
- [ ] 10 bets unlock TOTAL_SPINS_10 achievement
- [ ] Win of 100+ coins unlocks BIG_WIN_100
- [ ] Bet of 1000+ coins unlocks HIGH_ROLLER
- [ ] 3 consecutive wins unlock WINNING_STREAK_3
- [ ] Coin rewards are added to user balance
- [ ] BONUS transactions are created for rewards
- [ ] Duplicate unlocks are prevented

### Notification System

- [ ] Notification created on achievement unlock
- [ ] Notification has correct title and message
- [ ] Notification has achievement icon
- [ ] Notifications can be marked as read
- [ ] All notifications can be marked as read at once
- [ ] Unread count is accurate

### Leaderboard System

- [ ] Leaderboard returns top users by coins
- [ ] Leaderboard can be sorted by net_profit
- [ ] Leaderboard can be sorted by total_wins
- [ ] Daily timeframe filters correctly
- [ ] Weekly timeframe filters correctly
- [ ] User rank calculation is accurate
- [ ] Percentile calculation is accurate

### API Endpoints

- [ ] GET /achievements returns all 16 achievements
- [ ] GET /achievements/user returns user's unlocked achievements
- [ ] GET /achievements/progress returns progress percentages
- [ ] POST /achievements/:id/seen marks achievement as seen
- [ ] GET /leaderboard returns rankings
- [ ] GET /leaderboard/me returns user's rank
- [ ] GET /notifications returns user's notifications
- [ ] POST /notifications/:id/read marks notification as read
- [ ] POST /notifications/read-all marks all as read
- [ ] GET /profile returns comprehensive user profile
- [ ] Unauthorized access returns 401

### Game Integration

- [ ] Slots checks achievements after each spin
- [ ] Blackjack checks achievements on game end
- [ ] Bet-based achievements checked correctly
- [ ] Win-based achievements checked correctly
- [ ] General achievements checked correctly
- [ ] Winning streak detection works

## Running Tests

```bash
cd session_management

# Run all engagement tests
pytest imperioApp/tests/test_engagement_pytest.py -v

# Run specific test class
pytest imperioApp/tests/test_engagement_pytest.py::TestAchievementModel -v

# Run with coverage
pytest imperioApp/tests/test_engagement_pytest.py \
  --cov=imperioApp.utils.models \
  --cov=imperioApp.utils.achievement_service \
  --cov=imperioApp.routes

# Run only unit tests
pytest imperioApp/tests/test_engagement_pytest.py -v -m unit

# Run only API tests
pytest imperioApp/tests/test_engagement_pytest.py -v -m api

# Run only integration tests
pytest imperioApp/tests/test_engagement_pytest.py -v -m integration
```

## Troubleshooting

### Migration Fails

**Error**: "Table already exists"
```bash
# Check if tables exist
python deployment/scripts/add_engagement_tables.py --status

# If they exist but are incomplete, you may need to drop them first
# WARNING: This deletes all engagement data!
python deployment/scripts/add_engagement_tables.py --rollback
python deployment/scripts/add_engagement_tables.py
```

**Error**: "No module named 'imperioApp'"
```bash
# Make sure you're running from the project root
cd /path/to/ImperioCasino
python deployment/scripts/add_engagement_tables.py
```

### Achievements Not Unlocking

1. **Check logs**: Look for errors in achievement checking
2. **Verify transaction recording**: Ensure transactions are being created (Month 3)
3. **Test manually**:

```python
from imperioApp import app, db
from imperioApp.utils.models import User, Achievement
from imperioApp.utils.achievement_service import unlock_achievement, check_achievements
from imperioApp.utils.models import AchievementType

with app.app_context():
    user = User.query.first()

    # Try manually unlocking achievement
    result = unlock_achievement(user, AchievementType.FIRST_SPIN)
    print(f"Unlock result: {result}")

    # Check all achievements
    newly_unlocked = check_achievements(user)
    print(f"Newly unlocked: {[ua.achievement.name for ua in newly_unlocked if ua]}")
```

### Notifications Not Created

1. **Check that achievements are unlocking**: Notifications only created on unlock
2. **Verify notification creation**:

```python
from imperioApp import app, db
from imperioApp.utils.models import Notification, NotificationType

with app.app_context():
    user_id = 1
    notifications = Notification.query.filter_by(user_id=user_id).all()
    print(f"User has {len(notifications)} notifications")

    for notif in notifications:
        print(f"- {notif.title} ({notif.notification_type.value})")
```

### Leaderboard Shows Incorrect Rankings

1. **Verify transaction data**: Leaderboard calculated from transactions
2. **Check timeframe filtering**:

```python
from imperioApp import app, db
from imperioApp.utils.models import Transaction, User
from datetime import datetime, timedelta
from sqlalchemy import func

with app.app_context():
    # Check daily stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    daily_wins = db.session.query(
        User.username,
        func.sum(Transaction.amount).label('total_wins')
    ).join(Transaction).filter(
        Transaction.transaction_type == 'win',
        Transaction.created_at >= today_start
    ).group_by(User.id, User.username).all()

    for username, total_wins in daily_wins:
        print(f"{username}: {total_wins} coins won today")
```

### Winning Streak Not Detected

1. **Check reference_id linking**: Bets and wins must share reference_id
2. **Verify recent transactions**:

```python
from imperioApp import app, db
from imperioApp.utils.models import Transaction, TransactionType

with app.app_context():
    user_id = 1

    # Get recent games
    recent = Transaction.query.filter_by(user_id=user_id).filter(
        Transaction.transaction_type.in_([TransactionType.BET, TransactionType.WIN])
    ).order_by(Transaction.created_at.desc()).limit(20).all()

    # Group by reference_id
    games = {}
    for trans in recent:
        if trans.reference_id:
            if trans.reference_id not in games:
                games[trans.reference_id] = {'bet': None, 'win': None}

            if trans.transaction_type == TransactionType.BET:
                games[trans.reference_id]['bet'] = trans
            elif trans.transaction_type == TransactionType.WIN:
                games[trans.reference_id]['win'] = trans

    # Check each game
    print("Recent games:")
    for ref_id, game in games.items():
        result = "WIN" if game['win'] else "LOSS"
        print(f"  {ref_id[:8]}: {result}")
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Backup database
- [ ] Test migration in staging environment
- [ ] Review achievement definitions
- [ ] Test all API endpoints
- [ ] Verify game integration
- [ ] Check error handling
- [ ] Test with high concurrency
- [ ] Load test leaderboard endpoints

### Deployment Steps

1. **Backup database**:
```bash
# PostgreSQL
pg_dump imperiocasino > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use the backup script
bash deployment/scripts/backup_database.sh
```

2. **Pull latest code**:
```bash
git pull origin main
```

3. **Run migration**:
```bash
python deployment/scripts/add_engagement_tables.py
```

4. **Restart application**:
```bash
sudo systemctl restart imperiocasino
```

5. **Verify**:
```bash
# Check health
curl http://localhost:5000/health

# Check achievements initialized
curl http://localhost:5000/achievements

# Should return 16 achievements
```

6. **Monitor logs**:
```bash
# Follow application logs
journalctl -u imperiocasino -f

# Look for achievement unlocks
grep "achievement_unlocked" /var/log/imperiocasino/app.log

# Or check log files
tail -f /var/log/imperiocasino/app.log
```

### Rollback Plan

If issues occur:

1. **Restore database**:
```bash
psql imperiocasino < backup_YYYYMMDD_HHMMSS.sql
```

2. **Revert code**:
```bash
git revert <commit-hash>
git push
```

3. **Restart application**:
```bash
sudo systemctl restart imperiocasino
```

## Performance Monitoring

### Check Query Performance

```sql
-- PostgreSQL: Check leaderboard query performance
EXPLAIN ANALYZE
SELECT u.id, u.username, u.coins,
       SUM(CASE WHEN t.transaction_type = 'win' THEN t.amount ELSE 0 END) as total_wins
FROM users u
LEFT JOIN transactions t ON u.id = t.user_id
GROUP BY u.id, u.username, u.coins
ORDER BY u.coins DESC
LIMIT 100;

-- Should complete in < 50ms with proper indexes

-- Check achievement unlock query
EXPLAIN ANALYZE
SELECT * FROM user_achievements
WHERE user_id = 1 AND achievement_id = 1;

-- Should use index, complete in < 5ms
```

### Monitor Database Size

```sql
-- Check table sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('achievements', 'user_achievements', 'notifications')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Monitor Achievement Unlock Rate

```python
from imperioApp import app, db
from imperioApp.utils.models import UserAchievement, Achievement
from datetime import datetime, timedelta
from sqlalchemy import func

with app.app_context():
    # Unlocks in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_unlocks = UserAchievement.query.filter(
        UserAchievement.unlocked_at >= yesterday
    ).count()

    print(f"Achievements unlocked in last 24h: {recent_unlocks}")

    # Most popular achievements
    popular = db.session.query(
        Achievement.name,
        func.count(UserAchievement.id).label('unlock_count')
    ).join(UserAchievement).group_by(
        Achievement.id, Achievement.name
    ).order_by(func.count(UserAchievement.id).desc()).limit(5).all()

    print("\nMost unlocked achievements:")
    for name, count in popular:
        print(f"  {name}: {count} users")
```

### Monitor Notification Volume

```python
from imperioApp import app, db
from imperioApp.utils.models import Notification
from datetime import datetime, timedelta

with app.app_context():
    # Notifications in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_count = Notification.query.filter(
        Notification.created_at >= one_hour_ago
    ).count()

    print(f"Notifications in last hour: {recent_count}")

    # Unread notifications
    unread_count = Notification.query.filter_by(read=False).count()
    print(f"Total unread notifications: {unread_count}")
```

## Success Metrics

After deployment, you should see:

### Engagement Metrics
- **Achievement Unlock Rate**: 5-10 achievements per active user in first week
- **Notification Interaction**: 60-80% of notifications marked as read
- **Leaderboard Views**: 20-30% of active users view leaderboard daily
- **Profile Views**: 40-50% of users view their profile

### Performance Metrics
- **API Response Time**: < 100ms for achievement endpoints
- **Leaderboard Query**: < 50ms for top 100 users
- **Achievement Check**: < 20ms per game completion
- **No Errors**: No achievement-related errors in logs

### User Impact
- **Increased Engagement**: 20-30% more games played per session
- **Improved Retention**: 15-20% improvement in 7-day retention
- **User Satisfaction**: Positive feedback on gamification features

## Common Issues and Solutions

### Issue: Achievement unlocked multiple times

**Cause**: Race condition in achievement checking

**Solution**: Achievement unlocking already has duplicate prevention via UNIQUE constraint on `(user_id, achievement_id)`. If seeing duplicates, check for concurrent requests.

### Issue: Leaderboard shows stale data

**Cause**: Leaderboard calculated in real-time from transactions

**Solution**: Check that transactions are being created correctly (Month 3 feature). If needed, add caching with short TTL.

### Issue: Progress percentage > 100%

**Cause**: User exceeded target value significantly

**Solution**: Already capped at 100% in code with `min(progress, 100)`. If seeing > 100%, check progress calculation logic.

### Issue: Winning streak not detected

**Cause**: Missing reference_id in transactions

**Solution**: Ensure all BET and WIN transactions have matching reference_id:
```python
import uuid
ref_id = str(uuid.uuid4())
# Use same ref_id for bet and win
```

## Next Steps

After successful deployment:

1. **Monitor for 24-48 hours**: Watch for errors, performance issues
2. **Gather user feedback**: Survey users on achievement system
3. **Analyze engagement metrics**: Track games played, retention
4. **Plan frontend integration**: Design achievement popups, leaderboard UI
5. **Consider Month 5 features**: Social features, friend system, challenges

## Support

For issues or questions:
- Check logs first (`journalctl -u imperiocasino -f`)
- Review `docs/MONTH_4_COMPLETE.md` for detailed documentation
- Test endpoints with curl
- Verify database state with SQL queries
- Check game logic for achievement integration
- Run test suite for validation

## Additional Resources

- **Complete Documentation**: `docs/MONTH_4_COMPLETE.md`
- **Test Suite**: `imperioApp/tests/test_engagement_pytest.py`
- **Migration Script**: `deployment/scripts/add_engagement_tables.py`
- **Achievement Service**: `imperioApp/utils/achievement_service.py`
- **API Routes**: `imperioApp/routes.py` (lines 450-850)

# Month 3 Deployment & Verification Guide

## Quick Start

This guide helps you deploy and verify the Month 3 Transaction History & Wallet Management features in your environment.

## Prerequisites

- Python 3.9+ installed
- PostgreSQL database (for production) or SQLite (for testing)
- Redis server (optional, for production rate limiting)
- All dependencies from `requirements.txt` installed

## Installation Steps

### 1. Install Dependencies

```bash
cd session_management
pip install -r requirements.txt
```

### 2. Run Database Migration

```bash
# From the project root
python deployment/scripts/add_transactions_table.py

# Check migration status
python deployment/scripts/add_transactions_table.py --status

# Verify migration
python deployment/scripts/add_transactions_table.py --verify
```

Expected output:
```
================================================================================
 ImperioCasino - Transactions Table Migration (Month 3)
================================================================================

Starting migration: Adding transactions table...
Creating transactions table...
✓ Transactions table created successfully!

Verifying migration...
✓ Table is queryable. Current transaction count: 0
✓ Test transaction created: ID 1
✓ Test transaction retrieved successfully
✓ Serialization works: Migration test transaction
✓ Test transaction deleted

✓ All verification checks passed!

================================================================================
 Migration completed successfully!
================================================================================
```

### 3. Verify Game Integration

Start the application and test each game:

#### Test Slots
```bash
curl -X POST http://localhost:5000/spin \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Should return:
# {"stopSegments": [15, 22, 18], "totalCoins": 999}
```

Then check transactions:
```bash
curl http://localhost:5000/transactions/recent \
  -H "Authorization: Bearer YOUR_TOKEN"

# Should show BET transaction and possibly WIN transaction
```

#### Test Blackjack
```bash
# Start game
curl -X POST http://localhost:5000/blackjack/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wager": 50}'

# Check transactions
curl http://localhost:5000/transactions?game=blackjack \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Test Roulette
```bash
# Place bet
curl -X POST http://localhost:5000/roulette/spin \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bet": [{"numbers": "1,2,3", "odds": 10, "amt": 10}]}'

# Check transactions
curl http://localhost:5000/transactions?game=roulette \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Test API Endpoints

#### Get Transaction History
```bash
# Get all transactions
curl http://localhost:5000/transactions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get with pagination
curl "http://localhost:5000/transactions?limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by type
curl "http://localhost:5000/transactions?type=win" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by game
curl "http://localhost:5000/transactions?game=slots" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Statistics
```bash
# Overall statistics
curl http://localhost:5000/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"

# Game-specific statistics
curl http://localhost:5000/statistics/game/slots \
  -H "Authorization: Bearer YOUR_TOKEN"

curl http://localhost:5000/statistics/game/blackjack \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Verification Checklist

### Database

- [ ] Transactions table exists
- [ ] Table has all required columns (id, user_id, transaction_type, game_type, amount, balance_before, balance_after, description, metadata, reference_id, created_at)
- [ ] Indexes are created (idx_user_transactions, idx_transaction_type, idx_game_type, idx_created_at)
- [ ] Foreign key to users table works

### Game Integration

- [ ] Slots creates BET transaction (-1 coin)
- [ ] Slots creates WIN transaction on wins
- [ ] Blackjack creates BET transaction on game start
- [ ] Blackjack creates WIN/REFUND transaction on game end
- [ ] Roulette creates BET transaction on spin
- [ ] Roulette creates WIN transaction on winning spins
- [ ] Reference IDs link related transactions

### API Endpoints

- [ ] GET /transactions returns transaction history
- [ ] Pagination works (limit, offset)
- [ ] Filtering by transaction type works
- [ ] Filtering by game type works
- [ ] GET /transactions/<id> returns specific transaction
- [ ] GET /transactions/recent returns 10 most recent
- [ ] GET /statistics returns user stats
- [ ] GET /statistics/game/<type> returns game-specific stats
- [ ] Unauthorized access returns 401

### Data Integrity

- [ ] Balance_before equals user's balance before transaction
- [ ] Balance_after equals balance_before + amount
- [ ] BET transactions have negative amounts
- [ ] WIN/REFUND transactions have positive amounts
- [ ] User's actual coin balance matches transaction records
- [ ] Concurrent spins don't cause race conditions

## Running Tests

```bash
cd session_management

# Run all transaction tests
pytest imperioApp/tests/test_transactions_pytest.py -v

# Run specific test class
pytest imperioApp/tests/test_transactions_pytest.py::TestTransactionModel -v

# Run with coverage
pytest imperioApp/tests/test_transactions_pytest.py --cov=imperioApp.utils.models --cov=imperioApp.game_logic

# Run integration tests
pytest imperioApp/tests/test_transactions_pytest.py -v -m integration
```

## Troubleshooting

### Migration Fails

**Error**: "Table already exists"
```bash
# Check if table exists
python deployment/scripts/add_transactions_table.py --status

# If it exists but is incomplete, you may need to drop it first
# WARNING: This deletes all transaction data!
python deployment/scripts/add_transactions_table.py --rollback
python deployment/scripts/add_transactions_table.py
```

**Error**: "No module named 'imperioApp'"
```bash
# Make sure you're running from the project root
cd /path/to/ImperioCasino
python deployment/scripts/add_transactions_table.py
```

### Transactions Not Being Created

1. **Check logs**: Look for error messages in application logs
2. **Verify database connection**: Ensure app can connect to database
3. **Check commits**: Ensure `db.session.commit()` is called
4. **Test query**: Try `Transaction.query.count()` in Python shell

```python
from imperioApp import app, db
from imperioApp.utils.models import Transaction

with app.app_context():
    count = Transaction.query.count()
    print(f"Total transactions: {count}")
```

### Statistics Are Wrong

1. **Check transaction types**: Ensure BETs are negative, WINs are positive
2. **Verify enum values**: Check that transaction_type and game_type are correct
3. **Test query directly**:

```python
from imperioApp import app, db
from imperioApp.utils.models import Transaction, TransactionType

with app.app_context():
    user_id = 1
    bets = Transaction.query.filter_by(
        user_id=user_id,
        transaction_type=TransactionType.BET
    ).count()
    print(f"Total bets: {bets}")
```

### Balance Discrepancies

If user balance doesn't match transaction history:

```python
from imperioApp import app, db
from imperioApp.utils.models import Transaction, User

with app.app_context():
    user = User.query.get(1)

    # Calculate balance from transactions
    from sqlalchemy import func
    result = db.session.query(func.sum(Transaction.amount)).filter_by(
        user_id=user.id
    ).scalar()

    calculated_balance = 1000 + (result or 0)  # 1000 = DEFAULT_COINS

    print(f"User's current balance: {user.coins}")
    print(f"Calculated from transactions: {calculated_balance}")
    print(f"Difference: {user.coins - calculated_balance}")
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Backup database
- [ ] Test migration in staging environment
- [ ] Review transaction recording logic
- [ ] Test all API endpoints
- [ ] Check error handling
- [ ] Verify authentication works
- [ ] Test with high concurrency

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
python deployment/scripts/add_transactions_table.py
```

4. **Restart application**:
```bash
sudo systemctl restart imperiocasino
```

5. **Verify**:
```bash
# Check health
curl http://localhost:5000/health

# Check transaction endpoints
curl http://localhost:5000/transactions/recent \
  -H "Authorization: Bearer YOUR_TOKEN"
```

6. **Monitor logs**:
```bash
# Follow application logs
journalctl -u imperiocasino -f

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

### Check Transaction Query Performance

```sql
-- PostgreSQL: Check query performance
EXPLAIN ANALYZE
SELECT * FROM transactions
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 50;

-- Should use idx_user_transactions index
-- Should complete in < 10ms
```

### Monitor Database Size

```sql
-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('transactions'));

-- Check index sizes
SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND tablename = 'transactions';
```

### Monitor Transaction Volume

```python
from imperioApp import app, db
from imperioApp.utils.models import Transaction
from datetime import datetime, timedelta

with app.app_context():
    # Transactions in last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_count = Transaction.query.filter(
        Transaction.created_at >= one_hour_ago
    ).count()

    print(f"Transactions in last hour: {recent_count}")
    print(f"Rate: {recent_count / 60:.2f} per minute")
```

## Success Metrics

After deployment, you should see:

- **Transaction Creation**: Every game action creates appropriate transactions
- **API Response Time**: < 100ms for transaction queries
- **Balance Accuracy**: User balances match transaction history
- **No Errors**: No transaction-related errors in logs
- **Complete Audit Trail**: All coin movements are tracked

## Support

For issues or questions:
- Check logs first
- Review `docs/MONTH_3_COMPLETE.md` for detailed documentation
- Test endpoints with curl
- Verify database state with SQL queries
- Check game logic for transaction creation

## Next Steps

After successful deployment:
1. Monitor for 24-48 hours
2. Verify no performance issues
3. Check data accuracy daily
4. Plan frontend integration (display transaction history)
5. Consider implementing Month 4 features

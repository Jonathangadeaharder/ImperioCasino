"""
Database query optimization utilities (Month 5).

This module provides:
- Query performance monitoring
- Common optimized queries
- Database connection health checks
- Query result caching
"""

from flask import request
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from .. import db, cache
import time
import structlog
from functools import wraps

log = structlog.get_logger()

# Track slow queries (> 100ms)
SLOW_QUERY_THRESHOLD = 0.1  # seconds


def enable_query_profiling():
    """Enable query performance profiling for development"""

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_time = time.time() - conn.info['query_start_time'].pop(-1)

        if total_time > SLOW_QUERY_THRESHOLD:
            log.warning(
                "slow_query",
                duration=total_time,
                statement=statement[:200],  # Truncate long queries
                parameters=parameters if len(str(parameters)) < 200 else "..."
            )


def check_database_health():
    """Check database connection health"""
    try:
        # Simple query to test connection
        db.session.execute(text('SELECT 1'))
        return True
    except Exception as e:
        log.error("database_health_check_failed", error=str(e))
        return False


def cached_query(timeout=300, key_prefix='query'):
    """
    Decorator to cache query results.

    Usage:
        @cached_query(timeout=600, key_prefix='user_stats')
        def get_user_statistics(user_id):
            return expensive_query(user_id)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{f.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                log.debug("cache_hit", key=cache_key)
                return result

            # Execute function and cache result
            log.debug("cache_miss", key=cache_key)
            result = f(*args, **kwargs)

            if result is not None:
                cache.set(cache_key, result, timeout=timeout)

            return result

        return decorated_function
    return decorator


# ============================================================================
# Optimized Query Functions
# ============================================================================

@cached_query(timeout=60, key_prefix='top_users')
def get_top_users_by_coins(limit=100):
    """Get top users by coin balance with caching"""
    from ..utils.models import User

    users = db.session.query(
        User.id,
        User.username,
        User.coins
    ).order_by(User.coins.desc()).limit(limit).all()

    return [
        {'id': u.id, 'username': u.username, 'coins': u.coins}
        for u in users
    ]


@cached_query(timeout=300, key_prefix='user_stats')
def get_user_statistics_cached(user_id):
    """Get user statistics with caching"""
    from ..utils.models import Transaction, TransactionType
    from sqlalchemy import func

    # Aggregate statistics in a single query
    stats = db.session.query(
        func.count(func.distinct(Transaction.id)).filter(
            Transaction.transaction_type == TransactionType.BET
        ).label('total_bets'),
        func.coalesce(
            func.sum(func.abs(Transaction.amount)).filter(
                Transaction.transaction_type == TransactionType.BET
            ), 0
        ).label('total_wagered'),
        func.count(func.distinct(Transaction.id)).filter(
            Transaction.transaction_type == TransactionType.WIN
        ).label('total_wins'),
        func.coalesce(
            func.sum(Transaction.amount).filter(
                Transaction.transaction_type == TransactionType.WIN
            ), 0
        ).label('total_won'),
        func.max(Transaction.amount).filter(
            Transaction.transaction_type == TransactionType.WIN
        ).label('biggest_win')
    ).filter(Transaction.user_id == user_id).first()

    return {
        'total_bets': stats.total_bets or 0,
        'total_wagered': int(stats.total_wagered or 0),
        'total_wins': stats.total_wins or 0,
        'total_won': int(stats.total_won or 0),
        'net_profit': int((stats.total_won or 0) - (stats.total_wagered or 0)),
        'biggest_win': int(stats.biggest_win or 0),
        'win_rate': (stats.total_wins / stats.total_bets * 100) if stats.total_bets > 0 else 0
    }


def invalidate_user_cache(user_id):
    """Invalidate all cached queries for a user"""
    # Clear user-specific caches
    patterns = [
        f"query:get_user_statistics_cached:({user_id},)",
        f"leaderboard_*",  # Leaderboards might have changed
    ]

    for pattern in patterns:
        cache.delete(pattern)

    log.info("cache_invalidated", user_id=user_id, patterns=patterns)


def get_recent_transactions_optimized(user_id, limit=50, offset=0):
    """Get recent transactions with optimized query"""
    from ..utils.models import Transaction

    # Use index on (user_id, created_at) for efficient retrieval
    transactions = db.session.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(limit).offset(offset).all()

    return [t.to_dict() for t in transactions]


def get_game_statistics_optimized(user_id, game_type):
    """Get game-specific statistics with optimized query"""
    from ..utils.models import Transaction, TransactionType, GameType
    from sqlalchemy import func

    stats = db.session.query(
        func.count(func.distinct(Transaction.id)).filter(
            Transaction.transaction_type == TransactionType.BET
        ).label('total_bets'),
        func.coalesce(
            func.sum(func.abs(Transaction.amount)).filter(
                Transaction.transaction_type == TransactionType.BET
            ), 0
        ).label('total_wagered'),
        func.count(func.distinct(Transaction.id)).filter(
            Transaction.transaction_type == TransactionType.WIN
        ).label('total_wins'),
        func.coalesce(
            func.sum(Transaction.amount).filter(
                Transaction.transaction_type == TransactionType.WIN
            ), 0
        ).label('total_won')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.game_type == game_type
    ).first()

    return {
        'game_type': game_type.value,
        'total_bets': stats.total_bets or 0,
        'total_wagered': int(stats.total_wagered or 0),
        'total_wins': stats.total_wins or 0,
        'total_won': int(stats.total_won or 0),
        'net_profit': int((stats.total_won or 0) - (stats.total_wagered or 0)),
        'win_rate': (stats.total_wins / stats.total_bets * 100) if stats.total_bets > 0 else 0
    }


# ============================================================================
# Index Management
# ============================================================================

def ensure_indexes():
    """Ensure all performance-critical indexes exist"""
    from sqlalchemy import inspect

    inspector = inspect(db.engine)

    # List of critical indexes
    critical_indexes = {
        'transactions': ['idx_user_transactions', 'idx_transaction_type', 'idx_reference_id'],
        'users': ['idx_username', 'idx_email'],
        'notifications': ['idx_user_notifications', 'idx_unread_notifications'],
        'achievements': ['idx_achievement_type'],
        'user_achievements': ['idx_user_achievement']
    }

    for table, indexes in critical_indexes.items():
        table_indexes = [idx['name'] for idx in inspector.get_indexes(table)]

        for index in indexes:
            if index not in table_indexes:
                log.warning(
                    "missing_index",
                    table=table,
                    index=index,
                    message=f"Consider adding index: {index}"
                )


def get_table_sizes():
    """Get database table sizes (PostgreSQL only)"""
    try:
        if db.engine.dialect.name == 'postgresql':
            result = db.session.execute(text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                    pg_total_relation_size(schemaname||'.'||tablename) AS bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY bytes DESC;
            """))

            return [
                {
                    'schema': row[0],
                    'table': row[1],
                    'size': row[2],
                    'bytes': row[3]
                }
                for row in result
            ]
        else:
            return []
    except Exception as e:
        log.error("get_table_sizes_failed", error=str(e))
        return []


def analyze_query_performance(query_sql, explain=True):
    """Analyze query performance using EXPLAIN"""
    try:
        if explain and db.engine.dialect.name == 'postgresql':
            result = db.session.execute(
                text(f"EXPLAIN ANALYZE {query_sql}")
            )

            plan = [row[0] for row in result]
            return {
                'query': query_sql,
                'plan': plan
            }
        else:
            return {'query': query_sql, 'plan': ['EXPLAIN not supported for this database']}
    except Exception as e:
        log.error("analyze_query_failed", error=str(e))
        return {'error': str(e)}


# ============================================================================
# Connection Pool Monitoring
# ============================================================================

def get_connection_pool_stats():
    """Get connection pool statistics"""
    try:
        pool = db.engine.pool

        return {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.size() + pool.overflow()
        }
    except Exception as e:
        log.error("connection_pool_stats_failed", error=str(e))
        return {}


def warmup_cache():
    """Pre-populate cache with commonly accessed data"""
    log.info("cache_warmup_started")

    try:
        # Cache top users
        get_top_users_by_coins(limit=100)

        # Cache leaderboards
        from ..socketio_events import get_leaderboard_data

        for metric in ['coins', 'net_profit', 'total_wins']:
            for timeframe in ['daily', 'weekly', 'all_time']:
                get_leaderboard_data(metric, timeframe, limit=100)

        log.info("cache_warmup_completed")
    except Exception as e:
        log.error("cache_warmup_failed", error=str(e))

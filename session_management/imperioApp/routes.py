import jwt
from flask import render_template, flash, redirect, url_for, request, jsonify, session
from flask_login import current_user, login_required
from urllib.parse import urlparse
from . import app, limiter, cache
from .utils.forms import LoginForm, RegistrationForm
from .utils.models import User
import logging

# Import the new modules
from .utils.auth import generate_token, login_user_session, logout_user_session, token_required
from .utils.services import get_user_by_username, create_user, update_user_coins
from .game_logic.cherrycharm import cherryAction
from .game_logic.blackjack import start_game, player_action
from .game_logic.roulette import rouletteAction

# Health check and monitoring endpoints


@app.route("/health")
def health_check():
    """
    Health check endpoint for load balancers and monitoring systems.
    Returns 200 if the application is healthy.
    """
    health_status = {"status": "healthy", "checks": {}}
    http_status = 200

    # Check database connection
    try:
        from . import db
        from sqlalchemy import text

        db.session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
        http_status = 503

    # Check Redis connection (for rate limiting)
    try:
        import redis

        redis_url = app.config.get("REDIS_URL")
        if redis_url and redis_url != "memory://":
            r = redis.from_url(redis_url, socket_connect_timeout=5)
            r.ping()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "not configured (using memory)"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        # Redis is not critical, so don't mark as unhealthy
        # health_status['status'] = 'degraded'

    return jsonify(health_status), http_status


@app.route("/health/live")
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the application process is running.
    """
    return jsonify({"status": "alive"}), 200


@app.route("/health/ready")
def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if the application is ready to serve traffic.
    """
    from . import db

    try:
        # Check if database is accessible
        db.session.execute("SELECT 1")
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        logging.error(f"Readiness check failed: {e}")
        return jsonify({"status": "not ready", "reason": str(e)}), 503


@app.route("/metrics")
def metrics():
    """
    Basic metrics endpoint for monitoring.
    Returns application statistics.
    """
    from .utils.models import User

    try:
        # Get some basic metrics
        user_count = User.query.count()

        metrics_data = {
            "total_users": user_count,
            "app_version": "2.0.0",
            "environment": app.config.get("FLASK_ENV", "unknown"),
        }

        return jsonify(metrics_data), 200
    except Exception as e:
        logging.error(f"Metrics endpoint error: {e}")
        return jsonify({"error": "Unable to retrieve metrics"}), 500


@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", title="Dashboard")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_username(form.username.data)
        if user is None or not user.verify_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user_session(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        if not next_page or urlparse(next_page).netloc != "":
            next_page = url_for("dashboard")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user_session()
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = get_user_by_username(form.username.data)
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_user or existing_email:
            flash("Username or email already exists")
            return redirect(url_for("signup"))

        create_user(form.username.data, form.email.data, form.password.data)
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("signup.html", title="Register", form=form)


@app.route("/redirect-imperio")
@login_required
def redirect_to_imperio():
    username = current_user.username
    token = session.get("token")
    if not token:
        token = generate_token(current_user.username)
        session["token"] = token
    return redirect(f"{app.config['CHERRY_CHARM_URL']}/?username={username}&token={token}")


@app.route("/verify-token", methods=["POST"])
def verify_token():
    from session_management.imperioApp.utils.auth import decode_token

    data = request.get_json()
    token = data.get("token")
    username = data.get("username")

    if not token or not username:
        return jsonify({"message": "Token and username are required"}), 400

    try:
        decoded_token = decode_token(token)
        user = get_user_by_username(decoded_token["user_id"])

        if user:
            return jsonify({"message": "Token is valid"}), 200
        else:
            return jsonify({"message": "Invalid token or username"}), 401

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401


@app.route("/getCoins", methods=["GET"])
@token_required
def get_coins(current_user):
    logging.debug("Received getCoins request for user_id: %s with coins: %s", current_user.username, current_user.coins)
    return jsonify({"coins": current_user.coins}), 200


@app.route("/updateCoins", methods=["POST"])
@token_required
def update_coins(current_user):
    data = request.get_json()
    coins = data.get("coins")
    logging.debug("Received updateCoins request for user_id: %s with coins: %s", current_user.username, coins)

    if coins is None:
        logging.warning("Coins are missing in updateCoins request.")
        return jsonify({"message": "Coins are required"}), 400

    update_user_coins(current_user, coins)
    logging.info("Coins successfully updated for user_id: %s to %s coins", current_user.username, coins)
    return jsonify({"message": "Coins updated successfully"}), 200


# ========== Transaction History Endpoints (Month 3) ==========


@app.route("/transactions", methods=["GET"])
@token_required
def get_transactions(current_user):
    """
    Get transaction history for the current user with optional filtering.

    Query parameters:
    - limit: Number of transactions to return (default: 50, max: 200)
    - offset: Number of transactions to skip for pagination (default: 0)
    - type: Filter by transaction type (bet, win, loss, deposit, etc.)
    - game: Filter by game type (slots, blackjack, roulette)
    """
    from .utils.models import Transaction, TransactionType, GameType

    # Get query parameters
    limit = min(int(request.args.get("limit", 50)), 200)  # Cap at 200
    offset = int(request.args.get("offset", 0))
    transaction_type_str = request.args.get("type")
    game_type_str = request.args.get("game")

    # Convert string parameters to enums
    transaction_type = None
    game_type = None

    if transaction_type_str:
        try:
            transaction_type = TransactionType[transaction_type_str.upper()]
        except KeyError:
            return jsonify({"message": f"Invalid transaction type: {transaction_type_str}"}), 400

    if game_type_str:
        try:
            game_type = GameType[game_type_str.upper()]
        except KeyError:
            return jsonify({"message": f"Invalid game type: {game_type_str}"}), 400

    # Get transactions
    transactions = Transaction.get_user_transactions(
        user_id=current_user.id, limit=limit, offset=offset, transaction_type=transaction_type, game_type=game_type
    )

    # Get total count for pagination info
    query = Transaction.query.filter_by(user_id=current_user.id)
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    if game_type:
        query = query.filter_by(game_type=game_type)
    total_count = query.count()

    return (
        jsonify(
            {
                "transactions": [t.to_dict() for t in transactions],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": (offset + limit) < total_count,
                },
            }
        ),
        200,
    )


@app.route("/transactions/<int:transaction_id>", methods=["GET"])
@token_required
def get_transaction_detail(current_user, transaction_id):
    """Get details of a specific transaction."""
    from .utils.models import Transaction

    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()

    if not transaction:
        return jsonify({"message": "Transaction not found"}), 404

    return jsonify(transaction.to_dict()), 200


@app.route("/transactions/recent", methods=["GET"])
@token_required
def get_recent_transactions(current_user):
    """Get the 10 most recent transactions for quick display."""
    from .utils.models import Transaction

    transactions = Transaction.get_user_transactions(user_id=current_user.id, limit=10, offset=0)

    return jsonify({"transactions": [t.to_dict() for t in transactions]}), 200


@app.route("/statistics", methods=["GET"])
@token_required
def get_user_statistics(current_user):
    """
    Get comprehensive statistics for the current user.

    Returns:
    - Total bets placed and amount wagered
    - Total wins and amount won
    - Net profit/loss
    - Statistics broken down by game type

    Cached for 2 minutes to improve performance.
    """
    from .utils.models import Transaction

    # Try to get from cache
    cache_key = f"user_stats:{current_user.id}"
    stats = cache.get(cache_key)

    if stats is None:
        # Cache miss - query database
        stats = Transaction.get_user_statistics(current_user.id)
        stats["current_balance"] = current_user.coins

        # Cache for 2 minutes
        cache.set(cache_key, stats, timeout=120)
    else:
        # Update current balance (always fresh)
        stats["current_balance"] = current_user.coins

    return jsonify(stats), 200


@app.route("/statistics/game/<game_type>", methods=["GET"])
@token_required
def get_game_statistics(current_user, game_type):
    """Get statistics for a specific game type."""
    from .utils.models import Transaction, GameType, TransactionType
    from . import db
    from sqlalchemy import func

    try:
        game_enum = GameType[game_type.upper()]
    except KeyError:
        return jsonify({"message": f"Invalid game type: {game_type}"}), 400

    # Get bets for this game
    total_bets = (
        db.session.query(func.count(Transaction.id), func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == TransactionType.BET,
            Transaction.game_type == game_enum,
        )
        .first()
    )

    # Get wins for this game
    total_wins = (
        db.session.query(func.count(Transaction.id), func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == TransactionType.WIN,
            Transaction.game_type == game_enum,
        )
        .first()
    )

    return (
        jsonify(
            {
                "game_type": game_type,
                "total_bets_count": total_bets[0] or 0,
                "total_bets_amount": abs(total_bets[1] or 0),
                "total_wins_count": total_wins[0] or 0,
                "total_wins_amount": total_wins[1] or 0,
                "net_profit": (total_wins[1] or 0) + (total_bets[1] or 0),
            }
        ),
        200,
    )


# ========== End Transaction History Endpoints ==========

# ========== Leaderboard Endpoints (Month 4) ==========


@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """
    Get global leaderboard.

    Query parameters:
    - timeframe: 'daily', 'weekly', or 'all_time' (default: 'all_time')
    - metric: 'coins', 'net_profit', or 'total_wins' (default: 'coins')
    - limit: Number of results (default: 10, max: 100)
    """
    from .utils.models import Transaction, TransactionType
    from sqlalchemy import func
    from datetime import timedelta, datetime
    from . import db

    timeframe = request.args.get("timeframe", "all_time")
    metric = request.args.get("metric", "coins")
    limit = min(int(request.args.get("limit", 10)), 100)

    # Calculate date filter for timeframe
    date_filter = None
    if timeframe == "daily":
        date_filter = datetime.utcnow() - timedelta(days=1)
    elif timeframe == "weekly":
        date_filter = datetime.utcnow() - timedelta(days=7)

    if metric == "coins":
        # Leaderboard by current coins
        users = User.query.order_by(User.coins.desc()).limit(limit).all()
        leaderboard = [
            {"rank": idx + 1, "username": user.username, "value": user.coins, "metric": "coins"}
            for idx, user in enumerate(users)
        ]

    elif metric == "net_profit":
        # Leaderboard by net profit
        query = db.session.query(Transaction.user_id, func.sum(Transaction.amount).label("net_profit"))

        if date_filter:
            query = query.filter(Transaction.created_at >= date_filter)

        rankings = query.group_by(Transaction.user_id).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()

        leaderboard = []
        for idx, (user_id, net_profit) in enumerate(rankings):
            user = User.query.get(user_id)
            if user:
                leaderboard.append(
                    {
                        "rank": idx + 1,
                        "username": user.username,
                        "value": int(net_profit) if net_profit else 0,
                        "metric": "net_profit",
                    }
                )

    elif metric == "total_wins":
        # Leaderboard by total wins
        query = db.session.query(Transaction.user_id, func.count(Transaction.id).label("win_count")).filter(
            Transaction.transaction_type == TransactionType.WIN
        )

        if date_filter:
            query = query.filter(Transaction.created_at >= date_filter)

        rankings = query.group_by(Transaction.user_id).order_by(func.count(Transaction.id).desc()).limit(limit).all()

        leaderboard = []
        for idx, (user_id, win_count) in enumerate(rankings):
            user = User.query.get(user_id)
            if user:
                leaderboard.append(
                    {"rank": idx + 1, "username": user.username, "value": win_count, "metric": "total_wins"}
                )
    else:
        return jsonify({"message": "Invalid metric"}), 400

    return jsonify({"leaderboard": leaderboard, "timeframe": timeframe, "metric": metric}), 200


@app.route("/leaderboard/me", methods=["GET"])
@token_required
def get_my_leaderboard_rank(current_user):
    """Get current user's rank on the leaderboard."""
    # Get rank by coins
    users_above = User.query.filter(User.coins > current_user.coins).count()
    rank = users_above + 1

    # Get percentile
    total_users = User.query.count()
    percentile = ((total_users - rank) / total_users * 100) if total_users > 0 else 0

    return (
        jsonify(
            {"rank": rank, "total_users": total_users, "percentile": round(percentile, 1), "coins": current_user.coins}
        ),
        200,
    )


# ========== Achievement Endpoints (Month 4) ==========


@app.route("/achievements", methods=["GET"])
def get_all_achievements():
    """
    Get all available achievements.

    Cached for 10 minutes since achievement definitions rarely change.
    """
    from .utils.models import Achievement

    # Try to get from cache
    cache_key = "all_achievements"
    result = cache.get(cache_key)

    if result is None:
        # Cache miss - query database
        achievements = Achievement.query.all()
        result = {"achievements": [a.to_dict() for a in achievements]}

        # Cache for 10 minutes
        cache.set(cache_key, result, timeout=600)

    return jsonify(result), 200


@app.route("/achievements/user", methods=["GET"])
@token_required
def get_user_achievements(current_user):
    """Get current user's unlocked achievements."""
    from .utils.models import UserAchievement

    user_achievements = (
        UserAchievement.query.filter_by(user_id=current_user.id).order_by(UserAchievement.unlocked_at.desc()).all()
    )

    return (
        jsonify({"achievements": [ua.to_dict() for ua in user_achievements], "total_unlocked": len(user_achievements)}),
        200,
    )


@app.route("/achievements/<int:achievement_id>/mark-seen", methods=["POST"])
@token_required
def mark_achievement_seen(current_user, achievement_id):
    """Mark an achievement as seen by the user."""
    from .utils.models import UserAchievement

    user_achievement = UserAchievement.query.filter_by(user_id=current_user.id, achievement_id=achievement_id).first()

    if not user_achievement:
        return jsonify({"message": "Achievement not found"}), 404

    from . import db

    user_achievement.seen = True
    db.session.commit()

    return jsonify({"message": "Achievement marked as seen"}), 200


@app.route("/achievements/progress", methods=["GET"])
@token_required
def get_achievement_progress(current_user):
    """Get user's progress towards all achievements."""
    from .utils.models import Achievement, Transaction
    from .utils.achievement_service import has_achievement

    # Get user stats
    stats = Transaction.get_user_statistics(current_user.id)

    progress = []

    # Calculate progress for each achievement
    all_achievements = Achievement.query.all()
    for achievement in all_achievements:
        unlocked = has_achievement(current_user.id, achievement.achievement_type)

        # Calculate progress percentage
        progress_pct = 0
        current_value = 0
        target_value = 0

        achievement_type = achievement.achievement_type.value

        if "total_spins" in achievement_type:
            current_value = stats["total_bets_count"]
            if "10" in achievement_type:
                target_value = 10
            elif "100" in achievement_type:
                target_value = 100
            elif "1000" in achievement_type:
                target_value = 1000

        elif "net_profit" in achievement_type:
            current_value = max(0, stats["net_profit"])
            if "1000" in achievement_type:
                target_value = 1000
            elif "5000" in achievement_type:
                target_value = 5000

        elif "master" in achievement_type:
            game_type = achievement_type.split("_")[0]
            for game_stat in stats["wins_by_game"]:
                if game_stat["game"] == game_type:
                    current_value = game_stat["count"]
                    target_value = 10
                    break

        if target_value > 0:
            progress_pct = min(100, (current_value / target_value) * 100)

        progress.append(
            {
                "achievement": achievement.to_dict(),
                "unlocked": unlocked,
                "progress_percentage": round(progress_pct, 1),
                "current_value": current_value,
                "target_value": target_value,
            }
        )

    # Sort: unlocked last, then by progress
    progress.sort(key=lambda x: (x["unlocked"], -x["progress_percentage"]))

    return (
        jsonify(
            {
                "progress": progress,
                "total_unlocked": sum(1 for p in progress if p["unlocked"]),
                "total_achievements": len(progress),
            }
        ),
        200,
    )


# ========== Notification Endpoints (Month 4) ==========


@app.route("/notifications", methods=["GET"])
@token_required
def get_notifications(current_user):
    """
    Get user notifications.

    Query parameters:
    - unread_only: true/false (default: false)
    - limit: Number of notifications (default: 20, max: 100)
    """
    from .utils.models import Notification

    unread_only = request.args.get("unread_only", "false").lower() == "true"
    limit = min(int(request.args.get("limit", 20)), 100)

    query = Notification.query.filter_by(user_id=current_user.id)

    if unread_only:
        query = query.filter_by(read=False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()

    return jsonify({"notifications": [n.to_dict() for n in notifications], "unread_count": unread_count}), 200


@app.route("/notifications/<int:notification_id>/read", methods=["POST"])
@token_required
def mark_notification_read(current_user, notification_id):
    """Mark a notification as read."""
    from .utils.models import Notification

    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()

    if not notification:
        return jsonify({"message": "Notification not found"}), 404

    from . import db

    notification.read = True
    db.session.commit()

    return jsonify({"message": "Notification marked as read"}), 200


@app.route("/notifications/mark-all-read", methods=["POST"])
@token_required
def mark_all_notifications_read(current_user):
    """Mark all notifications as read."""
    from .utils.models import Notification
    from . import db

    Notification.query.filter_by(user_id=current_user.id, read=False).update({"read": True})

    db.session.commit()

    return jsonify({"message": "All notifications marked as read"}), 200


# ========== User Profile Endpoints (Month 4) ==========


@app.route("/profile", methods=["GET"])
@token_required
def get_user_profile(current_user):
    """Get current user's complete profile with statistics."""
    from .utils.models import Transaction, UserAchievement, Achievement, TransactionType
    from datetime import timedelta, datetime

    # Get basic stats
    stats = Transaction.get_user_statistics(current_user.id)

    # Get achievements
    total_achievements = Achievement.query.count()
    unlocked_achievements = UserAchievement.query.filter_by(user_id=current_user.id).count()

    # Get activity stats (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    games_this_week = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.transaction_type == TransactionType.BET,
        Transaction.created_at >= week_ago,
    ).count()

    # Get leaderboard rank
    users_above = User.query.filter(User.coins > current_user.coins).count()
    rank = users_above + 1
    total_users = User.query.count()

    return (
        jsonify(
            {
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "email": current_user.email,
                    "coins": current_user.coins,
                },
                "statistics": stats,
                "achievements": {
                    "unlocked": unlocked_achievements,
                    "total": total_achievements,
                    "completion_percentage": round(
                        (unlocked_achievements / total_achievements * 100) if total_achievements > 0 else 0, 1
                    ),
                },
                "activity": {"games_this_week": games_this_week, "average_per_day": round(games_this_week / 7, 1)},
                "leaderboard": {
                    "rank": rank,
                    "total_users": total_users,
                    "percentile": round(((total_users - rank) / total_users * 100) if total_users > 0 else 0, 1),
                },
            }
        ),
        200,
    )


@app.route("/profile/<int:user_id>", methods=["GET"])
@token_required
def get_other_user_profile(current_user, user_id):
    """Get another user's public profile."""
    from .utils.models import Transaction, UserAchievement, Achievement

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Get public stats
    stats = Transaction.get_user_statistics(user.id)

    # Get achievements
    total_achievements = Achievement.query.count()
    unlocked_achievements = UserAchievement.query.filter_by(user_id=user.id).count()

    # Get leaderboard rank
    users_above = User.query.filter(User.coins > user.coins).count()
    rank = users_above + 1

    return (
        jsonify(
            {
                "user": {"id": user.id, "username": user.username, "coins": user.coins},
                "statistics": {
                    "total_bets_count": stats["total_bets_count"],
                    "total_wins_count": stats["total_wins_count"],
                    "net_profit": stats["net_profit"],
                },
                "achievements": {"unlocked": unlocked_achievements, "total": total_achievements},
                "leaderboard": {"rank": rank},
            }
        ),
        200,
    )


# ========== End Month 4 Endpoints ==========


@app.route("/spin", methods=["POST"])
@token_required
@limiter.limit("60 per minute")
def spin(spin_user):
    return cherryAction(spin_user)


@app.route("/redirect-blackjack")
@login_required
def redirect_to_blackjack():
    username = current_user.username
    token = session.get("token")
    if not token:
        token = generate_token(current_user.username)
        session["token"] = token
    return redirect(f"{app.config['BLACK_JACK_URL']}/?username={username}&token={token}")


@app.route("/blackjack/start", methods=["POST"])
@token_required
def start_blackjack_game(current_user):
    data = request.get_json()
    wager = data.get("wager")
    if wager is None:
        return jsonify({"message": "Wager is required"}), 400

    game_state, status_code = start_game(current_user, wager)
    logging.debug("Start Blackjack Game - Game State: %s", game_state["player_hand"])
    return jsonify(game_state), status_code


@app.route("/blackjack/action", methods=["POST"])
@token_required
def blackjack_action(current_user):
    data = request.get_json()
    action = data.get("action")
    if action is None:
        return jsonify({"message": "Action is required"}), 400

    result, status_code = player_action(current_user, action)
    logging.debug("Blackjack Action - Result: %s", result["player_hand"])
    return jsonify(result), status_code


@app.route("/redirect-roulette")
@login_required
def redirect_to_roulette():
    username = current_user.username
    token = session.get("token")
    if not token:
        token = generate_token(current_user.username)
        session["token"] = token
    return redirect(f"{app.config['ROULETTE_URL']}/?username={username}&token={token}")


@app.route("/roulette/action", methods=["POST"])
@token_required
def roulette_action(current_user):
    data = request.get_json()
    logging.debug(f"Roulette action data: {data}")
    result, status_code = rouletteAction(current_user, data)
    return jsonify(result), status_code


# Global error handlers
@app.errorhandler(404)
def not_found(error):
    logging.warning(f"404 error: {request.url}")
    return jsonify({"message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    from . import db

    db.session.rollback()
    logging.error(f"Internal error: {error}", exc_info=True)
    return jsonify({"message": "Internal server error"}), 500


@app.errorhandler(400)
def bad_request(error):
    logging.warning(f"Bad request: {error}")
    return jsonify({"message": "Bad request"}), 400


@app.errorhandler(401)
def unauthorized(error):
    logging.warning(f"Unauthorized access attempt: {error}")
    return jsonify({"message": "Unauthorized"}), 401

"""
WebSocket event handlers for real-time features (Month 5).

This module implements:
- Live leaderboard updates
- Real-time notifications
- Multiplayer room support
- Live chat between players
- Big win announcements
"""

from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect
from . import socketio, db, cache
from .utils.models import User, Notification, Transaction
from .utils.auth import decode_token
import structlog
from datetime import datetime, timedelta
from sqlalchemy import func, desc

log = structlog.get_logger()

# Store active users and their rooms
active_users = {}  # {sid: {user_id, username, rooms}}
chat_messages = {}  # {room_id: [messages]}
multiplayer_rooms = {}  # {room_id: {game_type, users, status}}


# ============================================================================
# Connection Management
# ============================================================================


@socketio.on("connect")
def handle_connect():
    """Handle new WebSocket connection"""
    log.info("socket_connect", sid=request.sid, remote_addr=request.remote_addr)
    emit("connected", {"status": "connected", "sid": request.sid, "timestamp": datetime.utcnow().isoformat()})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle WebSocket disconnection"""
    sid = request.sid

    if sid in active_users:
        user_data = active_users[sid]
        log.info("socket_disconnect", sid=sid, user_id=user_data.get("user_id"), username=user_data.get("username"))

        # Notify rooms that user left
        for room in user_data.get("rooms", []):
            emit("user_left", {"username": user_data["username"], "room": room}, room=room, skip_sid=sid)

        # Remove from active users
        del active_users[sid]
    else:
        log.info("socket_disconnect_anonymous", sid=sid)


@socketio.on("authenticate")
def handle_authenticate(data):
    """Authenticate WebSocket connection with JWT token"""
    token = data.get("token")

    if not token:
        log.warning("socket_auth_no_token", sid=request.sid)
        emit("error", {"message": "No token provided"})
        disconnect()
        return

    try:
        # Decode JWT token
        decoded = decode_token(token)
        user = User.query.filter_by(username=decoded["user_id"]).first()

        if not user:
            log.warning("socket_auth_user_not_found", username=decoded["user_id"])
            emit("error", {"message": "User not found"})
            disconnect()
            return

        # Store user info
        active_users[request.sid] = {
            "user_id": user.id,
            "username": user.username,
            "rooms": [],
            "authenticated_at": datetime.utcnow().isoformat(),
        }

        # Join user-specific room
        user_room = f"user_{user.id}"
        join_room(user_room)
        active_users[request.sid]["rooms"].append(user_room)

        log.info("socket_auth_success", sid=request.sid, user_id=user.id, username=user.username)

        emit("authenticated", {"status": "authenticated", "username": user.username, "user_id": user.id})

    except Exception as e:
        log.error("socket_auth_failed", sid=request.sid, error=str(e))
        emit("error", {"message": "Authentication failed"})
        disconnect()


@socketio.on("ping")
def handle_ping():
    """Respond to ping to keep connection alive"""
    emit("pong", {"timestamp": datetime.utcnow().isoformat()})


# ============================================================================
# Live Leaderboard
# ============================================================================


@socketio.on("join_leaderboard")
def handle_join_leaderboard(data=None):
    """Join leaderboard room for real-time updates"""
    if request.sid not in active_users:
        emit("error", {"message": "Not authenticated"})
        return

    metric = data.get("metric", "coins") if data else "coins"
    timeframe = data.get("timeframe", "all_time") if data else "all_time"

    room = f"leaderboard_{metric}_{timeframe}"
    join_room(room)

    if room not in active_users[request.sid]["rooms"]:
        active_users[request.sid]["rooms"].append(room)

    # Send current leaderboard
    leaderboard_data = get_leaderboard_data(metric, timeframe)

    log.info(
        "join_leaderboard",
        sid=request.sid,
        user_id=active_users[request.sid]["user_id"],
        metric=metric,
        timeframe=timeframe,
    )

    emit(
        "joined_leaderboard", {"room": room, "metric": metric, "timeframe": timeframe, "leaderboard": leaderboard_data}
    )


@socketio.on("leave_leaderboard")
def handle_leave_leaderboard(data):
    """Leave leaderboard room"""
    if request.sid not in active_users:
        return

    metric = data.get("metric", "coins")
    timeframe = data.get("timeframe", "all_time")
    room = f"leaderboard_{metric}_{timeframe}"

    leave_room(room)

    if room in active_users[request.sid]["rooms"]:
        active_users[request.sid]["rooms"].remove(room)

    emit("left_leaderboard", {"room": room})


def get_leaderboard_data(metric="coins", timeframe="all_time", limit=100):
    """Get leaderboard data with caching"""
    cache_key = f"leaderboard_{metric}_{timeframe}"

    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    # Calculate leaderboard
    query = db.session.query(User.id, User.username, User.coins)

    # Add metric-specific calculations
    if metric == "net_profit":
        # Calculate net profit from transactions
        query = db.session.query(
            User.id,
            User.username,
            User.coins,
            (
                func.coalesce(
                    func.sum(func.case((Transaction.transaction_type == "WIN", Transaction.amount), else_=0)), 0
                )
                - func.coalesce(
                    func.abs(func.sum(func.case((Transaction.transaction_type == "BET", Transaction.amount), else_=0))),
                    0,
                )
            ).label("net_profit"),
        ).outerjoin(Transaction, User.id == Transaction.user_id)

        # Apply timeframe filter
        if timeframe == "daily":
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.created_at >= today_start)
        elif timeframe == "weekly":
            week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.created_at >= week_start)

        query = query.group_by(User.id, User.username, User.coins).order_by(desc("net_profit"))

        results = query.limit(limit).all()
        leaderboard = [
            {"rank": i + 1, "user_id": r.id, "username": r.username, "coins": r.coins, "net_profit": int(r.net_profit)}
            for i, r in enumerate(results)
        ]

    elif metric == "total_wins":
        # Count total wins from transactions
        query = (
            db.session.query(User.id, User.username, User.coins, func.count(Transaction.id).label("total_wins"))
            .outerjoin(Transaction, User.id == Transaction.user_id)
            .filter(Transaction.transaction_type == "WIN")
        )

        # Apply timeframe filter
        if timeframe == "daily":
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.created_at >= today_start)
        elif timeframe == "weekly":
            week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Transaction.created_at >= week_start)

        query = query.group_by(User.id, User.username, User.coins).order_by(desc("total_wins"))

        results = query.limit(limit).all()
        leaderboard = [
            {"rank": i + 1, "user_id": r.id, "username": r.username, "coins": r.coins, "total_wins": r.total_wins}
            for i, r in enumerate(results)
        ]

    else:  # coins (default)
        query = query.order_by(desc(User.coins))
        results = query.limit(limit).all()
        leaderboard = [
            {"rank": i + 1, "user_id": r.id, "username": r.username, "coins": r.coins} for i, r in enumerate(results)
        ]

    # Cache for 1 minute
    cache.set(cache_key, leaderboard, timeout=60)

    return leaderboard


def broadcast_leaderboard_update(user, metric="coins", timeframe="all_time"):
    """Broadcast leaderboard update to all subscribers"""
    room = f"leaderboard_{metric}_{timeframe}"

    # Invalidate cache
    cache_key = f"leaderboard_{metric}_{timeframe}"
    cache.delete(cache_key)

    # Get updated leaderboard
    leaderboard_data = get_leaderboard_data(metric, timeframe)

    # Broadcast to room
    socketio.emit(
        "leaderboard_update",
        {
            "metric": metric,
            "timeframe": timeframe,
            "leaderboard": leaderboard_data,
            "updated_at": datetime.utcnow().isoformat(),
        },
        room=room,
    )

    log.info("leaderboard_update_broadcast", user_id=user.id, metric=metric, timeframe=timeframe)


# ============================================================================
# Real-Time Notifications
# ============================================================================


@socketio.on("subscribe_notifications")
def handle_subscribe_notifications():
    """Subscribe to real-time notifications"""
    if request.sid not in active_users:
        emit("error", {"message": "Not authenticated"})
        return

    user_id = active_users[request.sid]["user_id"]
    room = f"notifications_{user_id}"

    join_room(room)

    log.info("subscribe_notifications", sid=request.sid, user_id=user_id)

    # Send unread notification count
    unread_count = Notification.query.filter_by(user_id=user_id, read=False).count()

    emit("subscribed_notifications", {"status": "subscribed", "unread_count": unread_count})


def send_notification_to_user(user_id, notification_data):
    """Send notification to specific user via WebSocket"""
    room = f"notifications_{user_id}"

    socketio.emit("new_notification", notification_data, room=room)

    log.info("notification_sent", user_id=user_id, notification_type=notification_data.get("notification_type"))


# ============================================================================
# Big Win Announcements
# ============================================================================


@socketio.on("join_big_wins")
def handle_join_big_wins():
    """Join big wins announcement channel"""
    join_room("big_wins")

    if request.sid in active_users:
        log.info("join_big_wins", sid=request.sid, user_id=active_users[request.sid]["user_id"])

    emit("joined_big_wins", {"status": "joined"})


def broadcast_big_win(user, win_amount, game_type):
    """Broadcast big win to all connected users"""
    # Only broadcast if win is significant (> 500 coins)
    if win_amount < 500:
        return

    announcement = {
        "username": user.username,
        "amount": win_amount,
        "game_type": game_type,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Broadcast to big wins room
    socketio.emit("big_win_announcement", announcement, room="big_wins")

    # Also notify the user directly
    socketio.emit(
        "your_big_win",
        {"amount": win_amount, "message": f"Congratulations! You won {win_amount} coins! 🎉"},
        room=f"user_{user.id}",
    )

    log.info("big_win_broadcast", user_id=user.id, username=user.username, amount=win_amount, game_type=game_type)


# ============================================================================
# Multiplayer Rooms
# ============================================================================


@socketio.on("create_multiplayer_room")
def handle_create_multiplayer_room(data):
    """Create a multiplayer game room"""
    if request.sid not in active_users:
        emit("error", {"message": "Not authenticated"})
        return

    user_data = active_users[request.sid]
    game_type = data.get("game_type", "blackjack")
    max_players = data.get("max_players", 4)
    is_private = data.get("private", False)

    # Generate room ID
    import uuid

    room_id = f"mp_{game_type}_{str(uuid.uuid4())[:8]}"

    # Create room
    multiplayer_rooms[room_id] = {
        "id": room_id,
        "game_type": game_type,
        "host": user_data["username"],
        "host_id": user_data["user_id"],
        "players": [{"user_id": user_data["user_id"], "username": user_data["username"], "status": "ready"}],
        "max_players": max_players,
        "status": "waiting",  # waiting, playing, finished
        "private": is_private,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Join the room
    join_room(room_id)
    active_users[request.sid]["rooms"].append(room_id)

    log.info("multiplayer_room_created", room_id=room_id, game_type=game_type, host=user_data["username"])

    emit("room_created", {"room": multiplayer_rooms[room_id]})

    # Broadcast new room to lobby
    if not is_private:
        socketio.emit(
            "new_room_available",
            {
                "room_id": room_id,
                "game_type": game_type,
                "host": user_data["username"],
                "players": 1,
                "max_players": max_players,
            },
            room="multiplayer_lobby",
        )


@socketio.on("join_multiplayer_room")
def handle_join_multiplayer_room(data):
    """Join an existing multiplayer room"""
    if request.sid not in active_users:
        emit("error", {"message": "Not authenticated"})
        return

    user_data = active_users[request.sid]
    room_id = data.get("room_id")

    if room_id not in multiplayer_rooms:
        emit("error", {"message": "Room not found"})
        return

    room = multiplayer_rooms[room_id]

    # Check if room is full
    if len(room["players"]) >= room["max_players"]:
        emit("error", {"message": "Room is full"})
        return

    # Check if game already started
    if room["status"] != "waiting":
        emit("error", {"message": "Game already in progress"})
        return

    # Check if user already in room
    if any(p["user_id"] == user_data["user_id"] for p in room["players"]):
        emit("error", {"message": "Already in this room"})
        return

    # Add player to room
    room["players"].append({"user_id": user_data["user_id"], "username": user_data["username"], "status": "not_ready"})

    # Join the room
    join_room(room_id)
    active_users[request.sid]["rooms"].append(room_id)

    log.info("player_joined_room", room_id=room_id, user_id=user_data["user_id"], username=user_data["username"])

    # Notify all players in room
    socketio.emit("player_joined", {"username": user_data["username"], "players": room["players"]}, room=room_id)

    emit("joined_room", {"room": room})


@socketio.on("leave_multiplayer_room")
def handle_leave_multiplayer_room(data):
    """Leave a multiplayer room"""
    if request.sid not in active_users:
        return

    user_data = active_users[request.sid]
    room_id = data.get("room_id")

    if room_id not in multiplayer_rooms:
        return

    room = multiplayer_rooms[room_id]

    # Remove player from room
    room["players"] = [p for p in room["players"] if p["user_id"] != user_data["user_id"]]

    # Leave the room
    leave_room(room_id)
    if room_id in active_users[request.sid]["rooms"]:
        active_users[request.sid]["rooms"].remove(room_id)

    log.info("player_left_room", room_id=room_id, user_id=user_data["user_id"])

    # If room is empty, delete it
    if len(room["players"]) == 0:
        del multiplayer_rooms[room_id]
        socketio.emit("room_closed", {"room_id": room_id}, room="multiplayer_lobby")
    else:
        # Notify remaining players
        socketio.emit("player_left", {"username": user_data["username"], "players": room["players"]}, room=room_id)

        # If host left, assign new host
        if room["host_id"] == user_data["user_id"] and len(room["players"]) > 0:
            new_host = room["players"][0]
            room["host"] = new_host["username"]
            room["host_id"] = new_host["user_id"]
            socketio.emit("new_host", {"host": new_host["username"]}, room=room_id)

    emit("left_room", {"room_id": room_id})


@socketio.on("get_multiplayer_rooms")
def handle_get_multiplayer_rooms(data=None):
    """Get list of available multiplayer rooms"""
    game_type = data.get("game_type") if data else None

    # Filter rooms
    available_rooms = [
        {
            "room_id": room_id,
            "game_type": room["game_type"],
            "host": room["host"],
            "players": len(room["players"]),
            "max_players": room["max_players"],
            "status": room["status"],
        }
        for room_id, room in multiplayer_rooms.items()
        if not room["private"] and room["status"] == "waiting" and (game_type is None or room["game_type"] == game_type)
    ]

    emit("multiplayer_rooms_list", {"rooms": available_rooms})


@socketio.on("join_multiplayer_lobby")
def handle_join_multiplayer_lobby():
    """Join the multiplayer lobby to see available rooms"""
    join_room("multiplayer_lobby")

    if request.sid in active_users:
        log.info("join_multiplayer_lobby", sid=request.sid, user_id=active_users[request.sid]["user_id"])

    emit("joined_multiplayer_lobby", {"status": "joined"})


# ============================================================================
# Live Chat
# ============================================================================


@socketio.on("join_chat")
def handle_join_chat(data):
    """Join a chat room"""
    if request.sid not in active_users:
        emit("error", {"message": "Not authenticated"})
        return

    user_data = active_users[request.sid]
    chat_room = data.get("room", "global")

    # Join the chat room
    join_room(f"chat_{chat_room}")

    log.info("join_chat", sid=request.sid, user_id=user_data["user_id"], room=chat_room)

    # Initialize chat messages for room if needed
    if chat_room not in chat_messages:
        chat_messages[chat_room] = []

    # Send recent messages
    recent_messages = chat_messages[chat_room][-50:]  # Last 50 messages

    emit("joined_chat", {"room": chat_room, "recent_messages": recent_messages})

    # Notify others
    socketio.emit(
        "user_joined_chat",
        {"username": user_data["username"], "room": chat_room},
        room=f"chat_{chat_room}",
        skip_sid=request.sid,
    )


@socketio.on("send_chat_message")
def handle_chat_message(data):
    """Send a chat message"""
    if request.sid not in active_users:
        emit("error", {"message": "Not authenticated"})
        return

    user_data = active_users[request.sid]
    message_text = data.get("message", "").strip()
    chat_room = data.get("room", "global")

    if not message_text or len(message_text) > 500:
        emit("error", {"message": "Invalid message"})
        return

    # Create message
    message = {
        "id": len(chat_messages.get(chat_room, [])) + 1,
        "username": user_data["username"],
        "user_id": user_data["user_id"],
        "message": message_text,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Store message
    if chat_room not in chat_messages:
        chat_messages[chat_room] = []

    chat_messages[chat_room].append(message)

    # Keep only last 100 messages per room
    if len(chat_messages[chat_room]) > 100:
        chat_messages[chat_room] = chat_messages[chat_room][-100:]

    log.info("chat_message_sent", user_id=user_data["user_id"], room=chat_room, message_length=len(message_text))

    # Broadcast to room
    socketio.emit("chat_message", message, room=f"chat_{chat_room}")


@socketio.on("leave_chat")
def handle_leave_chat(data):
    """Leave a chat room"""
    if request.sid not in active_users:
        return

    user_data = active_users[request.sid]
    chat_room = data.get("room", "global")

    leave_room(f"chat_{chat_room}")

    log.info("leave_chat", sid=request.sid, user_id=user_data["user_id"], room=chat_room)

    # Notify others
    socketio.emit("user_left_chat", {"username": user_data["username"], "room": chat_room}, room=f"chat_{chat_room}")

    emit("left_chat", {"room": chat_room})


# ============================================================================
# Error Handling
# ============================================================================


@socketio.on_error()
def error_handler(e):
    """Handle WebSocket errors"""
    log.error("socket_error", sid=request.sid, error=str(e), error_type=type(e).__name__)
    emit("error", {"message": "An error occurred"})


@socketio.on_error_default
def default_error_handler(e):
    """Handle all uncaught WebSocket errors"""
    log.error("socket_error_default", sid=request.sid, error=str(e), error_type=type(e).__name__)
    emit("error", {"message": "An unexpected error occurred"})

# FastAPI Migration Guide

## Overview
The ImperioCasino backend has been successfully migrated from Flask to FastAPI. This document provides information about the migration and how to use the new API.

## What Changed

### Framework Migration
- **From**: Flask + Flask-Login + Flask-SQLAlchemy + Flask-WTF
- **To**: FastAPI + JWT Authentication + SQLAlchemy 2.0 + Pydantic

### Key Improvements
1. **Modern Async Support**: FastAPI provides native async/await support for better performance
2. **Automatic API Documentation**: Interactive docs at `/docs` (Swagger UI) and `/redoc` (ReDoc)
3. **Type Safety**: Pydantic models provide runtime validation and type checking
4. **Better Performance**: FastAPI is one of the fastest Python frameworks
5. **JWT Authentication**: Token-based auth instead of session-based (better for APIs)
6. **Standards-Based**: Built on OpenAPI and JSON Schema standards

## Running the Application

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

```bash
cd session_management

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env and set your SECRET_KEY

# Initialize database (if needed)
python -c "from imperioApp.database import engine, Base; from imperioApp.utils.models_fastapi import User, BlackjackGameState; Base.metadata.create_all(bind=engine)"
```

### Starting the Server

```bash
# Development mode (with auto-reload)
python run.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 5000 --workers 4
```

The server will start on `http://localhost:5000`

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc
- **OpenAPI JSON**: http://localhost:5000/openapi.json

## API Endpoints

### Authentication

#### Register New User
```bash
POST /api/signup
Content-Type: application/json

{
  "username": "player1",
  "email": "player1@example.com",
  "password": "securepassword"
}

Response: 201 Created
{
  "message": "User created successfully",
  "username": "player1"
}
```

#### Login
```bash
POST /api/login
Content-Type: application/json

{
  "username": "player1",
  "password": "securepassword"
}

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Verify Token
```bash
POST /api/verify-token
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "player1"
}

Response: 200 OK
{
  "message": "Token is valid"
}
```

### Coin Management

#### Get Coins
```bash
GET /getCoins
Authorization: Bearer <token>

Response: 200 OK
{
  "coins": 100
}
```

#### Update Coins
```bash
POST /updateCoins
Authorization: Bearer <token>
Content-Type: application/json

{
  "coins": 150
}

Response: 200 OK
{
  "message": "Coins updated successfully"
}
```

### Games

#### Cherry Charm (Spin)
```bash
POST /spin
Authorization: Bearer <token>
Content-Type: application/json

Response: 200 OK
{
  "stopSegments": [23, 27, 24],
  "totalCoins": 149
}
```

#### Blackjack - Start Game
```bash
POST /blackjack/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "wager": 10
}

Response: 200 OK
{
  "id": 1,
  "user_id": 1,
  "dealer_hand": [...],
  "player_hand": [...],
  "player_coins": 140,
  "current_wager": 10,
  "game_over": false,
  "message": "Game started",
  ...
}
```

#### Blackjack - Player Action
```bash
POST /blackjack/action
Authorization: Bearer <token>
Content-Type: application/json

{
  "action": "hit",  // or "stand", "double", "split"
  "game_id": 1
}

Response: 200 OK
{
  "dealer_hand": [...],
  "player_hand": [...],
  "game_over": false,
  ...
}
```

#### Roulette - Place Bet
```bash
POST /roulette/action
Authorization: Bearer <token>
Content-Type: application/json

{
  "bet": [
    {
      "amt": 10,
      "odds": 35,
      "numbers": [7]
    }
  ]
}

Response: 200 OK
{
  "winning_number": 7,
  "total_win": 350,
  "total_coins": 490,
  ...
}
```

### Health & Info

#### Health Check
```bash
GET /health

Response: 200 OK
{
  "status": "healthy"
}
```

#### API Info
```bash
GET /

Response: 200 OK
{
  "message": "ImperioCasino API",
  "version": "2.0.0",
  "docs": "/docs",
  "dashboard": "/dashboard"
}
```

## Authentication Flow

1. **Register**: Call `POST /api/signup` to create a new user
2. **Login**: Call `POST /api/login` to get a JWT access token
3. **Use Token**: Include the token in the `Authorization` header for all authenticated requests:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Example: Complete Flow

```bash
# 1. Create a user
curl -X POST http://localhost:5000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "email": "player1@example.com", "password": "pass123"}'

# 2. Login and get token
TOKEN=$(curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "player1", "password": "pass123"}' \
  | jq -r '.access_token')

# 3. Check coin balance
curl -X GET http://localhost:5000/getCoins \
  -H "Authorization: Bearer $TOKEN"

# 4. Play Cherry Charm
curl -X POST http://localhost:5000/spin \
  -H "Authorization: Bearer $TOKEN"

# 5. Start a blackjack game
curl -X POST http://localhost:5000/blackjack/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"wager": 10}'
```

## Configuration

Configure the application using environment variables in `.env`:

```bash
# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URI=sqlite:///app.db

# Game Frontend URLs
CHERRY_CHARM_URL=http://localhost:5173
BLACK_JACK_URL=http://localhost:5174
ROULETTE_URL=http://localhost:5175

# CORS Origins
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175

# Session Security
SESSION_COOKIE_SECURE=False  # Set to True in production with HTTPS

# Logging
LOG_LEVEL=INFO
```

## Backward Compatibility

The migration includes a compatibility layer that allows the existing game logic to work without modification:

- **Flask DB Compatibility**: `imperioApp/flask_compat.py` provides a Flask-like `db.session` interface
- **Model Compatibility**: `imperioApp/utils/models.py` re-exports FastAPI models for backward compatibility
- **Game Logic**: Blackjack, Roulette, and Cherry Charm game logic work unchanged

## Architecture

```
session_management/
├── main.py                          # FastAPI application entry point
├── run.py                           # Server startup script
├── requirements.txt                 # Python dependencies
└── imperioApp/
    ├── __init__.py                  # Package initialization
    ├── database.py                  # SQLAlchemy database setup
    ├── flask_compat.py              # Flask compatibility layer
    ├── api/                         # API route modules
    │   ├── auth.py                  # Authentication routes
    │   ├── coins.py                 # Coin management routes
    │   └── games.py                 # Game routes
    ├── game_logic/                  # Game implementations
    │   ├── blackjack.py
    │   ├── cherrycharm.py
    │   └── roulette.py
    └── utils/                       # Utilities
        ├── auth_fastapi.py          # JWT authentication
        ├── models_fastapi.py        # SQLAlchemy models
        ├── services_fastapi.py      # Database services
        └── config.py                # Configuration
```

## Testing

To test the API:

1. **Using Interactive Docs**: Navigate to http://localhost:5000/docs
2. **Using curl**: See examples above
3. **Using Python requests**:

```python
import requests

# Login
response = requests.post('http://localhost:5000/api/login', 
    json={'username': 'player1', 'password': 'pass123'})
token = response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:5000/getCoins', headers=headers)
print(response.json())
```

## Security Features

1. **JWT Authentication**: Secure token-based authentication
2. **Password Hashing**: Bcrypt hashing for passwords
3. **Security Headers**: X-Frame-Options, X-Content-Type-Options, CSP, etc.
4. **CORS Configuration**: Configurable CORS origins
5. **Rate Limiting**: Built-in rate limiting with slowapi

## Performance

FastAPI provides excellent performance:
- Built on Starlette (async framework)
- Pydantic for fast data validation
- Async/await support throughout
- Minimal overhead compared to Flask

## Troubleshooting

### Server won't start
- Check if port 5000 is already in use: `lsof -i :5000`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check environment variables are set correctly

### Database errors
- Ensure database is initialized
- Check DATABASE_URI in .env
- For SQLite, ensure write permissions on the database file

### Authentication issues
- Verify SECRET_KEY is set in .env
- Check token expiration (default: 12 hours)
- Ensure Authorization header format: `Bearer <token>`

## Migration Notes

- All Flask dependencies are kept in requirements.txt for backward compatibility
- The Flask app (__init__.py, routes.py) is replaced but kept as reference
- Database schema remains the same
- Existing users and data are preserved
- Frontend games should continue to work with updated API URLs

## Support

For issues or questions:
- Check the interactive API docs at `/docs`
- Review error messages in server logs
- Consult the FastAPI documentation: https://fastapi.tiangolo.com/

# FastAPI-Users Migration Guide

## Overview
The application has been migrated to use FastAPI-Users for authentication and async SQLite for the database.

## What Changed

### Authentication
- **Before**: Custom JWT implementation with python-jose
- **After**: FastAPI-Users with built-in JWT authentication

### Database
- **Before**: Synchronous SQLite with SQLAlchemy
- **After**: Asynchronous SQLite with aiosqlite and SQLAlchemy async

### User Model
- **Before**: Custom User model with integer ID
- **After**: FastAPI-Users User model with UUID primary key

## New Endpoints

### Authentication
```bash
# Register a new user
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "myusername"
}

# Login (returns JWT token)
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded
username=user@example.com&password=securepassword

# Logout
POST /auth/jwt/logout
Authorization: ******

# Request password reset
POST /auth/forgot-password
{
  "email": "user@example.com"
}

# Reset password
POST /auth/reset-password
{
  "token": "reset_token",
  "password": "newpassword"
}

# Request email verification
POST /auth/request-verify-token

# Verify email
POST /auth/verify
{
  "token": "verification_token"
}
```

### User Management
```bash
# Get current user
GET /users/me
Authorization: ******

# Update current user
PATCH /users/me
Authorization: ******
{
  "username": "newusername",
  "coins": 200
}

# Get user by ID
GET /users/{id}
Authorization: ******

# Update user by ID (superuser only)
PATCH /users/{id}
Authorization: ******

# Delete user by ID (superuser only)
DELETE /users/{id}
Authorization: ******
```

### Coins
```bash
# Get coins (same as before)
GET /getCoins
Authorization: ******

# Update coins (same as before)
POST /updateCoins
Authorization: ******
{
  "coins": 150
}
```

## Quick Start

### Install Dependencies
```bash
cd session_management
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the Server
```bash
python run.py
```

The server will start on `http://localhost:5000`

### Example Usage

#### Python
```python
import requests

# Register
response = requests.post('http://localhost:5000/auth/register',
    json={
        'email': 'player@example.com',
        'password': 'secure123',
        'username': 'player1'
    })
print("User created:", response.json())

# Login
response = requests.post('http://localhost:5000/auth/jwt/login',
    data={'username': 'player@example.com', 'password': 'secure123'})
token = response.json()['access_token']
print("Token:", token)

# Get coins
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:5000/getCoins', headers=headers)
print("Coins:", response.json())

# Update coins
response = requests.post('http://localhost:5000/updateCoins',
    json={'coins': 200},
    headers=headers)
print("Update:", response.json())
```

#### cURL
```bash
# Register
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"player@example.com","password":"secure123","username":"player1"}'

# Login
curl -X POST http://localhost:5000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=player@example.com&password=secure123"

# Get coins (replace TOKEN with actual token)
curl -X GET http://localhost:5000/getCoins \
  -H "Authorization: ******"
```

## Key Differences

### User ID Format
- **Before**: Integer ID (1, 2, 3, ...)
- **After**: UUID (e.g., "98b1a26a-8a71-4c7a-8199-3214792e7d52")

### Login Endpoint
- **Before**: `POST /api/login` with JSON body
- **After**: `POST /auth/jwt/login` with form data (application/x-www-form-urlencoded)

### Registration
- **Before**: `POST /api/signup`
- **After**: `POST /auth/register`

### Authentication Header
Same format: `Authorization: ******`

## Database Schema

### User Table
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,  -- UUID
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(64) UNIQUE NOT NULL,
    coins INTEGER NOT NULL DEFAULT 100
);
```

### Blackjack Game State Table
```sql
CREATE TABLE blackjack_game_state (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,  -- Foreign key to users.id
    ...
);
```

## Configuration

All configuration remains in `.env` file:

```bash
# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URI=sqlite:///app.db

# Game URLs
CHERRY_CHARM_URL=http://localhost:5173
BLACK_JACK_URL=http://localhost:5174
ROULETTE_URL=http://localhost:5175

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175

# Logging
LOG_LEVEL=INFO
```

## Benefits

1. **Built-in User Management**: Email verification, password reset, user CRUD operations
2. **Better Security**: FastAPI-Users follows security best practices
3. **Async Performance**: Async SQLite for better concurrent request handling
4. **Standard Compliance**: Uses FastAPI-Users standard patterns
5. **Cleaner Code**: Less custom authentication code to maintain
6. **No Flask Dependencies**: Fully FastAPI native

## Interactive Documentation

Visit `http://localhost:5000/docs` for interactive API documentation (Swagger UI) where you can test all endpoints.

## Migration from Old API

If you have existing code using the old API:

### Old Code
```python
# Login
response = requests.post('http://localhost:5000/api/login',
    json={'username': 'user1', 'password': 'pass123'})
```

### New Code
```python
# Login
response = requests.post('http://localhost:5000/auth/jwt/login',
    data={'username': 'user1@example.com', 'password': 'pass123'})
```

**Key changes:**
1. Endpoint changed from `/api/login` to `/auth/jwt/login`
2. Content-Type changed from JSON to form data
3. Username field now expects email address
4. Response format is the same: `{"access_token": "...", "token_type": "bearer"}`

## Troubleshooting

### "User not found" on login
- Make sure you're using the email address, not username, in the login request
- Check that the user was registered successfully

### "Invalid credentials"
- Verify the password is correct
- Check that the user account is active (`is_active=true`)

### Database errors
- Delete the old `app.db` file if migrating from the old schema
- The database will be automatically created on first run
- Check file permissions on the database file

## Support

For issues or questions:
- Check the interactive docs at `/docs`
- Review FastAPI-Users documentation: https://fastapi-users.github.io/fastapi-users/
- Check server logs in `logs/app.log`

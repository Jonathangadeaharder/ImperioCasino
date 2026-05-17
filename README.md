# ImperioCasino 🎰

A multi-game online casino platform featuring Blackjack, Roulette, and a 3D Slot Machine (Cherry-Charm). Built with Flask backend and multiple frontend technologies.

## 🎮 Games

- **Blackjack** - Classic card game with hit, stand, double down, and split
- **Roulette** - European roulette with multiple bet types
- **Cherry-Charm** - 3D slot machine with Three.js graphics

## 🏗️ Architecture

```
ImperioCasino/
├── session_management/      # Flask backend (Port 5000)
│   ├── imperioApp/          # Main application
│   │   ├── game_logic/      # Game implementations
│   │   ├── utils/           # Models, auth, services
│   │   └── routes.py        # API endpoints
│   └── migrate_passwords.py # Password migration utility
├── blackjack-master/        # Blackjack frontend (Port 5174)
├── roulette/                # Roulette frontend (Port 5175)
└── cherry-charm/            # 3D Slots frontend (Port 5173)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for Cherry-Charm)
- uv (Python package manager)
- pnpm (Node package manager)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd session_management

# Install dependencies
uv sync

# Configure environment
cp ../.env.example .env
# Edit .env and set your SECRET_KEY (see below)

# Initialize database
uv run flask db upgrade

# Run the backend server
uv run python run.py
```

The backend will run on `http://localhost:5000`

### 2. Generate Secret Key

```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env file:
# SECRET_KEY=<generated-key-here>
```

### 3. Migrate Existing Passwords (if applicable)

If you have existing users with plain text passwords:

```bash
cd session_management

# Dry run to see what would change
python migrate_passwords.py --dry-run

# Perform actual migration
python migrate_passwords.py

# Verify migration
python migrate_passwords.py --verify
```

### 4. Frontend Setup

#### Cherry-Charm (3D Slots)

```bash
cd cherry-charm

# Install dependencies
pnpm install

# Configure environment
cp .env.example .env
# Edit .env if needed

# Run development server
pnpm run dev
```

Runs on `http://localhost:5173`

#### Blackjack & Roulette

These use Flask to serve static files. Update config files if needed:

- Blackjack: Edit `blackjack-master/js/config.js`
- Roulette: Edit `roulette/assets/js/config.js`

```bash
# Run Blackjack
cd blackjack-master
python run.py

# Run Roulette
cd roulette
python run.py
```

## 🔒 Security Features

### Implemented Security

✅ **Password Hashing** - Bcrypt password hashing with Werkzeug
✅ **Environment-based Configuration** - No hardcoded secrets
✅ **CORS Protection** - Restricted to specific origins
✅ **Rate Limiting** - Prevent brute force attacks
✅ **Input Validation** - Sanitized and validated user inputs
✅ **Database Row Locking** - Prevent race conditions
✅ **Security Headers** - X-Frame-Options, CSP, HSTS, etc.
✅ **Comprehensive Logging** - Configurable log levels
✅ **Error Handling** - Global error handlers with rollback

See [SECURITY.md](SECURITY.md) for detailed security documentation.

## 📝 Environment Variables

### Backend (.env)

```bash
# Flask Configuration
FLASK_ENV=development              # development or production
SECRET_KEY=your-secret-key         # REQUIRED: Generate with secrets.token_hex(32)

# Database
DATABASE_URI=sqlite:///app.db      # Or PostgreSQL for production
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600

# Game Frontend URLs
CHERRY_CHARM_URL=http://localhost:5173
BLACK_JACK_URL=http://localhost:5174
ROULETTE_URL=http://localhost:5175

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:5175

# Session Security
SESSION_COOKIE_SECURE=False        # Set to True in production with HTTPS

# Logging
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Frontend (cherry-charm/.env)

```bash
VITE_API_URL=http://localhost:5000
VITE_PORT=5173
VITE_DEV_LOG=true
```

## 🎯 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup` | Register new user (3/hour limit) |
| POST | `/login` | User login (5/min limit) |
| GET | `/logout` | User logout |
| POST | `/verify-token` | Verify JWT token |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/getCoins` | Get user's coin balance |
| POST | `/updateCoins` | Update coin balance |

### Games

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/spin` | Spin slot machine (60/min limit) |
| POST | `/blackjack/start` | Start blackjack game |
| POST | `/blackjack/action` | Perform blackjack action |
| POST | `/roulette/action` | Place roulette bets |

## 🧪 Testing

```bash
cd session_management

# Run all tests
uv run pytest

# Run specific test file
uv run pytest imperioApp/tests/test_auth.py

# Run with coverage
uv run pytest --cov --cov-branch --cov-report=term-missing
```

## 📦 Dependencies

### Backend

- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Login 0.6.3
- Flask-Limiter 3.5.0
- PyJWT 2.8.0
- Werkzeug 3.0.1

See [requirements.txt](session_management/requirements.txt) for full list.

### Frontend (Cherry-Charm)

- React 18.2.0
- TypeScript 5.x
- Three.js 0.153.0
- React Three Fiber 8.13.4
- Zustand 4.3.8
- Vite 4.3.9

## 🛠️ Development

### Database Migrations

```bash
cd session_management

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

### Running in Development

```bash
# Terminal 1 - Backend
cd session_management
uv run python run.py

# Terminal 2 - Cherry-Charm
cd cherry-charm
pnpm run dev

# Terminal 3 - Blackjack (optional)
cd blackjack-master
uv run python run.py

# Terminal 4 - Roulette (optional)
cd roulette
uv run python run.py
```

## 🚀 Production Deployment

### Pre-Deployment Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Set `FLASK_ENV=production`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `LOG_LEVEL=WARNING` or `INFO`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set up HTTPS/TLS certificates
- [ ] Update all URLs to use HTTPS
- [ ] Configure CORS for production domains
- [ ] Set up database backups
- [ ] Configure Redis for rate limiting
- [ ] Run security scans
- [ ] Migrate existing user passwords

### Production Server Setup

1. **Use Production WSGI Server**
   ```bash
   uv pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 'session_management.run:app'
   ```

2. **Set up Nginx Reverse Proxy**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl;
       server_name yourdomain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Use PostgreSQL Database**
   ```bash
   # In .env
   DATABASE_URI=postgresql://user:password@localhost/imperiocasino
   ```

## 🐛 Troubleshooting

### Common Issues

**Issue**: `SECRET_KEY environment variable must be set`
**Solution**: Generate and set SECRET_KEY in .env file

**Issue**: Database migrations fail
**Solution**: Delete existing database and run `flask db upgrade`

**Issue**: CORS errors in browser
**Solution**: Check CORS_ORIGINS in .env matches frontend URLs

**Issue**: Rate limit errors
**Solution**: Adjust rate limits in `imperioApp/__init__.py`

**Issue**: Password login fails after migration
**Solution**: Run password migration script or reset user passwords

## 📄 License

[Add your license here]

## 👥 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For security issues, see [SECURITY.md](SECURITY.md)

For bugs and features, open an issue on GitHub

## 📚 Additional Documentation

- [SECURITY.md](SECURITY.md) - Security features and deployment guide
- [.env.example](.env.example) - Environment configuration template

---

**Version**: 2.0.0
**Last Updated**: 2025-11-18
**Status**: Ready for staging deployment (requires HTTPS for production)

# ImperioCasino Production Deployment Guide

**Version**: 2.0.0
**Date**: 2025-11-20
**Status**: Production-Ready (Month 1 Complete)

---

## Overview

This guide provides step-by-step instructions for deploying ImperioCasino to a production environment with Gunicorn, NGINX, PostgreSQL, and Redis.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [PostgreSQL Installation & Configuration](#postgresql-installation--configuration)
4. [Redis Installation & Configuration](#redis-installation--configuration)
5. [Application Deployment](#application-deployment)
6. [NGINX Configuration](#nginx-configuration)
7. [SSL/TLS Setup](#ssltls-setup)
8. [Systemd Service Configuration](#systemd-service-configuration)
9. [Database Migration](#database-migration)
10. [Testing & Verification](#testing--verification)
11. [Monitoring & Maintenance](#monitoring--maintenance)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Minimum (Small deployment, <100 concurrent users)**:
- 2 CPU cores
- 4GB RAM
- 50GB SSD storage
- 100 Mbps network

**Recommended (Medium deployment, 100-1000 concurrent users)**:
- 4 CPU cores
- 8GB RAM
- 100GB SSD storage
- 1 Gbps network

**Production (Large deployment, 1000+ concurrent users)**:
- 8+ CPU cores
- 16GB+ RAM
- 200GB+ SSD storage
- 1 Gbps network
- Load balancer

### Software Requirements

- Ubuntu 20.04+ or Debian 11+ (recommended) or CentOS 8+
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- NGINX 1.18+
- Git
- sudo access

---

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    build-essential \
    libpq-dev \
    certbot \
    python3-certbot-nginx
```

### 3. Create Application User

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash imperiocasino

# Add to www-data group for NGINX integration
sudo usermod -a -G www-data imperiocasino
```

### 4. Create Directory Structure

```bash
# Create application directory
sudo mkdir -p /var/www/imperiocasino
sudo chown imperiocasino:www-data /var/www/imperiocasino

# Create logs directory
sudo mkdir -p /var/log/imperiocasino
sudo chown imperiocasino:www-data /var/log/imperiocasino

# Create backup directory
sudo mkdir -p /var/backups/imperiocasino
sudo chown imperiocasino:www-data /var/backups/imperiocasino
```

---

## PostgreSQL Installation & Configuration

### 1. Initialize PostgreSQL

```bash
# PostgreSQL should start automatically
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE imperiocasino_prod;
CREATE USER imperio_user WITH PASSWORD 'YOUR_SECURE_PASSWORD_HERE';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE imperiocasino_prod TO imperio_user;

# Exit PostgreSQL
\q
```

### 3. Configure PostgreSQL for Production

Edit `/etc/postgresql/14/main/postgresql.conf`:

```ini
# Connections
max_connections = 100
superuser_reserved_connections = 3

# Memory
shared_buffers = 256MB          # 25% of RAM for small instances
effective_cache_size = 1GB      # 50-75% of RAM
maintenance_work_mem = 64MB
work_mem = 8MB

# Write Ahead Log
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB

# Query Planning
random_page_cost = 1.1          # Lower for SSD
effective_io_concurrency = 200  # Higher for SSD
default_statistics_target = 100

# Checkpoints
checkpoint_completion_target = 0.9

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_min_duration_statement = 1000  # Log slow queries (>1s)
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   imperiocasino_prod  imperio_user                        md5
host    imperiocasino_prod  imperio_user    127.0.0.1/32        md5
host    imperiocasino_prod  imperio_user    ::1/128             md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 4. Test Database Connection

```bash
psql -h localhost -U imperio_user -d imperiocasino_prod -c "SELECT 1;"
```

---

## Redis Installation & Configuration

### 1. Configure Redis

Edit `/etc/redis/redis.conf`:

```ini
# Bind to localhost only (security)
bind 127.0.0.1 ::1

# Set password
requirepass YOUR_REDIS_PASSWORD_HERE

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence (optional for rate limiting)
# Disable for better performance if data loss is acceptable
save ""

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Security
protected-mode yes
```

### 2. Start and Enable Redis

```bash
sudo systemctl enable redis-server
sudo systemctl restart redis-server
```

### 3. Test Redis Connection

```bash
redis-cli -a YOUR_REDIS_PASSWORD_HERE ping
# Should return: PONG
```

---

## Application Deployment

### 1. Clone Repository

```bash
# Switch to application user
sudo su - imperiocasino

# Clone repository
cd /var/www/imperiocasino
git clone https://github.com/Jonathangadeaharder/ImperioCasino.git .
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
cd session_management
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `/var/www/imperiocasino/.env`:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=YOUR_SECRET_KEY_HERE  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

# Database
DATABASE_URI=postgresql://imperio_user:YOUR_DB_PASSWORD@localhost/imperiocasino_prod
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=YOUR_REDIS_PASSWORD_HERE
REDIS_DB=0

# Game Frontend URLs (update with your actual domains)
CHERRY_CHARM_URL=https://slots.yourdomain.com
BLACK_JACK_URL=https://blackjack.yourdomain.com
ROULETTE_URL=https://roulette.yourdomain.com

# CORS Origins (comma-separated, no spaces)
CORS_ORIGINS=https://slots.yourdomain.com,https://blackjack.yourdomain.com,https://roulette.yourdomain.com

# Session Security
SESSION_COOKIE_SECURE=True

# Logging
LOG_LEVEL=INFO

# Gunicorn
GUNICORN_WORKERS=4
GUNICORN_LOG_LEVEL=info

# Optional: S3 Backups
# S3_BACKUP_BUCKET=your-backup-bucket

# Optional: Notifications
# DEPLOY_NOTIFICATION_URL=https://hooks.slack.com/...
# BACKUP_NOTIFICATION_URL=https://hooks.slack.com/...
```

**Important**: Secure the .env file:

```bash
chmod 600 /var/www/imperiocasino/.env
```

### 5. Generate Secret Key

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
# Copy the output and add to .env file
```

---

## NGINX Configuration

### 1. Copy NGINX Configuration

```bash
sudo cp /var/www/imperiocasino/deployment/nginx/imperiocasino.conf /etc/nginx/sites-available/
```

### 2. Update Configuration

Edit `/etc/nginx/sites-available/imperiocasino.conf` and replace:
- `api.imperiocasino.com` with your actual API domain
- `slots.imperiocasino.com` with your slots domain
- `blackjack.imperiocasino.com` with your blackjack domain
- `roulette.imperiocasino.com` with your roulette domain

### 3. Test NGINX Configuration

```bash
sudo nginx -t
```

---

## SSL/TLS Setup

### 1. Obtain SSL Certificates

```bash
# Stop NGINX temporarily
sudo systemctl stop nginx

# Obtain certificates for all domains
sudo certbot certonly --standalone -d api.yourdomain.com
sudo certbot certonly --standalone -d slots.yourdomain.com
sudo certbot certonly --standalone -d blackjack.yourdomain.com
sudo certbot certonly --standalone -d roulette.yourdomain.com

# Start NGINX
sudo systemctl start nginx
```

### 2. Enable Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Enable auto-renewal timer
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 3. Verify Certificates

```bash
# Check certificate expiration
sudo certbot certificates
```

---

## Systemd Service Configuration

### 1. Copy Systemd Service File

```bash
sudo cp /var/www/imperiocasino/deployment/systemd/imperiocasino.service /etc/systemd/system/
```

### 2. Update Service File

Edit `/etc/systemd/system/imperiocasino.service` and update paths if necessary.

### 3. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable imperiocasino

# Start service
sudo systemctl start imperiocasino

# Check status
sudo systemctl status imperiocasino
```

### 4. Enable NGINX

```bash
# Enable NGINX site
sudo ln -s /etc/nginx/sites-available/imperiocasino.conf /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart NGINX
sudo systemctl restart nginx
```

---

## Database Migration

### Option 1: Fresh Installation

If this is a new installation:

```bash
cd /var/www/imperiocasino/session_management
source /var/www/imperiocasino/venv/bin/activate

# Run migrations
flask db upgrade

# Verify
flask db current
```

### Option 2: Migrate from SQLite

If you have existing data in SQLite:

```bash
cd /var/www/imperiocasino
source venv/bin/activate

# Set environment variable
export DATABASE_URI=postgresql://imperio_user:PASSWORD@localhost/imperiocasino_prod

# Run migration script (dry run first)
python deployment/scripts/migrate_to_postgres.py --sqlite-db=session_management/app.db --dry-run

# Actual migration
python deployment/scripts/migrate_to_postgres.py --sqlite-db=session_management/app.db

# Verify migration
python deployment/scripts/migrate_to_postgres.py --verify-only
```

---

## Testing & Verification

### 1. Health Check

```bash
# Check health endpoint
curl https://api.yourdomain.com/health

# Expected output:
# {
#   "checks": {
#     "database": "ok",
#     "redis": "ok"
#   },
#   "status": "healthy"
# }
```

### 2. Service Status

```bash
# Check all services
sudo systemctl status imperiocasino
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis-server
```

### 3. Log Check

```bash
# Application logs
sudo journalctl -u imperiocasino -n 50 --no-pager

# NGINX logs
sudo tail -f /var/log/nginx/imperiocasino_access.log
sudo tail -f /var/log/nginx/imperiocasino_error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### 4. Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 1000 requests, 10 concurrent
ab -n 1000 -c 10 https://api.yourdomain.com/health
```

---

## Monitoring & Maintenance

### 1. Set Up Automated Backups

Add to crontab for imperiocasino user:

```bash
sudo crontab -e -u imperiocasino

# Add these lines:
# Backup database every day at 2 AM
0 2 * * * /var/www/imperiocasino/deployment/scripts/backup_database.sh

# Clean old logs weekly
0 3 * * 0 find /var/log/imperiocasino -name "*.log" -mtime +30 -delete
```

### 2. Log Rotation

Create `/etc/logrotate.d/imperiocasino`:

```
/var/log/imperiocasino/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 imperiocasino www-data
    sharedscripts
    postrotate
        systemctl reload imperiocasino > /dev/null 2>&1 || true
    endscript
}
```

### 3. Monitoring Endpoints

- **Health**: `https://api.yourdomain.com/health`
- **Liveness**: `https://api.yourdomain.com/health/live`
- **Readiness**: `https://api.yourdomain.com/health/ready`
- **Metrics**: `https://api.yourdomain.com/metrics`

### 4. Performance Monitoring

Install and configure monitoring tools:

```bash
# Install htop for server monitoring
sudo apt install htop

# Install pgAdmin for PostgreSQL monitoring (optional)
# Or use command line:
psql -U imperio_user -d imperiocasino_prod -c "
    SELECT pid, usename, state, query
    FROM pg_stat_activity
    WHERE state != 'idle'
    ORDER BY query_start;"
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u imperiocasino -n 100 --no-pager

# Check if port is in use
sudo netstat -tulpn | grep 5000

# Check file permissions
ls -la /var/www/imperiocasino

# Check environment variables
sudo -u imperiocasino bash -c 'source /var/www/imperiocasino/.env && env | grep FLASK'
```

### Database Connection Errors

```bash
# Test PostgreSQL connection
psql -h localhost -U imperio_user -d imperiocasino_prod

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Check connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

### Redis Connection Errors

```bash
# Test Redis
redis-cli -a YOUR_PASSWORD ping

# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

### NGINX 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status imperiocasino

# Check Gunicorn logs
sudo journalctl -u imperiocasino -n 50

# Check NGINX logs
sudo tail -f /var/log/nginx/imperiocasino_error.log

# Test backend directly
curl http://localhost:5000/health
```

### High Memory Usage

```bash
# Check memory usage
free -h

# Check process memory
ps aux --sort=-%mem | head -10

# Reduce Gunicorn workers if needed
# Edit /etc/systemd/system/imperiocasino.service
# Or set GUNICORN_WORKERS environment variable
```

### Slow Performance

```bash
# Check database slow queries
sudo -u postgres psql -d imperiocasino_prod -c "
    SELECT query, calls, total_time, mean_time
    FROM pg_stat_statements
    ORDER BY mean_time DESC
    LIMIT 10;"

# Enable query logging
# Edit /etc/postgresql/14/main/postgresql.conf
# Set: log_min_duration_statement = 1000

# Check NGINX connections
sudo netstat -an | grep :443 | wc -l

# Check system load
uptime
```

---

## Deployment Automation

### Automated Deployment

Use the deployment script for updates:

```bash
# Switch to application user
sudo su - imperiocasino

# Run deployment
cd /var/www/imperiocasino
./deployment/scripts/deploy.sh
```

### Manual Deployment Steps

If automation fails, manual steps:

```bash
# 1. Backup database
./deployment/scripts/backup_database.sh

# 2. Pull latest code
git pull origin main

# 3. Activate virtualenv
source venv/bin/activate

# 4. Install dependencies
cd session_management
pip install -r requirements.txt

# 5. Run migrations
flask db upgrade

# 6. Restart service
sudo systemctl restart imperiocasino

# 7. Reload NGINX
sudo systemctl reload nginx

# 8. Verify
curl https://api.yourdomain.com/health
```

---

## Security Checklist

Before going live, verify:

- [ ] SECRET_KEY is strong and unique (64+ characters)
- [ ] All passwords are strong and unique
- [ ] .env file has 600 permissions
- [ ] DATABASE_URI uses strong password
- [ ] REDIS_PASSWORD is set
- [ ] SESSION_COOKIE_SECURE=True
- [ ] SSL certificates are valid
- [ ] HTTPS redirect is working
- [ ] CORS_ORIGINS contains only your domains
- [ ] Firewall is configured (UFW or iptables)
- [ ] SSH key authentication enabled (password disabled)
- [ ] Regular backups are scheduled
- [ ] Monitoring is set up
- [ ] Log rotation is configured
- [ ] Rate limiting is active
- [ ] Security headers are present

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop service
sudo systemctl stop imperiocasino

# 2. Restore database from backup
./deployment/scripts/restore_database.sh /var/backups/imperiocasino/latest.sql.gz

# 3. Revert code
git reset --hard <previous-commit-hash>

# 4. Reinstall dependencies
source venv/bin/activate
pip install -r session_management/requirements.txt

# 5. Restart service
sudo systemctl start imperiocasino

# 6. Verify
curl https://api.yourdomain.com/health
```

---

## Additional Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Gunicorn Documentation**: https://docs.gunicorn.org/
- **NGINX Documentation**: https://nginx.org/en/docs/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Redis Documentation**: https://redis.io/documentation
- **Let's Encrypt**: https://letsencrypt.org/
- **ImperioCasino Repository**: https://github.com/Jonathangadeaharder/ImperioCasino

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u imperiocasino -n 100`
2. Review troubleshooting section
3. Check GitHub issues: https://github.com/Jonathangadeaharder/ImperioCasino/issues

---

**Document Version**: 1.0
**Last Updated**: 2025-11-20
**Deployment Status**: Production-Ready

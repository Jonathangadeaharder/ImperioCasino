#!/bin/bash
# ImperioCasino Deployment Script
#
# This script automates the deployment process for ImperioCasino.
# It handles code updates, dependency installation, database migrations, and service restarts.
#
# Usage:
#   ./deploy.sh [--skip-backup] [--skip-tests]

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_DIR="$PROJECT_ROOT/session_management"
VENV_DIR="$PROJECT_ROOT/venv"

# Parse arguments
SKIP_BACKUP=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-backup] [--skip-tests]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handler
handle_error() {
    log_error "Deployment failed at step: $1"
    log_error "Rolling back changes..."
    # Add rollback logic here if needed
    exit 1
}

log_info "========================================="
log_info "ImperioCasino Deployment Starting"
log_info "========================================="
log_info "Timestamp: $(date)"
log_info "Project root: $PROJECT_ROOT"

# Step 1: Backup database (unless skipped)
if [ "$SKIP_BACKUP" = false ]; then
    log_step "Creating database backup..."
    if [ -f "$SCRIPT_DIR/backup_database.sh" ]; then
        bash "$SCRIPT_DIR/backup_database.sh" || handle_error "Database backup"
    else
        log_warn "Backup script not found, skipping backup"
    fi
else
    log_warn "Skipping database backup (--skip-backup flag set)"
fi

# Step 2: Pull latest code
log_step "Pulling latest code from git..."
cd "$PROJECT_ROOT"
git fetch origin || handle_error "Git fetch"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Stash any local changes
if ! git diff-index --quiet HEAD --; then
    log_warn "Local changes detected, stashing..."
    git stash
fi

git pull origin "$CURRENT_BRANCH" || handle_error "Git pull"

# Step 3: Activate virtual environment
log_step "Activating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    log_warn "Virtual environment not found, creating..."
    python3 -m venv "$VENV_DIR" || handle_error "Create virtual environment"
fi

source "$VENV_DIR/bin/activate" || handle_error "Activate virtual environment"

# Step 4: Install/update dependencies
log_step "Installing/updating Python dependencies..."
cd "$APP_DIR"
pip install --upgrade pip
pip install -r requirements.txt || handle_error "Install dependencies"

# Step 5: Run database migrations
log_step "Running database migrations..."
flask db upgrade || handle_error "Database migrations"

# Step 6: Run tests (unless skipped)
if [ "$SKIP_TESTS" = false ]; then
    log_step "Running tests..."
    if command -v pytest &> /dev/null; then
        pytest || handle_error "Tests failed"
    elif [ -f "run_tests.sh" ]; then
        bash run_tests.sh || handle_error "Tests failed"
    else
        log_warn "No test runner found, skipping tests"
    fi
else
    log_warn "Skipping tests (--skip-tests flag set)"
fi

# Step 7: Collect static files (if applicable)
# log_step "Collecting static files..."
# python manage.py collectstatic --noinput || handle_error "Collect static"

# Step 8: Restart application service
log_step "Restarting application service..."
if systemctl is-active --quiet imperiocasino; then
    sudo systemctl restart imperiocasino || handle_error "Restart service"
    log_info "Service restarted successfully"
else
    log_warn "ImperioCasino service is not running, starting..."
    sudo systemctl start imperiocasino || handle_error "Start service"
fi

# Wait for service to be ready
log_info "Waiting for service to be ready..."
sleep 3

# Check if service is running
if systemctl is-active --quiet imperiocasino; then
    log_info "Service is running"
else
    log_error "Service failed to start!"
    sudo journalctl -u imperiocasino -n 50 --no-pager
    exit 1
fi

# Step 9: Reload NGINX
log_step "Reloading NGINX..."
sudo nginx -t || handle_error "NGINX config test"
sudo systemctl reload nginx || handle_error "NGINX reload"

# Step 10: Health check
log_step "Running health check..."
sleep 2

HEALTH_URL="${HEALTH_CHECK_URL:-http://localhost:5000/health}"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    log_info "Health check passed!"
else
    log_error "Health check failed! HTTP status: $HEALTH_RESPONSE"
    log_error "Check application logs:"
    log_error "  sudo journalctl -u imperiocasino -n 50"
    exit 1
fi

# Step 11: Cleanup
log_step "Cleaning up..."
find "$APP_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$APP_DIR" -type f -name "*.pyc" -delete 2>/dev/null || true

# Summary
log_info "========================================="
log_info "Deployment completed successfully!"
log_info "========================================="
log_info "Timestamp: $(date)"
log_info "Git commit: $(git rev-parse --short HEAD)"
log_info "Branch: $CURRENT_BRANCH"
log_info ""
log_info "Service status:"
systemctl status imperiocasino --no-pager -l || true
log_info ""
log_info "Recent logs:"
sudo journalctl -u imperiocasino -n 20 --no-pager || true

# Send notification (optional)
if [ ! -z "$DEPLOY_NOTIFICATION_URL" ]; then
    curl -X POST "$DEPLOY_NOTIFICATION_URL" \
         -H "Content-Type: application/json" \
         -d "{\"text\":\"ImperioCasino deployment completed successfully on $CURRENT_BRANCH\"}" \
         > /dev/null 2>&1 || true
fi

exit 0

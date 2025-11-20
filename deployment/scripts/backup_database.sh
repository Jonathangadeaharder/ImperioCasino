#!/bin/bash
# ImperioCasino Database Backup Script
#
# This script creates backups of the PostgreSQL database and uploads them to S3 (optional).
# Add to crontab for automated backups: 0 2 * * * /path/to/backup_database.sh
#
# Requirements:
# - PostgreSQL client tools (pg_dump)
# - AWS CLI (optional, for S3 uploads)
# - .env file with database credentials

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/imperiocasino}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/imperiocasino_backup_$DATE.sql"
RETENTION_DAYS=${RETENTION_DAYS:-30}

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if DATABASE_URI is set
if [ -z "$DATABASE_URI" ]; then
    log_error "DATABASE_URI environment variable is not set"
    exit 1
fi

# Parse DATABASE_URI
if [[ $DATABASE_URI =~ postgresql://([^:]+):([^@]+)@([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASS="${BASH_REMATCH[2]}"
    DB_HOST_PORT="${BASH_REMATCH[3]}"
    DB_NAME="${BASH_REMATCH[4]}"

    # Split host and port
    if [[ $DB_HOST_PORT =~ ([^:]+):([0-9]+) ]]; then
        DB_HOST="${BASH_REMATCH[1]}"
        DB_PORT="${BASH_REMATCH[2]}"
    else
        DB_HOST="$DB_HOST_PORT"
        DB_PORT="5432"
    fi
else
    log_error "Invalid DATABASE_URI format"
    exit 1
fi

log_info "Starting backup for database: $DB_NAME"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Set PostgreSQL password
export PGPASSWORD="$DB_PASS"

# Create backup
log_info "Creating backup: $BACKUP_FILE"
if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
           --format=plain \
           --no-owner \
           --no-acl \
           --verbose \
           > "$BACKUP_FILE" 2>&1; then
    log_info "Backup created successfully"
else
    log_error "Backup failed!"
    exit 1
fi

# Compress backup
log_info "Compressing backup..."
if gzip -f "$BACKUP_FILE"; then
    BACKUP_FILE="${BACKUP_FILE}.gz"
    log_info "Backup compressed: $BACKUP_FILE"

    # Get file size
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup size: $FILE_SIZE"
else
    log_error "Compression failed!"
    exit 1
fi

# Upload to S3 (optional)
if [ ! -z "$S3_BACKUP_BUCKET" ] && command -v aws &> /dev/null; then
    log_info "Uploading backup to S3: s3://$S3_BACKUP_BUCKET/"
    if aws s3 cp "$BACKUP_FILE" "s3://$S3_BACKUP_BUCKET/database/$(basename $BACKUP_FILE)"; then
        log_info "Backup uploaded to S3 successfully"
    else
        log_warn "Failed to upload backup to S3"
    fi
else
    log_info "Skipping S3 upload (S3_BACKUP_BUCKET not set or AWS CLI not available)"
fi

# Delete old backups (keep last N days)
log_info "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "imperiocasino_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
OLD_COUNT=$(find "$BACKUP_DIR" -name "imperiocasino_backup_*.sql.gz" | wc -l)
log_info "Remaining backups: $OLD_COUNT"

# Create a 'latest' symlink
ln -sf "$(basename $BACKUP_FILE)" "$BACKUP_DIR/latest.sql.gz"

# Unset password
unset PGPASSWORD

log_info "Backup completed successfully!"
log_info "Backup location: $BACKUP_FILE"

# Send notification (optional)
if [ ! -z "$BACKUP_NOTIFICATION_URL" ]; then
    curl -X POST "$BACKUP_NOTIFICATION_URL" \
         -H "Content-Type: application/json" \
         -d "{\"text\":\"Database backup completed: $BACKUP_FILE (size: $FILE_SIZE)\"}" \
         > /dev/null 2>&1 || true
fi

exit 0

#!/bin/bash
#
# Database backup script for ImperioCasino
#
# Usage:
#   ./backup_database.sh              # Full backup
#   ./backup_database.sh --restore    # Restore from latest backup
#   ./backup_database.sh --list       # List available backups
#   ./backup_database.sh --clean      # Clean old backups
#

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups/imperiocasino/database}"
DB_NAME="${DB_NAME:-imperiocasino_prod}"
DB_USER="${DB_USER:-imperio_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
RETENTION_DAYS=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_backup() {
    log_info "Starting database backup..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Generate filename with timestamp
    DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

    log_info "Backup file: $BACKUP_FILE"

    # Create SQL backup
    log_info "Creating SQL format backup..."
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"

    # Compress backup
    log_info "Compressing backup..."
    gzip -f "$BACKUP_FILE"

    # Verify backup
    if [ -f "$BACKUP_FILE.gz" ] && [ -s "$BACKUP_FILE.gz" ]; then
        SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
        log_info "✓ Backup created successfully: $SIZE"
    else
        log_error "Backup verification failed"
        exit 1
    fi

    log_info "Backup completed: $BACKUP_FILE.gz"
}

list_backups() {
    log_info "Available backups in $BACKUP_DIR:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ]; then
        log_warn "Backup directory does not exist"
        return
    fi

    BACKUPS=$(ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null || true)

    if [ -z "$BACKUPS" ]; then
        log_warn "No backups found"
        return
    fi

    for backup in $BACKUPS; do
        FILENAME=$(basename "$backup")
        SIZE=$(du -h "$backup" | cut -f1)
        echo "  $FILENAME ($SIZE)"
    done
}

clean_old_backups() {
    log_info "Cleaning backups older than $RETENTION_DAYS days..."

    if [ ! -d "$BACKUP_DIR" ]; then
        log_warn "Backup directory does not exist"
        return
    fi

    find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete

    log_info "Cleanup completed"
}

# Main script
case "${1:-backup}" in
    backup)
        create_backup
        ;;
    --list)
        list_backups
        ;;
    --clean)
        clean_old_backups
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo "  backup       Create a new backup (default)"
        echo "  --list       List available backups"
        echo "  --clean      Remove old backups"
        echo "  --help       Show this help message"
        ;;
    *)
        log_error "Unknown option: $1"
        exit 1
        ;;
esac

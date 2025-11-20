#!/bin/bash
# ImperioCasino Database Restore Script
#
# This script restores a PostgreSQL database from a backup file.
#
# Usage:
#   ./restore_database.sh /path/to/backup.sql.gz
#   ./restore_database.sh latest  # Restores the most recent backup

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/imperiocasino}"

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

# Check arguments
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <backup_file.sql.gz|latest>"
    exit 1
fi

BACKUP_FILE="$1"

# If 'latest' specified, use the latest backup
if [ "$BACKUP_FILE" == "latest" ]; then
    BACKUP_FILE="$BACKUP_DIR/latest.sql.gz"
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "No latest backup found at $BACKUP_FILE"
        exit 1
    fi
    log_info "Using latest backup: $BACKUP_FILE"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

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

# Confirm restore
log_warn "WARNING: This will DROP and RECREATE the database: $DB_NAME"
log_warn "Backup file: $BACKUP_FILE"
echo -n "Are you sure you want to continue? (yes/no): "
read CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log_info "Restore cancelled"
    exit 0
fi

# Set PostgreSQL password
export PGPASSWORD="$DB_PASS"

log_info "Starting database restore..."

# Drop existing database (if exists)
log_warn "Dropping existing database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" || {
    log_error "Failed to drop database"
    exit 1
}

# Create new database
log_info "Creating new database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" || {
    log_error "Failed to create database"
    exit 1
}

# Restore from backup
log_info "Restoring from backup..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" || {
        log_error "Failed to restore database"
        exit 1
    }
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE" || {
        log_error "Failed to restore database"
        exit 1
    }
fi

log_info "Database restored successfully!"

# Verify restore
log_info "Verifying restore..."
TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
log_info "Tables found: $TABLE_COUNT"

# Unset password
unset PGPASSWORD

log_info "Restore completed successfully!"
log_info "Database: $DB_NAME"
log_info "Tables: $TABLE_COUNT"

exit 0

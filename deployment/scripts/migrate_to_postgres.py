#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script migrates data from SQLite to PostgreSQL for ImperioCasino.
It preserves all user data, game states, and relationships.

Usage:
    python migrate_to_postgres.py --sqlite-db=/path/to/app.db --postgres-uri=postgresql://user:pass@localhost/dbname

    Or with environment variables:
    DATABASE_URI=postgresql://user:pass@localhost/dbname python migrate_to_postgres.py
"""

import sys
import argparse
import sqlite3
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_data(sqlite_path, postgres_uri, dry_run=False):
    """
    Migrate data from SQLite to PostgreSQL

    Args:
        sqlite_path: Path to SQLite database file
        postgres_uri: PostgreSQL connection URI
        dry_run: If True, don't actually write to PostgreSQL
    """
    logger.info(f"Starting migration from {sqlite_path} to PostgreSQL")

    if dry_run:
        logger.info("DRY RUN MODE - No data will be written to PostgreSQL")

    # Connect to both databases
    logger.info("Connecting to SQLite database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    logger.info("Connecting to PostgreSQL database...")
    pg_engine = create_engine(postgres_uri)
    pg_metadata = MetaData()
    pg_metadata.reflect(bind=pg_engine)

    Session = sessionmaker(bind=pg_engine)
    pg_session = Session()

    try:
        # Get list of tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]

        logger.info(f"Found {len(tables)} tables to migrate: {', '.join(tables)}")

        # Migrate each table
        total_rows = 0
        for table_name in tables:
            logger.info(f"Migrating table: {table_name}")

            # Get data from SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()

            if not rows:
                logger.info(f"  No data in table {table_name}, skipping...")
                continue

            logger.info(f"  Found {len(rows)} rows in {table_name}")

            if not dry_run:
                # Get SQLAlchemy table object
                if table_name not in pg_metadata.tables:
                    logger.error(f"  Table {table_name} does not exist in PostgreSQL!")
                    continue

                pg_table = pg_metadata.tables[table_name]

                # Convert rows to dictionaries
                columns = [col[0] for col in sqlite_cursor.description]
                data = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    data.append(row_dict)

                # Insert data
                try:
                    pg_engine.execute(pg_table.insert(), data)
                    logger.info(f"  Successfully migrated {len(data)} rows to {table_name}")
                    total_rows += len(data)
                except Exception as e:
                    logger.error(f"  Error migrating {table_name}: {e}")
                    raise
            else:
                logger.info(f"  [DRY RUN] Would migrate {len(rows)} rows")
                total_rows += len(rows)

        if not dry_run:
            pg_session.commit()
            logger.info(f"Migration completed successfully! Total rows migrated: {total_rows}")

            # Update sequences for PostgreSQL
            logger.info("Updating PostgreSQL sequences...")
            for table_name in tables:
                try:
                    pg_session.execute(f"""
                        SELECT setval(pg_get_serial_sequence('{table_name}', 'id'),
                                     COALESCE(MAX(id), 1))
                        FROM {table_name};
                    """)
                except Exception as e:
                    logger.warning(f"Could not update sequence for {table_name}: {e}")

            pg_session.commit()
            logger.info("Sequences updated successfully")
        else:
            logger.info(f"[DRY RUN] Would migrate {total_rows} total rows")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if not dry_run:
            pg_session.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_session.close()


def verify_migration(sqlite_path, postgres_uri):
    """
    Verify that migration was successful by comparing row counts
    """
    logger.info("Verifying migration...")

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()

    pg_engine = create_engine(postgres_uri)
    pg_conn = pg_engine.connect()

    try:
        # Get tables
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]

        all_match = True
        for table_name in tables:
            # Count rows in SQLite
            sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_count = sqlite_cursor.fetchone()[0]

            # Count rows in PostgreSQL
            result = pg_conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            pg_count = result.fetchone()[0]

            if sqlite_count == pg_count:
                logger.info(f"✓ {table_name}: {sqlite_count} rows match")
            else:
                logger.error(f"✗ {table_name}: SQLite has {sqlite_count} rows, PostgreSQL has {pg_count} rows")
                all_match = False

        if all_match:
            logger.info("✓ Migration verification successful! All row counts match.")
        else:
            logger.error("✗ Migration verification failed! Row counts do not match.")
            return False

        return True

    finally:
        sqlite_conn.close()
        pg_conn.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate ImperioCasino data from SQLite to PostgreSQL')
    parser.add_argument('--sqlite-db',
                       default='session_management/app.db',
                       help='Path to SQLite database file (default: session_management/app.db)')
    parser.add_argument('--postgres-uri',
                       help='PostgreSQL connection URI (e.g., postgresql://user:pass@localhost/dbname)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Perform a dry run without actually migrating data')
    parser.add_argument('--verify-only',
                       action='store_true',
                       help='Only verify an existing migration')

    args = parser.parse_args()

    # Get PostgreSQL URI from args or environment
    import os
    postgres_uri = args.postgres_uri or os.environ.get('DATABASE_URI')

    if not postgres_uri:
        logger.error("PostgreSQL URI not provided. Use --postgres-uri or set DATABASE_URI environment variable")
        sys.exit(1)

    if not postgres_uri.startswith('postgresql'):
        logger.error("Invalid PostgreSQL URI. Must start with 'postgresql://'")
        sys.exit(1)

    try:
        if args.verify_only:
            success = verify_migration(args.sqlite_db, postgres_uri)
            sys.exit(0 if success else 1)
        else:
            migrate_data(args.sqlite_db, postgres_uri, dry_run=args.dry_run)

            if not args.dry_run:
                logger.info("\nRunning verification...")
                verify_migration(args.sqlite_db, postgres_uri)

            logger.info("\nMigration complete!")
            logger.info("\nNext steps:")
            logger.info("1. Update your .env file to use the PostgreSQL URI")
            logger.info("2. Restart your application")
            logger.info("3. Test thoroughly before removing SQLite database")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

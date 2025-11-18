#!/usr/bin/env python
"""
Password Migration Script for ImperioCasino

This script migrates existing user passwords from plain text to hashed passwords.
This is necessary after implementing the password hashing security fix.

⚠️ WARNING: This script assumes you still have access to plain text passwords.
If passwords are already corrupted or hashed incorrectly, users will need to reset.

Usage:
    python migrate_passwords.py [--dry-run]

Options:
    --dry-run    Show what would be changed without making changes
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import imperioApp
sys.path.insert(0, str(Path(__file__).parent))

from imperioApp import app, db
from imperioApp.utils.models import User
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def is_already_hashed(password_str):
    """
    Check if a password is already hashed (bcrypt format).
    Bcrypt hashes start with $2b$ or $2a$ or $2y$
    """
    if not password_str:
        return False
    return password_str.startswith(('$2b$', '$2a$', '$2y$', 'pbkdf2:', 'scrypt:'))


def migrate_passwords(dry_run=False):
    """
    Migrate all user passwords from plain text to hashed format.

    Args:
        dry_run (bool): If True, only show what would be changed without saving
    """
    with app.app_context():
        users = User.query.all()

        if not users:
            logger.warning("No users found in database.")
            return

        logger.info(f"Found {len(users)} users in database")

        migrated_count = 0
        already_hashed_count = 0
        error_count = 0

        for user in users:
            try:
                if not user.password:
                    logger.warning(f"User {user.username} has no password set. Skipping.")
                    error_count += 1
                    continue

                if is_already_hashed(user.password):
                    logger.info(f"User {user.username} password is already hashed. Skipping.")
                    already_hashed_count += 1
                    continue

                # Password appears to be plain text
                plain_password = user.password

                if dry_run:
                    logger.info(f"[DRY RUN] Would hash password for user: {user.username}")
                    migrated_count += 1
                else:
                    # Hash the password using the model's method
                    user.set_password(plain_password)
                    logger.info(f"✓ Hashed password for user: {user.username}")
                    migrated_count += 1

            except Exception as e:
                logger.error(f"Error processing user {user.username}: {e}")
                error_count += 1

        # Commit changes if not dry run
        if not dry_run and migrated_count > 0:
            try:
                db.session.commit()
                logger.info(f"\n✓ Successfully committed {migrated_count} password hashes to database")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to commit changes: {e}")
                return

        # Summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total users:           {len(users)}")
        logger.info(f"Passwords migrated:    {migrated_count}")
        logger.info(f"Already hashed:        {already_hashed_count}")
        logger.info(f"Errors/Skipped:        {error_count}")
        logger.info("="*60)

        if dry_run and migrated_count > 0:
            logger.info("\n⚠️  This was a DRY RUN. No changes were saved.")
            logger.info("Run without --dry-run to apply changes.")


def verify_migration():
    """
    Verify that all users have hashed passwords.
    """
    with app.app_context():
        users = User.query.all()

        unhashed_count = 0
        for user in users:
            if user.password and not is_already_hashed(user.password):
                logger.warning(f"User {user.username} still has unhashed password!")
                unhashed_count += 1

        if unhashed_count == 0:
            logger.info("✓ All users have properly hashed passwords")
            return True
        else:
            logger.error(f"✗ {unhashed_count} users still have unhashed passwords")
            return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate user passwords from plain text to hashed')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be changed without making changes')
    parser.add_argument('--verify', action='store_true',
                        help='Verify that all passwords are hashed')

    args = parser.parse_args()

    logger.info("ImperioCasino Password Migration Tool")
    logger.info("="*60)

    if args.verify:
        logger.info("Verifying password hashes...\n")
        verify_migration()
    else:
        if args.dry_run:
            logger.info("Running in DRY RUN mode (no changes will be saved)\n")
        else:
            logger.warning("⚠️  WARNING: This will modify the database!")
            response = input("Continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Migration cancelled.")
                sys.exit(0)
            print()

        migrate_passwords(dry_run=args.dry_run)

        # Verify after migration if not dry run
        if not args.dry_run:
            print()
            logger.info("Verifying migration...")
            verify_migration()

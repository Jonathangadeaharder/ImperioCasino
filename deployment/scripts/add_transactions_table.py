#!/usr/bin/env python3
"""
Database migration script to add transactions table (Month 3).

This script creates the transactions table with proper indexes and enums.
It's safe to run multiple times (idempotent).

Usage:
    python deployment/scripts/add_transactions_table.py
    python deployment/scripts/add_transactions_table.py --rollback  # To remove table
"""

import sys
import os
import argparse

# Add parent directory to path to import imperioApp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'session_management'))

from imperioApp import app, db
from imperioApp.utils.models import Transaction, TransactionType, GameType
from sqlalchemy import inspect


def table_exists(table_name):
    """Check if a table exists in the database."""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()


def create_transactions_table():
    """Create the transactions table."""
    print("Starting migration: Adding transactions table...")

    with app.app_context():
        # Check if table already exists
        if table_exists('transactions'):
            print("✓ Transactions table already exists. Skipping creation.")
            return True

        try:
            # Create the table
            print("Creating transactions table...")
            Transaction.__table__.create(db.engine)

            # Verify table was created
            if table_exists('transactions'):
                print("✓ Transactions table created successfully!")

                # Show table structure
                inspector = inspect(db.engine)
                columns = inspector.get_columns('transactions')
                indexes = inspector.get_indexes('transactions')

                print("\nTable structure:")
                print("Columns:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")

                print("\nIndexes:")
                for index in indexes:
                    print(f"  - {index['name']}: {index['column_names']}")

                return True
            else:
                print("✗ Failed to create transactions table")
                return False

        except Exception as e:
            print(f"✗ Error creating transactions table: {e}")
            import traceback
            traceback.print_exc()
            return False


def rollback_transactions_table():
    """Remove the transactions table (rollback migration)."""
    print("Rolling back migration: Removing transactions table...")

    with app.app_context():
        if not table_exists('transactions'):
            print("✓ Transactions table does not exist. Nothing to rollback.")
            return True

        try:
            # Ask for confirmation
            response = input("Are you sure you want to delete the transactions table? This will delete ALL transaction data! (yes/no): ")
            if response.lower() != 'yes':
                print("Rollback cancelled.")
                return False

            # Drop the table
            print("Dropping transactions table...")
            Transaction.__table__.drop(db.engine)

            # Verify table was dropped
            if not table_exists('transactions'):
                print("✓ Transactions table dropped successfully!")
                return True
            else:
                print("✗ Failed to drop transactions table")
                return False

        except Exception as e:
            print(f"✗ Error dropping transactions table: {e}")
            import traceback
            traceback.print_exc()
            return False


def verify_migration():
    """Verify that the migration was successful."""
    print("\nVerifying migration...")

    with app.app_context():
        try:
            # Check table exists
            if not table_exists('transactions'):
                print("✗ Verification failed: transactions table does not exist")
                return False

            # Try to query the table
            count = Transaction.query.count()
            print(f"✓ Table is queryable. Current transaction count: {count}")

            # Test creating a transaction (if there's a test user)
            from imperioApp.utils.models import User
            test_user = User.query.first()

            if test_user:
                print("\nTesting transaction creation...")

                # Create a test transaction
                test_transaction = Transaction.create_transaction(
                    user=test_user,
                    transaction_type=TransactionType.BONUS,
                    amount=100,
                    game_type=GameType.NONE,
                    description="Migration test transaction"
                )
                db.session.commit()

                print(f"✓ Test transaction created: ID {test_transaction.id}")

                # Try to retrieve it
                retrieved = Transaction.query.get(test_transaction.id)
                if retrieved:
                    print("✓ Test transaction retrieved successfully")

                    # Convert to dict to test serialization
                    data = retrieved.to_dict()
                    print(f"✓ Serialization works: {data['description']}")

                    # Delete test transaction
                    db.session.delete(test_transaction)
                    db.session.commit()
                    print("✓ Test transaction deleted")

                print("\n✓ All verification checks passed!")
                return True
            else:
                print("⚠ No users in database to test with, but table structure is correct")
                return True

        except Exception as e:
            print(f"✗ Verification failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def show_status():
    """Show current migration status."""
    print("Checking migration status...")

    with app.app_context():
        if table_exists('transactions'):
            print("✓ Transactions table exists")

            # Get transaction count
            count = Transaction.query.count()
            print(f"  Total transactions: {count}")

            if count > 0:
                # Get transaction breakdown
                from sqlalchemy import func

                # By type
                by_type = db.session.query(
                    Transaction.transaction_type,
                    func.count(Transaction.id)
                ).group_by(Transaction.transaction_type).all()

                print("\n  Transactions by type:")
                for trans_type, count in by_type:
                    print(f"    {trans_type.value}: {count}")

                # By game
                by_game = db.session.query(
                    Transaction.game_type,
                    func.count(Transaction.id)
                ).group_by(Transaction.game_type).all()

                print("\n  Transactions by game:")
                for game_type, count in by_game:
                    if game_type:
                        print(f"    {game_type.value}: {count}")
        else:
            print("✗ Transactions table does NOT exist")
            print("  Run this script without --rollback to create it")


def main():
    parser = argparse.ArgumentParser(description='Add transactions table migration')
    parser.add_argument('--rollback', action='store_true',
                       help='Remove the transactions table')
    parser.add_argument('--status', action='store_true',
                       help='Show current migration status')
    parser.add_argument('--verify', action='store_true',
                       help='Verify migration was successful')

    args = parser.parse_args()

    print("=" * 80)
    print(" ImperioCasino - Transactions Table Migration (Month 3)")
    print("=" * 80)
    print()

    if args.status:
        show_status()
    elif args.verify:
        if verify_migration():
            sys.exit(0)
        else:
            sys.exit(1)
    elif args.rollback:
        if rollback_transactions_table():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Run migration
        if create_transactions_table():
            print()
            if verify_migration():
                print("\n" + "=" * 80)
                print(" Migration completed successfully!")
                print("=" * 80)
                sys.exit(0)
            else:
                print("\n" + "=" * 80)
                print(" Migration completed but verification failed")
                print("=" * 80)
                sys.exit(1)
        else:
            print("\n" + "=" * 80)
            print(" Migration failed!")
            print("=" * 80)
            sys.exit(1)


if __name__ == '__main__':
    main()

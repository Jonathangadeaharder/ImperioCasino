#!/usr/bin/env python3
"""
Database migration script to add engagement tables (Month 4).

This script creates:
- achievements table (stores 16 pre-defined achievements)
- user_achievements table (tracks which users unlocked which achievements)
- notifications table (stores user notifications)

It also initializes the 16 pre-defined achievements.
It's safe to run multiple times (idempotent).

Usage:
    python deployment/scripts/add_engagement_tables.py
    python deployment/scripts/add_engagement_tables.py --rollback  # To remove tables
    python deployment/scripts/add_engagement_tables.py --status    # Show current status
    python deployment/scripts/add_engagement_tables.py --verify    # Verify migration
"""

import sys
import os
import argparse

# Add parent directory to path to import imperioApp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'session_management'))

from imperioApp import app, db
from imperioApp.utils.models import (
    Achievement, UserAchievement, Notification,
    AchievementType, NotificationType
)
from imperioApp.utils.achievement_service import initialize_achievements
from sqlalchemy import inspect


def table_exists(table_name):
    """Check if a table exists in the database."""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()


def create_engagement_tables():
    """Create the engagement tables (achievements, user_achievements, notifications)."""
    print("Starting migration: Adding engagement tables...")

    with app.app_context():
        tables_created = []
        tables_skipped = []

        try:
            # Create achievements table
            if table_exists('achievements'):
                print("✓ Achievements table already exists. Skipping creation.")
                tables_skipped.append('achievements')
            else:
                print("Creating achievements table...")
                Achievement.__table__.create(db.engine)
                if table_exists('achievements'):
                    print("✓ Achievements table created successfully!")
                    tables_created.append('achievements')
                else:
                    print("✗ Failed to create achievements table")
                    return False

            # Create user_achievements table
            if table_exists('user_achievements'):
                print("✓ User achievements table already exists. Skipping creation.")
                tables_skipped.append('user_achievements')
            else:
                print("Creating user_achievements table...")
                UserAchievement.__table__.create(db.engine)
                if table_exists('user_achievements'):
                    print("✓ User achievements table created successfully!")
                    tables_created.append('user_achievements')
                else:
                    print("✗ Failed to create user_achievements table")
                    return False

            # Create notifications table
            if table_exists('notifications'):
                print("✓ Notifications table already exists. Skipping creation.")
                tables_skipped.append('notifications')
            else:
                print("Creating notifications table...")
                Notification.__table__.create(db.engine)
                if table_exists('notifications'):
                    print("✓ Notifications table created successfully!")
                    tables_created.append('notifications')
                else:
                    print("✗ Failed to create notifications table")
                    return False

            # Initialize achievements (adds 16 pre-defined achievements)
            if tables_created or not Achievement.query.first():
                print("\nInitializing achievements...")
                initialize_achievements()
                achievement_count = Achievement.query.count()
                print(f"✓ Achievements initialized! Total achievements: {achievement_count}")

            # Show table structures for created tables
            if tables_created:
                inspector = inspect(db.engine)
                for table_name in tables_created:
                    print(f"\n{table_name} structure:")
                    columns = inspector.get_columns(table_name)
                    print("Columns:")
                    for column in columns:
                        print(f"  - {column['name']}: {column['type']}")

                    indexes = inspector.get_indexes(table_name)
                    if indexes:
                        print("Indexes:")
                        for index in indexes:
                            print(f"  - {index['name']}: {index['column_names']}")

            return True

        except Exception as e:
            print(f"✗ Error creating engagement tables: {e}")
            import traceback
            traceback.print_exc()
            return False


def rollback_engagement_tables():
    """Remove the engagement tables (rollback migration)."""
    print("Rolling back migration: Removing engagement tables...")

    with app.app_context():
        tables_to_remove = ['user_achievements', 'notifications', 'achievements']
        existing_tables = [t for t in tables_to_remove if table_exists(t)]

        if not existing_tables:
            print("✓ No engagement tables exist. Nothing to rollback.")
            return True

        print(f"Tables to remove: {', '.join(existing_tables)}")

        try:
            # Ask for confirmation
            response = input("Are you sure you want to delete these tables? This will delete ALL engagement data! (yes/no): ")
            if response.lower() != 'yes':
                print("Rollback cancelled.")
                return False

            # Drop tables in correct order (reverse foreign key dependencies)
            if table_exists('user_achievements'):
                print("Dropping user_achievements table...")
                UserAchievement.__table__.drop(db.engine)
                print("✓ User achievements table dropped")

            if table_exists('notifications'):
                print("Dropping notifications table...")
                Notification.__table__.drop(db.engine)
                print("✓ Notifications table dropped")

            if table_exists('achievements'):
                print("Dropping achievements table...")
                Achievement.__table__.drop(db.engine)
                print("✓ Achievements table dropped")

            # Verify all tables were dropped
            remaining = [t for t in tables_to_remove if table_exists(t)]
            if not remaining:
                print("\n✓ All engagement tables dropped successfully!")
                return True
            else:
                print(f"\n✗ Failed to drop some tables: {', '.join(remaining)}")
                return False

        except Exception as e:
            print(f"✗ Error dropping engagement tables: {e}")
            import traceback
            traceback.print_exc()
            return False


def verify_migration():
    """Verify that the migration was successful."""
    print("\nVerifying migration...")

    with app.app_context():
        try:
            # Check all tables exist
            required_tables = ['achievements', 'user_achievements', 'notifications']
            for table in required_tables:
                if not table_exists(table):
                    print(f"✗ Verification failed: {table} table does not exist")
                    return False
                print(f"✓ {table} table exists")

            # Check achievements are initialized
            achievement_count = Achievement.query.count()
            if achievement_count < 16:
                print(f"⚠ Warning: Only {achievement_count} achievements found (expected 16)")
            else:
                print(f"✓ All {achievement_count} achievements initialized")

            # Test querying tables
            print("\nTesting table queries...")

            # Try to query user_achievements
            ua_count = UserAchievement.query.count()
            print(f"✓ User achievements table is queryable. Current count: {ua_count}")

            # Try to query notifications
            notif_count = Notification.query.count()
            print(f"✓ Notifications table is queryable. Current count: {notif_count}")

            # Test creating a notification (if there's a test user)
            from imperioApp.utils.models import User
            test_user = User.query.first()

            if test_user:
                print("\nTesting notification creation...")

                # Create a test notification
                test_notification = Notification.create_notification(
                    user=test_user,
                    notification_type=NotificationType.SYSTEM,
                    title="Migration Test",
                    message="This is a test notification from migration script",
                    icon="🔧"
                )
                db.session.commit()

                print(f"✓ Test notification created: ID {test_notification.id}")

                # Try to retrieve it
                retrieved = Notification.query.get(test_notification.id)
                if retrieved:
                    print("✓ Test notification retrieved successfully")

                    # Convert to dict to test serialization
                    data = retrieved.to_dict()
                    print(f"✓ Serialization works: {data['title']}")

                    # Delete test notification
                    db.session.delete(test_notification)
                    db.session.commit()
                    print("✓ Test notification deleted")

                # Test achievement unlocking
                print("\nTesting achievement system...")
                first_achievement = Achievement.query.filter_by(
                    achievement_type=AchievementType.FIRST_SPIN
                ).first()

                if first_achievement:
                    print(f"✓ Achievement found: {first_achievement.name}")
                    print(f"  Description: {first_achievement.description}")
                    print(f"  Reward: {first_achievement.reward_coins} coins")
                    print(f"  Icon: {first_achievement.icon}")

                print("\n✓ All verification checks passed!")
                return True
            else:
                print("⚠ No users in database to test with, but table structures are correct")
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
        tables = ['achievements', 'user_achievements', 'notifications']
        all_exist = True

        for table in tables:
            exists = table_exists(table)
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"{status}: {table}")

            if not exists:
                all_exist = False

        if all_exist:
            print("\n📊 Data Summary:")

            # Achievement stats
            achievement_count = Achievement.query.count()
            print(f"  Total achievements: {achievement_count}")

            if achievement_count > 0:
                # Count by type
                print("\n  Achievement types:")
                for achievement in Achievement.query.all():
                    print(f"    - {achievement.name} ({achievement.achievement_type.value}): {achievement.reward_coins} coins")

            # User achievement stats
            ua_count = UserAchievement.query.count()
            print(f"\n  Total user achievements unlocked: {ua_count}")

            if ua_count > 0:
                # Most unlocked achievements
                from sqlalchemy import func
                popular = db.session.query(
                    Achievement.name,
                    func.count(UserAchievement.id).label('unlock_count')
                ).join(UserAchievement).group_by(Achievement.id, Achievement.name).order_by(
                    func.count(UserAchievement.id).desc()
                ).limit(5).all()

                if popular:
                    print("\n  Most unlocked achievements:")
                    for name, count in popular:
                        print(f"    - {name}: {count} users")

            # Notification stats
            notif_count = Notification.query.count()
            unread_count = Notification.query.filter_by(read=False).count()
            print(f"\n  Total notifications: {notif_count}")
            print(f"  Unread notifications: {unread_count}")

            if notif_count > 0:
                # By type
                by_type = db.session.query(
                    Notification.notification_type,
                    func.count(Notification.id)
                ).group_by(Notification.notification_type).all()

                print("\n  Notifications by type:")
                for notif_type, count in by_type:
                    print(f"    {notif_type.value}: {count}")

        else:
            print("\n⚠ Some tables are missing. Run this script to create them:")
            print("  python deployment/scripts/add_engagement_tables.py")


def main():
    parser = argparse.ArgumentParser(description='Add engagement tables migration (Month 4)')
    parser.add_argument('--rollback', action='store_true',
                       help='Remove the engagement tables')
    parser.add_argument('--status', action='store_true',
                       help='Show current migration status')
    parser.add_argument('--verify', action='store_true',
                       help='Verify migration was successful')

    args = parser.parse_args()

    print("=" * 80)
    print(" ImperioCasino - Engagement Tables Migration (Month 4)")
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
        if rollback_engagement_tables():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Run migration
        if create_engagement_tables():
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

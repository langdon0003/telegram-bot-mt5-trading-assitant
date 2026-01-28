#!/usr/bin/env python3
"""
Migration: Add default_rr_ratio column to user_settings table
Run this script once to update existing database
"""

import sqlite3
import os

DB_PATH = "trading_bot.db"

def migrate():
    """Add default_rr_ratio column if it doesn't exist"""

    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found: {DB_PATH}")
        print("   Please run the bot first to create database")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'default_rr_ratio' in columns:
            print("✅ Column 'default_rr_ratio' already exists")
            conn.close()
            return True

        # Add the column
        print("📝 Adding 'default_rr_ratio' column to user_settings...")
        cursor.execute("""
            ALTER TABLE user_settings
            ADD COLUMN default_rr_ratio REAL DEFAULT 2.0
        """)

        # Update existing rows to have default value
        cursor.execute("""
            UPDATE user_settings
            SET default_rr_ratio = 2.0
            WHERE default_rr_ratio IS NULL
        """)

        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'default_rr_ratio' in columns:
            print("✅ Migration successful!")
            print("   Column 'default_rr_ratio' added with default value 2.0")

            # Show updated rows
            cursor.execute("SELECT COUNT(*) FROM user_settings")
            count = cursor.fetchone()[0]
            print(f"   Updated {count} existing user settings")

            conn.close()
            return True
        else:
            print("❌ Migration failed - column not added")
            conn.close()
            return False

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add default_rr_ratio to user_settings")
    print("=" * 60)

    success = migrate()

    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("You can now use /setrr command to configure R:R ratio")
        print("Default R:R ratio is set to 2.0 (2:1 reward to risk)")
    else:
        print("\n" + "=" * 60)
        print("❌ MIGRATION FAILED")
        print("=" * 60)
        exit(1)

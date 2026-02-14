"""
Migration: Create bookmarks table
Creates the bookmarks table for storing user's saved locations.
"""

import os
import sys

# Add parent directory to path to import database_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Create bookmarks table."""
    try:
        # Create bookmarks table
        cursor.execute("""
            CREATE TABLE bookmarks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                latitude DECIMAL(10, 8) NOT NULL,
                longitude DECIMAL(11, 8) NOT NULL,
                address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on user_id for faster lookups
        cursor.execute("""
            CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id)
        """)

        # Create unique constraint to prevent duplicate bookmarks
        cursor.execute("""
            CREATE UNIQUE INDEX idx_bookmarks_unique_location
            ON bookmarks(user_id, latitude, longitude)
        """)

        print("✅ Bookmarks table created successfully")
        print("   - Added user_id index for performance")
        print("   - Added unique constraint for location per user")

    except Exception as e:
        print(f"❌ Error creating bookmarks table: {e}")
        raise e


def down(cursor):
    """Drop bookmarks table (rollback function)."""
    try:
        # Drop table (indexes and constraints are dropped automatically)
        cursor.execute("DROP TABLE IF EXISTS bookmarks CASCADE")

        print("✅ Bookmarks table dropped successfully")

    except Exception as e:
        print(f"❌ Error dropping bookmarks table: {e}")
        raise e


if __name__ == "__main__":
    # Allow running migration directly for testing
    conn = get_db_connection()
    cursor = conn.cursor()

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        down(cursor)
    else:
        up(cursor)

    conn.commit()
    cursor.close()
    conn.close()

"""
Migration: Create route_bookmarks table
Creates the route_bookmarks table for storing user's saved routes.
"""

import os
import sys

# Add parent directory to path to import database_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Create route_bookmarks table."""
    try:
        # Create route_bookmarks table
        cursor.execute("""
            CREATE TABLE route_bookmarks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,

                start_name VARCHAR(255) NOT NULL,
                start_address TEXT,
                start_lat DECIMAL(10, 8) NOT NULL,
                start_lon DECIMAL(11, 8) NOT NULL,

                end_name VARCHAR(255) NOT NULL,
                end_address TEXT,
                end_lat DECIMAL(10, 8) NOT NULL,
                end_lon DECIMAL(11, 8) NOT NULL,

                notes TEXT,
                is_favorite BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on user_id for faster lookups
        cursor.execute("""
            CREATE INDEX idx_route_bookmarks_user_id ON route_bookmarks(user_id)
        """)

        # Create index on is_favorite for quick filtering
        cursor.execute("""
            CREATE INDEX idx_route_bookmarks_favorite ON route_bookmarks(user_id, is_favorite)
        """)

        print("✅ Route bookmarks table created successfully")
        print("   - Added user_id index for performance")
        print("   - Added favorite filter index")

    except Exception as e:
        print(f"❌ Error creating route_bookmarks table: {e}")
        raise e


def down(cursor):
    """Drop route_bookmarks table (rollback function)."""
    try:
        # Drop table (indexes and constraints are dropped automatically)
        cursor.execute("DROP TABLE IF EXISTS route_bookmarks CASCADE")

        print("✅ Route bookmarks table dropped successfully")

    except Exception as e:
        print(f"❌ Error dropping route_bookmarks table: {e}")
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

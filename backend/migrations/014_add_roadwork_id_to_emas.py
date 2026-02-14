"""
Migration 014: Add roadwork_id column to emas_incidents table
Links EMAS incidents to roadwork events when created together
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Add roadwork_id column to emas_incidents table"""
    try:
        print("Adding roadwork_id column to emas_incidents table...")

        # Add roadwork_id column with foreign key reference
        cursor.execute("""
            ALTER TABLE emas_incidents
            ADD COLUMN IF NOT EXISTS roadwork_id INTEGER REFERENCES roadwork_events(id) ON DELETE SET NULL;
        """)
        print("   Added roadwork_id column")

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_emas_incidents_roadwork_id
            ON emas_incidents(roadwork_id);
        """)
        print("   Created index on roadwork_id")

        print("Migration 014 completed successfully")

    except Exception as e:
        print(f"Migration 014 failed: {e}")
        raise e


def down(cursor):
    """Remove roadwork_id column (rollback migration)"""
    try:
        print("Rolling back migration 014...")

        cursor.execute("""
            DROP INDEX IF EXISTS idx_emas_incidents_roadwork_id;
        """)
        print("   Dropped index")

        cursor.execute("""
            ALTER TABLE emas_incidents
            DROP COLUMN IF EXISTS roadwork_id;
        """)
        print("   Dropped roadwork_id column")

        print("Migration 014 rollback completed")

    except Exception as e:
        print(f"Migration 014 rollback failed: {e}")
        raise e


if __name__ == "__main__":
    conn = get_db_connection()
    cursor = conn.cursor()

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        down(cursor)
    else:
        up(cursor)

    conn.commit()
    cursor.close()
    conn.close()

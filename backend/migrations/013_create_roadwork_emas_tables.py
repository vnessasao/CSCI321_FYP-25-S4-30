"""
Migration 013: Create tables for roadwork events and EMAS incidents
- roadwork_events: Government roadwork event management
- emas_incidents: EMAS incident tracking
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Create roadwork and EMAS tables"""
    try:
        print("Creating roadwork and EMAS tables...")

        # 1. Create roadwork_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roadwork_events (
                id SERIAL PRIMARY KEY,
                location VARCHAR(255) NOT NULL,
                description TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                is_emas BOOLEAN DEFAULT FALSE,
                status VARCHAR(50) DEFAULT 'active',
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   Created roadwork_events table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_roadwork_events_status
            ON roadwork_events(status);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_roadwork_events_dates
            ON roadwork_events(start_time, end_time);
        """)

        # 2. Create emas_incidents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emas_incidents (
                id SERIAL PRIMARY KEY,
                location VARCHAR(255) NOT NULL,
                description TEXT,
                incident_type VARCHAR(100),
                status VARCHAR(50) DEFAULT 'Active',
                latitude FLOAT,
                longitude FLOAT,
                reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cleared_at TIMESTAMP,
                cleared_by INTEGER REFERENCES users(id),
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   Created emas_incidents table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_emas_incidents_status
            ON emas_incidents(status);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_emas_incidents_reported
            ON emas_incidents(reported_at DESC);
        """)

        # Seed some sample EMAS incidents
        cursor.execute("""
            INSERT INTO emas_incidents (location, description, incident_type, status)
            VALUES
                ('PIE - Toa Payoh', 'Vehicle breakdown on PIE', 'Breakdown', 'Active'),
                ('AYE - Clementi', 'Minor accident reported', 'Accident', 'Active'),
                ('CTE - Ang Mo Kio', 'Debris on road cleared', 'Obstruction', 'Cleared')
            ON CONFLICT DO NOTHING;
        """)
        print("   Seeded sample EMAS incidents")

        print("Migration 013 completed successfully")

    except Exception as e:
        print(f"Migration 013 failed: {e}")
        raise e


def down(cursor):
    """Drop roadwork and EMAS tables (rollback migration)"""
    try:
        print("Rolling back migration 013...")

        cursor.execute("DROP TABLE IF EXISTS roadwork_events CASCADE;")
        print("   Dropped roadwork_events table")

        cursor.execute("DROP TABLE IF EXISTS emas_incidents CASCADE;")
        print("   Dropped emas_incidents table")

        print("Migration 013 rollback completed")

    except Exception as e:
        print(f"Migration 013 rollback failed: {e}")
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

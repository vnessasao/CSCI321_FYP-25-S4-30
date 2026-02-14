"""
Fix missing columns in existing tables.
This migration adds columns that were missing when tables were created
before the schema was updated.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def add_column_if_not_exists(cursor, table_name, column_name, column_definition):
    """Helper to safely add a column if it doesn't exist"""
    cursor.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = '{table_name}' AND column_name = '{column_name}'
            ) THEN
                ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition};
                RAISE NOTICE 'Added column {column_name} to {table_name}';
            END IF;
        END $$;
    """)


def run_migration():
    """Add missing columns to all tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("=" * 60)
        print("Migration 011: Fix Missing Columns")
        print("=" * 60)

        # ============================================
        # FIX system_logs TABLE
        # ============================================
        print("\n1. Fixing system_logs table...")

        system_logs_columns = [
            ("user_id", "INTEGER REFERENCES users(id)"),
            ("session_id", "UUID"),
            ("request_id", "VARCHAR(100)"),
            ("ip_address", "VARCHAR(45)"),
            ("is_flagged", "BOOLEAN DEFAULT FALSE"),
            ("flagged_by", "INTEGER REFERENCES users(id)"),
            ("flagged_at", "TIMESTAMP"),
            ("is_resolved", "BOOLEAN DEFAULT FALSE"),
            ("resolved_by", "INTEGER REFERENCES users(id)"),
            ("resolved_at", "TIMESTAMP"),
            ("resolution_notes", "TEXT"),
        ]

        for col_name, col_def in system_logs_columns:
            add_column_if_not_exists(cursor, 'system_logs', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX backups TABLE
        # ============================================
        print("\n2. Fixing backups table...")

        backups_columns = [
            ("file_path", "VARCHAR(500)"),
            ("file_size", "BIGINT"),
            ("backup_type", "VARCHAR(50) DEFAULT 'full'"),
            ("status", "VARCHAR(50) DEFAULT 'completed'"),
            ("tables_included", "TEXT[]"),
            ("created_by", "INTEGER REFERENCES users(id)"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("notes", "TEXT"),
            ("is_deleted", "BOOLEAN DEFAULT FALSE"),
            ("deleted_at", "TIMESTAMP"),
        ]

        for col_name, col_def in backups_columns:
            add_column_if_not_exists(cursor, 'backups', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX feedback TABLE
        # ============================================
        print("\n3. Fixing feedback table...")

        feedback_columns = [
            ("user_id", "INTEGER REFERENCES users(id)"),
            ("user_email", "VARCHAR(255)"),
            ("user_name", "VARCHAR(255)"),
            ("category", "VARCHAR(50)"),
            ("subject", "VARCHAR(255)"),
            ("message", "TEXT"),
            ("rating", "INTEGER CHECK (rating >= 1 AND rating <= 5)"),
            ("status", "VARCHAR(50) DEFAULT 'pending'"),
            ("is_broadcast", "BOOLEAN DEFAULT FALSE"),
            ("broadcast_message", "TEXT"),
            ("broadcast_at", "TIMESTAMP"),
            ("broadcast_by", "INTEGER REFERENCES users(id)"),
            ("admin_response", "TEXT"),
            ("responded_by", "INTEGER REFERENCES users(id)"),
            ("responded_at", "TIMESTAMP"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]

        for col_name, col_def in feedback_columns:
            add_column_if_not_exists(cursor, 'feedback', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX model_schedules TABLE
        # ============================================
        print("\n4. Fixing model_schedules table...")

        schedules_columns = [
            ("name", "VARCHAR(255)"),
            ("model_type", "VARCHAR(50)"),
            ("algorithm_id", "INTEGER REFERENCES algorithms(id)"),
            ("cron_expression", "VARCHAR(100)"),
            ("notification_email", "VARCHAR(255)"),
            ("parameters", "JSONB DEFAULT '{}'"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("last_run", "TIMESTAMP"),
            ("last_run_status", "VARCHAR(50)"),
            ("last_run_message", "TEXT"),
            ("next_run", "TIMESTAMP"),
            ("run_count", "INTEGER DEFAULT 0"),
            ("created_by", "INTEGER REFERENCES users(id)"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]

        for col_name, col_def in schedules_columns:
            add_column_if_not_exists(cursor, 'model_schedules', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX detected_anomalies TABLE
        # ============================================
        print("\n5. Fixing detected_anomalies table...")

        anomalies_columns = [
            ("road_node_id", "INTEGER"),
            ("road_name", "VARCHAR(255)"),
            ("anomaly_type", "VARCHAR(50)"),
            ("severity", "VARCHAR(20) DEFAULT 'medium'"),
            ("latitude", "FLOAT"),
            ("longitude", "FLOAT"),
            ("current_speed", "FLOAT"),
            ("expected_speed", "FLOAT"),
            ("deviation_percent", "FLOAT"),
            ("confidence_score", "FLOAT"),
            ("detected_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("detected_by_model", "VARCHAR(50)"),
            ("is_confirmed", "BOOLEAN DEFAULT FALSE"),
            ("confirmed_by", "INTEGER REFERENCES users(id)"),
            ("confirmed_at", "TIMESTAMP"),
            ("is_resolved", "BOOLEAN DEFAULT FALSE"),
            ("resolved_by", "INTEGER REFERENCES users(id)"),
            ("resolved_at", "TIMESTAMP"),
            ("resolution_notes", "TEXT"),
            ("session_id", "UUID"),
        ]

        for col_name, col_def in anomalies_columns:
            add_column_if_not_exists(cursor, 'detected_anomalies', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX permissions TABLE
        # ============================================
        print("\n6. Fixing permissions table...")

        permissions_columns = [
            ("display_name", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("category", "VARCHAR(50)"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("is_suspended", "BOOLEAN DEFAULT FALSE"),
            ("suspended_at", "TIMESTAMP"),
            ("suspended_by", "INTEGER"),
            ("suspended_reason", "TEXT"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]

        for col_name, col_def in permissions_columns:
            add_column_if_not_exists(cursor, 'permissions', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX algorithms TABLE
        # ============================================
        print("\n7. Fixing algorithms table...")

        algorithms_columns = [
            ("display_name", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("model_type", "VARCHAR(50)"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("suspended_at", "TIMESTAMP"),
            ("suspended_reason", "TEXT"),
            ("parameters", "JSONB DEFAULT '{}'"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ]

        for col_name, col_def in algorithms_columns:
            add_column_if_not_exists(cursor, 'algorithms', col_name, col_def)
            print(f"   - {col_name}: OK")

        # ============================================
        # FIX users TABLE
        # ============================================
        print("\n8. Fixing users table...")

        users_columns = [
            ("name", "VARCHAR(255)"),
            ("is_super_admin", "BOOLEAN DEFAULT FALSE"),
            ("last_login", "TIMESTAMP"),
            ("is_suspended", "BOOLEAN DEFAULT FALSE"),
            ("suspended_at", "TIMESTAMP"),
            ("suspended_reason", "TEXT"),
        ]

        for col_name, col_def in users_columns:
            add_column_if_not_exists(cursor, 'users', col_name, col_def)
            print(f"   - {col_name}: OK")

        conn.commit()
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

    except Exception as e:
        conn.rollback()
        print(f"\nError during migration: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    run_migration()

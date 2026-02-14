"""
Migration 009: Create permissions tables for role-based access control
- permissions: Available system permissions
- role_permissions: Mapping of roles to permissions
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Create permissions tables"""
    try:
        print("🔄 Creating permissions tables...")

        # 1. Create permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(255),
                description TEXT,
                category VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_at TIMESTAMP,
                suspended_by INTEGER,
                suspended_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ Created permissions table")

        # 2. Create role_permissions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id SERIAL PRIMARY KEY,
                role VARCHAR(50) NOT NULL,
                permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
                granted_by INTEGER,
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_at TIMESTAMP,
                suspended_reason TEXT,
                UNIQUE(role, permission_id)
            );
        """)
        print("   ✅ Created role_permissions table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_role_permissions_role
            ON role_permissions(role);
        """)

        # Seed default permissions
        cursor.execute("""
            INSERT INTO permissions (name, display_name, description, category)
            VALUES
                ('view_dashboard', 'View Dashboard', 'Access to view main dashboard', 'general'),
                ('view_traffic_map', 'View Traffic Map', 'Access to real-time traffic map', 'traffic'),
                ('view_predictions', 'View Predictions', 'Access to traffic predictions', 'traffic'),
                ('view_bottlenecks', 'View Bottlenecks', 'Access to bottleneck analysis', 'analysis'),
                ('run_models', 'Run Models', 'Execute traffic analysis models', 'analysis'),
                ('upload_data', 'Upload Data', 'Upload road network and GPS data', 'data'),
                ('view_historical', 'View Historical Trends', 'Access historical traffic data', 'analysis'),
                ('generate_reports', 'Generate Reports', 'Create and export reports', 'reports'),
                ('manage_users', 'Manage Users', 'Create, edit, and deactivate users', 'admin'),
                ('manage_algorithms', 'Manage Algorithms', 'Enable/disable traffic algorithms', 'admin'),
                ('manage_schedules', 'Manage Schedules', 'Create and manage scheduled runs', 'admin'),
                ('view_logs', 'View System Logs', 'Access system log viewer', 'admin'),
                ('manage_backups', 'Manage Backups', 'Create and restore backups', 'admin'),
                ('manage_permissions', 'Manage Permissions', 'Edit role permissions', 'admin'),
                ('view_feedback', 'View Feedback', 'Access user feedback', 'admin'),
                ('broadcast_feedback', 'Broadcast Feedback', 'Send system-wide alerts', 'admin'),
                ('report_incidents', 'Report Incidents', 'Submit incident reports', 'general'),
                ('save_bookmarks', 'Save Bookmarks', 'Save location and route bookmarks', 'general'),
                ('view_weather', 'View Weather Overlay', 'Access weather data overlay', 'traffic'),
                ('view_transport', 'View Transport Overlay', 'Access public transport overlay', 'traffic')
            ON CONFLICT (name) DO NOTHING;
        """)
        print("   ✅ Seeded default permissions")

        # Assign permissions to roles
        # Public role
        cursor.execute("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'public', id FROM permissions
            WHERE name IN ('view_dashboard', 'view_traffic_map', 'view_predictions',
                          'report_incidents', 'save_bookmarks')
            ON CONFLICT (role, permission_id) DO NOTHING;
        """)

        # Government role
        cursor.execute("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'government', id FROM permissions
            WHERE name IN ('view_dashboard', 'view_traffic_map', 'view_predictions',
                          'view_bottlenecks', 'run_models', 'upload_data', 'view_historical',
                          'generate_reports', 'manage_users', 'report_incidents',
                          'save_bookmarks', 'view_weather', 'view_transport')
            ON CONFLICT (role, permission_id) DO NOTHING;
        """)

        # Analyst role
        cursor.execute("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'analyst', id FROM permissions
            WHERE name IN ('view_dashboard', 'view_traffic_map', 'view_predictions',
                          'view_bottlenecks', 'run_models', 'upload_data', 'view_historical',
                          'generate_reports', 'manage_schedules', 'report_incidents',
                          'save_bookmarks')
            ON CONFLICT (role, permission_id) DO NOTHING;
        """)

        # Developer role (all permissions)
        cursor.execute("""
            INSERT INTO role_permissions (role, permission_id)
            SELECT 'developer', id FROM permissions
            ON CONFLICT (role, permission_id) DO NOTHING;
        """)

        print("   ✅ Assigned default permissions to roles")
        print("✅ Migration 009 completed successfully")

    except Exception as e:
        print(f"❌ Migration 009 failed: {e}")
        raise e


def down(cursor):
    """Drop permissions tables (rollback migration)"""
    try:
        print("🔄 Rolling back migration 009...")

        cursor.execute("DROP TABLE IF EXISTS role_permissions CASCADE;")
        print("   ✅ Dropped role_permissions table")

        cursor.execute("DROP TABLE IF EXISTS permissions CASCADE;")
        print("   ✅ Dropped permissions table")

        print("✅ Migration 009 rollback completed")

    except Exception as e:
        print(f"❌ Migration 009 rollback failed: {e}")
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

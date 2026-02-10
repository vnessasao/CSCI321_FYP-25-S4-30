"""
Quick fix script to add missing columns to existing tables.
Run this if migrations fail due to existing tables with missing columns.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection

def fix_tables():
    """Add missing columns to existing tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("🔧 Fixing existing tables...")

        # Fix algorithms table - add missing columns
        print("\n📦 Fixing algorithms table...")
        columns_to_add = [
            ("display_name", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("model_type", "VARCHAR(50)"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("suspended_at", "TIMESTAMP"),
            ("suspended_reason", "TEXT"),
            ("parameters", "JSONB DEFAULT '{}'"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]

        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='algorithms' AND column_name='{col_name}'
                        ) THEN
                            ALTER TABLE algorithms ADD COLUMN {col_name} {col_type};
                        END IF;
                    END $$;
                """)
                print(f"   ✅ Added/verified {col_name} column")
            except Exception as e:
                print(f"   ⚠️ {col_name}: {e}")

        # Add unique constraint on name column if it doesn't exist
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'algorithms_name_unique'
                ) THEN
                    ALTER TABLE algorithms ADD CONSTRAINT algorithms_name_unique UNIQUE (name);
                END IF;
            END $$;
        """)
        print("   ✅ Added/verified unique constraint on name column")

        # Insert default algorithms
        cursor.execute("""
            INSERT INTO algorithms (name, display_name, description, model_type, is_active)
            VALUES
                ('LIM', 'Linear Independent Cascade', 'Monte Carlo simulation with probabilistic spread for traffic jam prediction', 'spread_model', TRUE),
                ('LTM', 'Linear Threshold Model', 'Threshold-based activation model for congestion spread', 'spread_model', TRUE),
                ('SIR', 'Susceptible-Infected-Recovered', 'Epidemic model for traffic congestion with recovery', 'spread_model', TRUE),
                ('SIS', 'Susceptible-Infected-Susceptible', 'Epidemic model allowing re-infection for persistent congestion', 'spread_model', TRUE),
                ('GREEDY', 'Greedy Bottleneck Finder', 'Iterative selection algorithm for top-K bottleneck identification', 'optimization', TRUE)
            ON CONFLICT (name) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                model_type = EXCLUDED.model_type;
        """)
        print("   ✅ Seeded/updated default algorithms")

        # Fix permissions table - add missing columns
        print("\n📦 Fixing permissions table...")
        perm_columns = [
            ("display_name", "VARCHAR(255)"),
            ("description", "TEXT"),
            ("category", "VARCHAR(50)"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("is_suspended", "BOOLEAN DEFAULT FALSE"),
            ("suspended_at", "TIMESTAMP"),
            ("suspended_by", "INTEGER"),
            ("suspended_reason", "TEXT"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]

        for col_name, col_type in perm_columns:
            try:
                cursor.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='permissions' AND column_name='{col_name}'
                        ) THEN
                            ALTER TABLE permissions ADD COLUMN {col_name} {col_type};
                        END IF;
                    END $$;
                """)
                print(f"   ✅ Added/verified {col_name} column")
            except Exception as e:
                print(f"   ⚠️ {col_name}: {e}")

        # Add unique constraint on name column if it doesn't exist
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'permissions_name_unique'
                ) THEN
                    ALTER TABLE permissions ADD CONSTRAINT permissions_name_unique UNIQUE (name);
                END IF;
            END $$;
        """)
        print("   ✅ Added/verified unique constraint on name column")

        # Insert default permissions
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
            ON CONFLICT (name) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                category = EXCLUDED.category;
        """)
        print("   ✅ Seeded/updated default permissions")

        # Assign permissions to roles
        print("\n📦 Assigning permissions to roles...")

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

        print("   ✅ Assigned permissions to roles")

        # Create other missing tables
        print("\n📦 Creating other missing tables...")

        # model_schedules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_schedules (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                model_type VARCHAR(50) NOT NULL,
                algorithm_id INTEGER REFERENCES algorithms(id),
                cron_expression VARCHAR(100) NOT NULL,
                notification_email VARCHAR(255),
                parameters JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                last_run_status VARCHAR(50),
                last_run_message TEXT,
                next_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ Created/verified model_schedules table")

        # system_logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id SERIAL PRIMARY KEY,
                log_level VARCHAR(20) NOT NULL,
                source VARCHAR(100),
                message TEXT NOT NULL,
                details JSONB,
                user_id INTEGER REFERENCES users(id),
                session_id UUID,
                request_id VARCHAR(100),
                ip_address VARCHAR(45),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_flagged BOOLEAN DEFAULT FALSE,
                flagged_by INTEGER REFERENCES users(id),
                flagged_at TIMESTAMP,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_by INTEGER REFERENCES users(id),
                resolved_at TIMESTAMP,
                resolution_notes TEXT
            );
        """)
        print("   ✅ Created/verified system_logs table")

        # detected_anomalies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detected_anomalies (
                id SERIAL PRIMARY KEY,
                road_node_id INTEGER,
                road_name VARCHAR(255),
                anomaly_type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) DEFAULT 'medium',
                latitude FLOAT,
                longitude FLOAT,
                current_speed FLOAT,
                expected_speed FLOAT,
                deviation_percent FLOAT,
                confidence_score FLOAT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detected_by_model VARCHAR(50),
                is_confirmed BOOLEAN DEFAULT FALSE,
                confirmed_by INTEGER REFERENCES users(id),
                confirmed_at TIMESTAMP,
                is_resolved BOOLEAN DEFAULT FALSE,
                resolved_by INTEGER REFERENCES users(id),
                resolved_at TIMESTAMP,
                resolution_notes TEXT,
                session_id UUID
            );
        """)
        print("   ✅ Created/verified detected_anomalies table")

        # feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                user_email VARCHAR(255),
                user_name VARCHAR(255),
                category VARCHAR(50),
                subject VARCHAR(255),
                message TEXT NOT NULL,
                rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                status VARCHAR(50) DEFAULT 'pending',
                is_broadcast BOOLEAN DEFAULT FALSE,
                broadcast_message TEXT,
                broadcast_at TIMESTAMP,
                broadcast_by INTEGER REFERENCES users(id),
                admin_response TEXT,
                responded_by INTEGER REFERENCES users(id),
                responded_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ Created/verified feedback table")

        # backups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backups (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500),
                file_size BIGINT,
                backup_type VARCHAR(50) DEFAULT 'full',
                status VARCHAR(50) DEFAULT 'completed',
                tables_included TEXT[],
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                is_deleted BOOLEAN DEFAULT FALSE,
                deleted_at TIMESTAMP
            );
        """)
        print("   ✅ Created/verified backups table")

        conn.commit()
        print("\n✅ All tables fixed successfully!")
        print("\n📋 Super Admin Login:")
        print("   Email: admin@trafficsg.gov")
        print("   Password: SuperAdmin@2024")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    fix_tables()

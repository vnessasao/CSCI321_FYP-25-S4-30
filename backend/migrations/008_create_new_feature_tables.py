"""
Migration 008: Create tables for new features
- algorithms: Algorithm management and suspend/activate functionality
- model_schedules: Scheduled model runs
- system_logs: System log tracking
- detected_anomalies: Traffic anomaly detection
- feedback: User feedback with broadcast capability
- backups: Database backup history
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Create new feature tables"""
    try:
        print("🔄 Creating new feature tables...")

        # 1. Create algorithms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS algorithms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                display_name VARCHAR(255),
                description TEXT,
                model_type VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                suspended_at TIMESTAMP,
                suspended_reason TEXT,
                parameters JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("   ✅ Created algorithms table")

        # Seed default algorithms
        cursor.execute("""
            INSERT INTO algorithms (name, display_name, description, model_type, is_active)
            VALUES
                ('LIM', 'Linear Independent Cascade', 'Monte Carlo simulation with probabilistic spread for traffic jam prediction', 'spread_model', TRUE),
                ('LTM', 'Linear Threshold Model', 'Threshold-based activation model for congestion spread', 'spread_model', TRUE),
                ('SIR', 'Susceptible-Infected-Recovered', 'Epidemic model for traffic congestion with recovery', 'spread_model', TRUE),
                ('SIS', 'Susceptible-Infected-Susceptible', 'Epidemic model allowing re-infection for persistent congestion', 'spread_model', TRUE),
                ('GREEDY', 'Greedy Bottleneck Finder', 'Iterative selection algorithm for top-K bottleneck identification', 'optimization', TRUE)
            ON CONFLICT (name) DO NOTHING;
        """)
        print("   ✅ Seeded default algorithms")

        # 2. Create model_schedules table
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
        print("   ✅ Created model_schedules table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_schedules_active
            ON model_schedules(is_active);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_schedules_next_run
            ON model_schedules(next_run);
        """)

        # 3. Create system_logs table
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
        print("   ✅ Created system_logs table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp
            ON system_logs(timestamp DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_level
            ON system_logs(log_level);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_logs_flagged
            ON system_logs(is_flagged) WHERE is_flagged = TRUE;
        """)

        # 4. Create detected_anomalies table
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
        print("   ✅ Created detected_anomalies table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_anomalies_detected_at
            ON detected_anomalies(detected_at DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_anomalies_type
            ON detected_anomalies(anomaly_type);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_anomalies_unresolved
            ON detected_anomalies(is_resolved) WHERE is_resolved = FALSE;
        """)

        # 5. Create feedback table
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
        print("   ✅ Created feedback table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_status
            ON feedback(status);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_created_at
            ON feedback(created_at DESC);
        """)

        # 6. Create backups table
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
        print("   ✅ Created backups table")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_backups_created_at
            ON backups(created_at DESC);
        """)

        print("✅ Migration 008 completed successfully")

    except Exception as e:
        print(f"❌ Migration 008 failed: {e}")
        raise e


def down(cursor):
    """Drop new feature tables (rollback migration)"""
    try:
        print("🔄 Rolling back migration 008...")

        tables = [
            'backups',
            'feedback',
            'detected_anomalies',
            'system_logs',
            'model_schedules',
            'algorithms'
        ]

        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"   ✅ Dropped {table} table")

        print("✅ Migration 008 rollback completed")

    except Exception as e:
        print(f"❌ Migration 008 rollback failed: {e}")
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

"""
Migration 005: Create upload_sessions table and add session_id to related tables
This migration creates the infrastructure for tracking file upload sessions and preprocessing status.
"""

import sys
import os
import psycopg
import logging

# Add parent directory to path to import database_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import DatabaseConfig

logger = logging.getLogger(__name__)

def upgrade():
    """Create upload_sessions table and add session_id columns to existing tables"""
    conn = None
    cursor = None

    try:
        db_config = DatabaseConfig()
        conn = db_config.get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting migration 005: Create upload_sessions table")

        # Enable uuid-ossp extension if not already enabled
        cursor.execute("""
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """)

        # Create upload_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS upload_sessions (
                session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'pending',
                road_network_filename VARCHAR(255),
                gps_trajectories_filename VARCHAR(255),
                road_count INTEGER DEFAULT 0,
                gps_point_count INTEGER DEFAULT 0,
                preprocessing_started_at TIMESTAMP,
                preprocessing_completed_at TIMESTAMP,
                error_message TEXT,
                is_active BOOLEAN DEFAULT TRUE
            );
        """)
        logger.info("Created upload_sessions table")

        # Create indexes for upload_sessions
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_upload_sessions_status
            ON upload_sessions(status);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_upload_sessions_active
            ON upload_sessions(is_active);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_upload_sessions_created_at
            ON upload_sessions(created_at DESC);
        """)
        logger.info("Created indexes on upload_sessions table")

        # Add session_id column to road_nodes (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='road_nodes' AND column_name='session_id'
                ) THEN
                    ALTER TABLE road_nodes
                    ADD COLUMN session_id UUID REFERENCES upload_sessions(session_id);

                    CREATE INDEX idx_road_nodes_session_id ON road_nodes(session_id);
                END IF;
            END $$;
        """)
        logger.info("Added session_id column to road_nodes table")

        # Add session_id column to gps_trajectories (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='gps_trajectories' AND column_name='session_id'
                ) THEN
                    ALTER TABLE gps_trajectories
                    ADD COLUMN session_id UUID REFERENCES upload_sessions(session_id);

                    CREATE INDEX idx_gps_trajectories_session_id ON gps_trajectories(session_id);
                END IF;
            END $$;
        """)
        logger.info("Added session_id column to gps_trajectories table")

        # Add session_id column to congestion_states (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='congestion_states' AND column_name='session_id'
                ) THEN
                    ALTER TABLE congestion_states
                    ADD COLUMN session_id UUID REFERENCES upload_sessions(session_id);

                    CREATE INDEX idx_congestion_states_session_id ON congestion_states(session_id);
                END IF;
            END $$;
        """)
        logger.info("Added session_id column to congestion_states table")

        # Add session_id column to bottleneck_rankings (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='bottleneck_rankings' AND column_name='session_id'
                ) THEN
                    ALTER TABLE bottleneck_rankings
                    ADD COLUMN session_id UUID REFERENCES upload_sessions(session_id);

                    CREATE INDEX idx_bottleneck_rankings_session_id ON bottleneck_rankings(session_id);
                END IF;
            END $$;
        """)
        logger.info("Added session_id column to bottleneck_rankings table")

        # Add session_id column to influence_probabilities (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='influence_probabilities' AND column_name='session_id'
                ) THEN
                    ALTER TABLE influence_probabilities
                    ADD COLUMN session_id UUID REFERENCES upload_sessions(session_id);

                    CREATE INDEX idx_influence_probabilities_session_id ON influence_probabilities(session_id);
                END IF;
            END $$;
        """)
        logger.info("Added session_id column to influence_probabilities table")

        # Add session_id column to road_edges (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='road_edges' AND column_name='session_id'
                ) THEN
                    ALTER TABLE road_edges
                    ADD COLUMN session_id UUID REFERENCES upload_sessions(session_id);

                    CREATE INDEX idx_road_edges_session_id ON road_edges(session_id);
                END IF;
            END $$;
        """)
        logger.info("Added session_id column to road_edges table")

        conn.commit()
        logger.info("Migration 005 completed successfully")

        return {"success": True, "message": "Upload sessions migration completed"}

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration 005 failed: {str(e)}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def downgrade():
    """Remove upload_sessions table and session_id columns (rollback migration)"""
    conn = None
    cursor = None

    try:
        db_config = DatabaseConfig()
        conn = db_config.get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting migration 005 rollback")

        # Drop session_id columns from all tables
        tables = [
            'road_nodes',
            'gps_trajectories',
            'congestion_states',
            'bottleneck_rankings',
            'influence_probabilities',
            'road_edges'
        ]

        for table in tables:
            cursor.execute(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='{table}' AND column_name='session_id'
                    ) THEN
                        ALTER TABLE {table} DROP COLUMN session_id;
                    END IF;
                END $$;
            """)
            logger.info(f"Dropped session_id column from {table} table")

        # Drop upload_sessions table
        cursor.execute("DROP TABLE IF EXISTS upload_sessions CASCADE;")
        logger.info("Dropped upload_sessions table")

        conn.commit()
        logger.info("Migration 005 rollback completed successfully")

        return {"success": True, "message": "Upload sessions rollback completed"}

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration 005 rollback failed: {str(e)}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Run the migration
    logging.basicConfig(level=logging.INFO)
    print("Running migration 005: Create upload_sessions table...")
    result = upgrade()
    print(result["message"])

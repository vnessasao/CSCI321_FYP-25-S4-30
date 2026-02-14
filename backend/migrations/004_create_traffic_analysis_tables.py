"""
Migration 004: Create traffic analysis tables
Creates tables for road network, GPS trajectories, congestion states, and bottleneck analysis
"""

import sys
import os
import psycopg
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import DatabaseConfig

logger = logging.getLogger(__name__)

def upgrade():
    """Create traffic analysis tables"""
    conn = None
    cursor = None

    try:
        db_config = DatabaseConfig()
        conn = db_config.get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting migration 004: Create traffic analysis tables")

        # Enable PostGIS extension
        cursor.execute("""
            CREATE EXTENSION IF NOT EXISTS postgis;
        """)
        logger.info("Enabled PostGIS extension")

        # Create road_nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS road_nodes (
                id SERIAL PRIMARY KEY,
                road_id VARCHAR(255) UNIQUE NOT NULL,
                road_name VARCHAR(255),
                highway_type VARCHAR(50),
                length_meters FLOAT,
                geometry GEOMETRY(LINESTRING, 4326),
                free_flow_speed FLOAT DEFAULT 60,
                capacity INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created road_nodes table")

        # Create indexes for road_nodes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_road_nodes_road_id ON road_nodes(road_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_road_nodes_geometry ON road_nodes USING GIST(geometry);
        """)
        logger.info("Created indexes for road_nodes")

        # Create road_edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS road_edges (
                id SERIAL PRIMARY KEY,
                from_node_id INTEGER REFERENCES road_nodes(id),
                to_node_id INTEGER REFERENCES road_nodes(id),
                distance_meters FLOAT,
                is_directional BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created road_edges table")

        # Create indexes for road_edges
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_road_edges_from ON road_edges(from_node_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_road_edges_to ON road_edges(to_node_id);
        """)
        logger.info("Created indexes for road_edges")

        # Create gps_trajectories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gps_trajectories (
                id SERIAL PRIMARY KEY,
                vehicle_id VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                latitude FLOAT NOT NULL,
                longitude FLOAT NOT NULL,
                speed_kmh FLOAT,
                heading FLOAT,
                matched_road_node_id INTEGER REFERENCES road_nodes(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created gps_trajectories table")

        # Create indexes for gps_trajectories
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gps_vehicle_timestamp
            ON gps_trajectories(vehicle_id, timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gps_timestamp ON gps_trajectories(timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gps_location
            ON gps_trajectories USING GIST(ST_MakePoint(longitude, latitude));
        """)
        logger.info("Created indexes for gps_trajectories")

        # Create congestion_states table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS congestion_states (
                id SERIAL PRIMARY KEY,
                road_node_id INTEGER REFERENCES road_nodes(id),
                timestamp TIMESTAMP NOT NULL,
                speed_kmh FLOAT,
                flow_vehicles_per_min FLOAT,
                density_vehicles_per_km FLOAT,
                congestion_index FLOAT,
                congestion_state VARCHAR(20),
                speed_band VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created congestion_states table")

        # Create indexes for congestion_states
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_congestion_road_time
            ON congestion_states(road_node_id, timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_congestion_timestamp
            ON congestion_states(timestamp);
        """)
        logger.info("Created indexes for congestion_states")

        # Create influence_probabilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS influence_probabilities (
                id SERIAL PRIMARY KEY,
                from_road_node_id INTEGER REFERENCES road_nodes(id),
                to_road_node_id INTEGER REFERENCES road_nodes(id),
                time_horizon_minutes INTEGER NOT NULL,
                probability FLOAT NOT NULL,
                model_type VARCHAR(20) NOT NULL,
                confidence VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        logger.info("Created influence_probabilities table")

        # Create indexes for influence_probabilities
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_influence_from
            ON influence_probabilities(from_road_node_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_influence_to
            ON influence_probabilities(to_road_node_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_influence_horizon
            ON influence_probabilities(time_horizon_minutes);
        """)
        logger.info("Created indexes for influence_probabilities")

        # Create bottleneck_rankings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bottleneck_rankings (
                id SERIAL PRIMARY KEY,
                road_node_id INTEGER REFERENCES road_nodes(id),
                rank_position INTEGER NOT NULL,
                benefit_score FLOAT NOT NULL,
                affected_roads_count INTEGER,
                calculation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_horizon_minutes INTEGER
            );
        """)
        logger.info("Created bottleneck_rankings table")

        # Create indexes for bottleneck_rankings
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bottleneck_timestamp
            ON bottleneck_rankings(calculation_timestamp);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bottleneck_rank
            ON bottleneck_rankings(rank_position);
        """)
        logger.info("Created indexes for bottleneck_rankings")

        conn.commit()
        logger.info("Migration 004 completed successfully")

        print("✅ Migration 004 completed successfully!")
        print("Created tables:")
        print("  - road_nodes")
        print("  - road_edges")
        print("  - gps_trajectories")
        print("  - congestion_states")
        print("  - influence_probabilities")
        print("  - bottleneck_rankings")

        return {"success": True, "message": "Traffic analysis tables created"}

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration 004 failed: {str(e)}")
        print(f"❌ Migration 004 failed: {str(e)}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def downgrade():
    """Drop traffic analysis tables (rollback)"""
    conn = None
    cursor = None

    try:
        db_config = DatabaseConfig()
        conn = db_config.get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting migration 004 rollback")

        # Drop tables in reverse order (respecting foreign keys)
        tables = [
            'bottleneck_rankings',
            'influence_probabilities',
            'congestion_states',
            'gps_trajectories',
            'road_edges',
            'road_nodes'
        ]

        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            logger.info(f"Dropped {table} table")

        conn.commit()
        logger.info("Migration 004 rollback completed successfully")

        return {"success": True, "message": "Traffic analysis tables dropped"}

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration 004 rollback failed: {str(e)}")
        raise e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Run the migration
    logging.basicConfig(level=logging.INFO)
    print("Running migration 004: Create traffic analysis tables...")
    upgrade()

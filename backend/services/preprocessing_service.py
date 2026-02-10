"""
Preprocessing Service
Handles loading road networks, GPS trajectories, and building road connectivity graphs
"""

import json
import csv
import os
import logging
from database_config import DatabaseConfig
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class PreprocessingService:
    """Service for preprocessing road network and GPS trajectory data"""

    def __init__(self):
        self.db_config = DatabaseConfig()

    def get_db_connection(self):
        """Get database connection"""
        return self.db_config.get_db_connection()

    def load_road_network_from_geojson(self, session_id):
        """
        Load road network from GeoJSON file and insert into database

        Args:
            session_id: UUID of the upload session

        Returns:
            int: Number of roads loaded
        """
        conn = None
        cursor = None

        try:
            # Get file path
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'sessions',
                session_id,
                'roads.geojson'
            )

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Road network file not found: {file_path}")

            logger.info(f"Loading road network from {file_path}")

            # Load GeoJSON
            with open(file_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)

            features = geojson_data.get('features', [])
            logger.info(f"Found {len(features)} road features in GeoJSON")

            conn = self.get_db_connection()
            cursor = conn.cursor()

            road_count = 0

            for feature in features:
                try:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})

                    # Extract properties
                    road_id = properties.get('road_id') or properties.get('ROAD_ID') or properties.get('id')
                    road_name = properties.get('road_name') or properties.get('ROAD_NAME') or properties.get('name') or 'Unknown Road'
                    highway_type = properties.get('highway') or properties.get('HIGHWAY_TYPE') or 'road'

                    # Extract geometry
                    if geometry.get('type') == 'LineString':
                        coordinates = geometry.get('coordinates', [])

                        if len(coordinates) < 2:
                            logger.warning(f"Skipping road {road_id}: insufficient coordinates")
                            continue

                        # Calculate length from coordinates (rough estimate)
                        length_meters = self._calculate_linestring_length(coordinates)

                        # Build PostGIS LineString
                        # Format: LINESTRING(lon1 lat1, lon2 lat2, ...)
                        linestring_coords = ', '.join([f"{coord[0]} {coord[1]}" for coord in coordinates])
                        linestring_wkt = f"LINESTRING({linestring_coords})"

                        # Generate road_id if not provided
                        if not road_id:
                            road_id = f"road_{road_count + 1}"

                        # Insert road into database
                        cursor.execute("""
                            INSERT INTO road_nodes (
                                road_id, road_name, highway_type, length_meters,
                                geometry, session_id, free_flow_speed, capacity
                            )
                            VALUES (
                                %s, %s, %s, %s,
                                ST_GeomFromText(%s, 4326), %s, 60, 1000
                            )
                            ON CONFLICT (road_id) DO UPDATE
                            SET road_name = EXCLUDED.road_name,
                                highway_type = EXCLUDED.highway_type,
                                length_meters = EXCLUDED.length_meters,
                                geometry = EXCLUDED.geometry,
                                session_id = EXCLUDED.session_id
                        """, (road_id, road_name, highway_type, length_meters, linestring_wkt, session_id))

                        road_count += 1

                    else:
                        logger.warning(f"Skipping road: unsupported geometry type {geometry.get('type')}")

                except Exception as e:
                    logger.warning(f"Error processing road feature: {str(e)}")
                    continue

            conn.commit()
            logger.info(f"Successfully loaded {road_count} roads for session {session_id}")

            return road_count

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error loading road network: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _calculate_linestring_length(self, coordinates):
        """
        Calculate approximate length of linestring in meters using Haversine formula

        Args:
            coordinates: List of [lon, lat] pairs

        Returns:
            float: Length in meters
        """
        if len(coordinates) < 2:
            return 0.0

        total_length = 0.0

        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i][0], coordinates[i][1]
            lon2, lat2 = coordinates[i + 1][0], coordinates[i + 1][1]

            # Haversine formula
            R = 6371000  # Earth's radius in meters
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)

            a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            total_length += R * c

        return total_length

    def build_road_graph(self, session_id):
        """
        Build road connectivity graph by finding adjacent roads

        Args:
            session_id: UUID of the upload session
        """
        conn = None
        cursor = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            logger.info(f"Building road graph for session {session_id}")

            # Find adjacent roads using spatial proximity (within 50 meters)
            cursor.execute("""
                DELETE FROM road_edges WHERE session_id = %s
            """, (session_id,))

            cursor.execute("""
                INSERT INTO road_edges (from_node_id, to_node_id, distance_meters, is_directional, session_id)
                SELECT DISTINCT
                    r1.id as from_node_id,
                    r2.id as to_node_id,
                    ST_Distance(
                        ST_Transform(ST_EndPoint(r1.geometry), 3857),
                        ST_Transform(ST_StartPoint(r2.geometry), 3857)
                    ) as distance_meters,
                    TRUE as is_directional,
                    r1.session_id
                FROM road_nodes r1
                JOIN road_nodes r2 ON r1.id != r2.id AND r1.session_id = r2.session_id
                WHERE r1.session_id = %s
                  AND ST_DWithin(
                      ST_Transform(ST_EndPoint(r1.geometry), 3857),
                      ST_Transform(ST_StartPoint(r2.geometry), 3857),
                      50  -- 50 meters threshold
                  )
            """, (session_id,))

            edge_count = cursor.rowcount
            conn.commit()

            logger.info(f"Built road graph with {edge_count} edges for session {session_id}")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error building road graph: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def process_gps_trajectories(self, session_id):
        """
        Process GPS trajectories from CSV file

        Args:
            session_id: UUID of the upload session

        Returns:
            int: Number of GPS points processed
        """
        conn = None
        cursor = None

        try:
            # Get file path
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'data',
                'sessions',
                session_id,
                'gps_trajectories.csv'
            )

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"GPS trajectories file not found: {file_path}")

            logger.info(f"Processing GPS trajectories from {file_path}")

            # Read CSV file
            gps_points = []
            with open(file_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)

                for row in csv_reader:
                    try:
                        gps_point = {
                            'vehicle_id': row.get('vehicle_id') or row.get('VEHICLE_ID'),
                            'timestamp': row.get('timestamp') or row.get('TIMESTAMP'),
                            'latitude': float(row.get('latitude') or row.get('LATITUDE') or row.get('lat')),
                            'longitude': float(row.get('longitude') or row.get('LONGITUDE') or row.get('lon')),
                            'speed_kmh': float(row.get('speed') or row.get('SPEED') or row.get('speed_kmh') or 0),
                            'heading': float(row.get('heading') or row.get('HEADING') or 0)
                        }
                        gps_points.append(gps_point)
                    except Exception as e:
                        logger.warning(f"Skipping invalid GPS point: {str(e)}")
                        continue

            logger.info(f"Read {len(gps_points)} GPS points from CSV")

            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Batch insert GPS points
            gps_count = 0
            batch_size = 1000

            for i in range(0, len(gps_points), batch_size):
                batch = gps_points[i:i + batch_size]

                for gps_point in batch:
                    try:
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(gps_point['timestamp'].replace('Z', '+00:00'))

                        # Find nearest road for map matching
                        cursor.execute("""
                            SELECT id
                            FROM road_nodes
                            WHERE session_id = %s
                            ORDER BY ST_Distance(
                                geometry,
                                ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                            )
                            LIMIT 1
                        """, (session_id, gps_point['longitude'], gps_point['latitude']))

                        nearest_road = cursor.fetchone()
                        matched_road_id = nearest_road[0] if nearest_road else None

                        # Insert GPS point
                        cursor.execute("""
                            INSERT INTO gps_trajectories (
                                vehicle_id, timestamp, latitude, longitude,
                                speed_kmh, heading, matched_road_node_id, session_id
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            gps_point['vehicle_id'],
                            timestamp,
                            gps_point['latitude'],
                            gps_point['longitude'],
                            gps_point['speed_kmh'],
                            gps_point['heading'],
                            matched_road_id,
                            session_id
                        ))

                        gps_count += 1

                    except Exception as e:
                        logger.warning(f"Error inserting GPS point: {str(e)}")
                        continue

                conn.commit()
                logger.info(f"Inserted batch of GPS points (total: {gps_count})")

            logger.info(f"Successfully processed {gps_count} GPS points for session {session_id}")

            # Calculate congestion states from GPS data
            self._calculate_congestion_states(session_id, cursor, conn)

            return gps_count

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error processing GPS trajectories: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _calculate_congestion_states(self, session_id, cursor, conn):
        """
        Calculate congestion states from GPS trajectories

        Args:
            session_id: UUID of the upload session
            cursor: Database cursor
            conn: Database connection
        """
        try:
            logger.info(f"Calculating congestion states for session {session_id}")

            # Aggregate GPS data by road and time window (5-minute intervals)
            cursor.execute("""
                INSERT INTO congestion_states (
                    road_node_id, timestamp, speed_kmh, flow_vehicles_per_min,
                    density_vehicles_per_km, congestion_index, congestion_state, session_id
                )
                SELECT
                    matched_road_node_id as road_node_id,
                    DATE_TRUNC('minute', timestamp) +
                        INTERVAL '5 minute' * FLOOR(EXTRACT(MINUTE FROM timestamp) / 5) as time_window,
                    AVG(speed_kmh) as avg_speed,
                    COUNT(DISTINCT vehicle_id)::float / 5.0 as flow_rate,
                    COUNT(DISTINCT vehicle_id)::float / NULLIF(AVG(rn.length_meters), 0) * 1000 as density,
                    CASE
                        WHEN AVG(speed_kmh) = 0 THEN 1.0
                        WHEN rn.free_flow_speed = 0 THEN 0.5
                        ELSE GREATEST(0.0, LEAST(1.0, 1.0 - AVG(speed_kmh) / NULLIF(rn.free_flow_speed, 1)))
                    END as congestion_index,
                    CASE
                        WHEN AVG(speed_kmh) >= rn.free_flow_speed * 0.8 THEN 'free'
                        WHEN AVG(speed_kmh) >= rn.free_flow_speed * 0.5 THEN 'moderate'
                        WHEN AVG(speed_kmh) >= rn.free_flow_speed * 0.3 THEN 'heavy'
                        ELSE 'jammed'
                    END as congestion_state,
                    %s as session_id
                FROM gps_trajectories gps
                JOIN road_nodes rn ON gps.matched_road_node_id = rn.id
                WHERE gps.session_id = %s
                  AND matched_road_node_id IS NOT NULL
                GROUP BY matched_road_node_id, time_window, rn.free_flow_speed, rn.length_meters
            """, (session_id, session_id))

            congestion_count = cursor.rowcount
            conn.commit()

            logger.info(f"Calculated {congestion_count} congestion states for session {session_id}")

        except Exception as e:
            logger.error(f"Error calculating congestion states: {str(e)}")
            raise e

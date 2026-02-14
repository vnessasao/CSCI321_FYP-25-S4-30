"""
Historical Trends API for Traffic Analysis system.
Provides endpoints for viewing and analyzing historical traffic data.
Supports daily, weekly, monthly, and yearly aggregations with region filtering.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import sys
import os
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import token_required

trends_bp = Blueprint('trends', __name__)


def generate_demo_trends(timescale, date_from, date_to):
    """
    Generate realistic demo traffic trend data when no real data exists.
    Simulates Singapore traffic patterns with morning/evening peaks.
    """
    trends = []

    start_date = datetime.strptime(date_from, '%Y-%m-%d')
    end_date = datetime.strptime(date_to, '%Y-%m-%d')

    # Determine time delta based on timescale
    if timescale == 'hourly':
        delta = timedelta(hours=1)
        max_points = 48  # 2 days of hourly data
    elif timescale == 'daily':
        delta = timedelta(days=1)
        max_points = 60  # 2 months
    elif timescale == 'weekly':
        delta = timedelta(weeks=1)
        max_points = 26  # 6 months
    elif timescale == 'monthly':
        delta = timedelta(days=30)
        max_points = 24  # 2 years
    else:  # yearly
        delta = timedelta(days=365)
        max_points = 5

    current = start_date
    count = 0

    while current <= end_date and count < max_points:
        # Base congestion varies by hour/day
        hour = current.hour if timescale == 'hourly' else 12
        day_of_week = current.weekday()

        # Morning peak (7-9 AM) and evening peak (5-7 PM)
        if 7 <= hour <= 9:
            base_congestion = 0.65 + random.uniform(-0.1, 0.15)
        elif 17 <= hour <= 19:
            base_congestion = 0.70 + random.uniform(-0.1, 0.15)
        elif 12 <= hour <= 14:
            base_congestion = 0.45 + random.uniform(-0.1, 0.1)
        elif 0 <= hour <= 6:
            base_congestion = 0.15 + random.uniform(-0.05, 0.1)
        else:
            base_congestion = 0.35 + random.uniform(-0.1, 0.15)

        # Weekends have less congestion
        if day_of_week >= 5:
            base_congestion *= 0.7

        # Add some randomness
        base_congestion = max(0.05, min(0.95, base_congestion))

        # Calculate breakdown
        total_samples = random.randint(800, 1500)
        jammed_pct = base_congestion * 0.3 if base_congestion > 0.5 else base_congestion * 0.1
        heavy_pct = base_congestion * 0.4 if base_congestion > 0.4 else base_congestion * 0.2
        moderate_pct = 0.3 + random.uniform(-0.1, 0.1)
        free_pct = 1 - jammed_pct - heavy_pct - moderate_pct

        # Speed inversely related to congestion
        avg_speed = 60 - (base_congestion * 45) + random.uniform(-5, 5)
        avg_speed = max(10, min(70, avg_speed))

        trends.append({
            'timestamp': current.isoformat(),
            'avg_congestion': round(base_congestion, 3),
            'max_congestion': round(min(0.98, base_congestion + random.uniform(0.1, 0.25)), 3),
            'min_congestion': round(max(0.02, base_congestion - random.uniform(0.1, 0.2)), 3),
            'avg_speed': round(avg_speed, 1),
            'roads_count': random.randint(150, 250),
            'sample_count': total_samples,
            'congestion_breakdown': {
                'jammed': int(total_samples * jammed_pct),
                'heavy': int(total_samples * heavy_pct),
                'moderate': int(total_samples * moderate_pct),
                'free': int(total_samples * free_pct)
            }
        })

        current += delta
        count += 1

    return trends

# Singapore region boundaries (lat/lon) - Subdividing the route-dense area
SINGAPORE_REGIONS = {
    'North': {'lat_min': 1.32, 'lat_max': 1.36, 'lon_min': 103.82, 'lon_max': 103.88},
    'Central': {'lat_min': 1.29, 'lat_max': 1.32, 'lon_min': 103.84, 'lon_max': 103.88},
    'South': {'lat_min': 1.27, 'lat_max': 1.29, 'lon_min': 103.83, 'lon_max': 103.87},
    'East': {'lat_min': 1.29, 'lat_max': 1.34, 'lon_min': 103.88, 'lon_max': 103.90},
    'West': {'lat_min': 1.30, 'lat_max': 1.33, 'lon_min': 103.82, 'lon_max': 103.84}
}


@trends_bp.route('/historical', methods=['GET'])
def get_historical_trends():
    """
    Get historical traffic trends with time aggregation.

    Query Parameters:
    - timescale: 'hourly', 'daily', 'weekly', 'monthly', 'yearly' (default: 'daily')
    - date_from: Start date in YYYY-MM-DD format
    - date_to: End date in YYYY-MM-DD format
    - region: 'North', 'South', 'East', 'West', 'Central', or 'All' (default: 'All')
    - session_id: Optional upload session ID to filter data

    Returns aggregated congestion data for the specified time range.
    """
    try:
        # Parse query parameters
        timescale = request.args.get('timescale', 'daily').lower()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        region = request.args.get('region', 'All')
        session_id = request.args.get('session_id')

        # Validate timescale
        valid_timescales = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']
        if timescale not in valid_timescales:
            return jsonify({'error': f'Invalid timescale. Must be one of: {", ".join(valid_timescales)}'}), 400

        # Set default date range if not provided
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        if not date_from:
            # Default to last 30 days for daily, 12 months for monthly, etc.
            if timescale == 'hourly':
                date_from = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            elif timescale == 'daily':
                date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            elif timescale == 'weekly':
                date_from = (datetime.now() - timedelta(weeks=12)).strftime('%Y-%m-%d')
            elif timescale == 'monthly':
                date_from = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            else:  # yearly
                date_from = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')

        # Map timescale to PostgreSQL date_trunc
        trunc_map = {
            'hourly': 'hour',
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month',
            'yearly': 'year'
        }
        trunc_value = trunc_map[timescale]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build the query with optional region filtering
        region_filter = ""
        params = [date_from, date_to]

        if region != 'All' and region in SINGAPORE_REGIONS:
            bounds = SINGAPORE_REGIONS[region]
            region_filter = """
                AND EXISTS (
                    SELECT 1 FROM road_nodes rn
                    WHERE rn.id = cs.road_node_id
                    AND ST_X(ST_Centroid(rn.geometry)) BETWEEN %s AND %s
                    AND ST_Y(ST_Centroid(rn.geometry)) BETWEEN %s AND %s
                )
            """
            params.extend([bounds['lon_min'], bounds['lon_max'], bounds['lat_min'], bounds['lat_max']])

        session_filter = ""
        if session_id:
            session_filter = "AND cs.session_id = %s"
            params.append(session_id)

        query = f"""
            SELECT
                DATE_TRUNC('{trunc_value}', cs.timestamp) as time_bucket,
                AVG(cs.congestion_index) as avg_congestion,
                MAX(cs.congestion_index) as max_congestion,
                MIN(cs.congestion_index) as min_congestion,
                AVG(cs.speed_kmh) as avg_speed,
                COUNT(DISTINCT cs.road_node_id) as roads_count,
                COUNT(*) as sample_count,
                SUM(CASE WHEN cs.congestion_state = 'jammed' THEN 1 ELSE 0 END) as jammed_count,
                SUM(CASE WHEN cs.congestion_state = 'heavy' THEN 1 ELSE 0 END) as heavy_count,
                SUM(CASE WHEN cs.congestion_state = 'moderate' THEN 1 ELSE 0 END) as moderate_count,
                SUM(CASE WHEN cs.congestion_state = 'free' THEN 1 ELSE 0 END) as free_count
            FROM congestion_states cs
            WHERE cs.timestamp >= %s AND cs.timestamp <= %s::date + INTERVAL '1 day'
            {region_filter}
            {session_filter}
            GROUP BY DATE_TRUNC('{trunc_value}', cs.timestamp)
            ORDER BY time_bucket ASC;
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Format results
        trends = []
        for row in rows:
            trends.append({
                'timestamp': row[0].isoformat() if row[0] else None,
                'avg_congestion': round(row[1], 3) if row[1] else 0,
                'max_congestion': round(row[2], 3) if row[2] else 0,
                'min_congestion': round(row[3], 3) if row[3] else 0,
                'avg_speed': round(row[4], 1) if row[4] else 0,
                'roads_count': row[5] or 0,
                'sample_count': row[6] or 0,
                'congestion_breakdown': {
                    'jammed': row[7] or 0,
                    'heavy': row[8] or 0,
                    'moderate': row[9] or 0,
                    'free': row[10] or 0
                }
            })

        # If no real data found, use demo data
        use_demo = len(trends) == 0

        if use_demo:
            trends = generate_demo_trends(timescale, date_from, date_to)
            # Generate demo summary
            if trends:
                avg_cong = sum(t['avg_congestion'] for t in trends) / len(trends)
                max_cong = max(t['max_congestion'] for t in trends)
                summary = {
                    'overall_avg_congestion': round(avg_cong, 3),
                    'peak_congestion': round(max_cong, 3),
                    'total_roads_analyzed': 200,
                    'is_demo_data': True
                }
            else:
                summary = {
                    'overall_avg_congestion': 0,
                    'peak_congestion': 0,
                    'total_roads_analyzed': 0,
                    'is_demo_data': True
                }
        else:
            # Get summary statistics from real data
            cursor.execute("""
                SELECT
                    AVG(congestion_index) as overall_avg,
                    MAX(congestion_index) as peak_congestion,
                    COUNT(DISTINCT road_node_id) as total_roads
                FROM congestion_states cs
                WHERE cs.timestamp >= %s AND cs.timestamp <= %s::date + INTERVAL '1 day'
            """, [date_from, date_to])

            summary_row = cursor.fetchone()
            summary = {
                'overall_avg_congestion': round(summary_row[0], 3) if summary_row[0] else 0,
                'peak_congestion': round(summary_row[1], 3) if summary_row[1] else 0,
                'total_roads_analyzed': summary_row[2] or 0
            }

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'timescale': timescale,
            'date_from': date_from,
            'date_to': date_to,
            'region': region,
            'data_points': len(trends),
            'trends': trends,
            'summary': summary,
            'is_demo_data': use_demo
        }), 200

    except Exception as e:
        print(f"Historical trends error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@trends_bp.route('/hotspots', methods=['GET'])
def get_hotspots():
    """
    Get top congestion hotspots for a given time period.

    Query Parameters:
    - date_from: Start date
    - date_to: End date
    - limit: Number of hotspots to return (default: 10)
    - region: Filter by region
    """
    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50
        region = request.args.get('region', 'All')

        conn = get_db_connection()
        cursor = conn.cursor()

        region_filter = ""
        params = [date_from, date_to]

        if region != 'All' and region in SINGAPORE_REGIONS:
            bounds = SINGAPORE_REGIONS[region]
            region_filter = """
                AND ST_X(ST_Centroid(rn.geometry)) BETWEEN %s AND %s
                AND ST_Y(ST_Centroid(rn.geometry)) BETWEEN %s AND %s
            """
            params.extend([bounds['lon_min'], bounds['lon_max'], bounds['lat_min'], bounds['lat_max']])

        params.append(limit)

        query = f"""
            SELECT
                rn.id,
                rn.road_name,
                AVG(cs.congestion_index) as avg_congestion,
                COUNT(*) as occurrence_count,
                SUM(CASE WHEN cs.congestion_state = 'jammed' THEN 1 ELSE 0 END) as jammed_count,
                ST_X(ST_Centroid(rn.geometry)) as longitude,
                ST_Y(ST_Centroid(rn.geometry)) as latitude
            FROM congestion_states cs
            JOIN road_nodes rn ON cs.road_node_id = rn.id
            WHERE cs.timestamp >= %s AND cs.timestamp <= %s::date + INTERVAL '1 day'
            {region_filter}
            GROUP BY rn.id, rn.road_name, rn.geometry
            HAVING AVG(cs.congestion_index) > 0.5
            ORDER BY avg_congestion DESC, occurrence_count DESC
            LIMIT %s;
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        hotspots = []
        for rank, row in enumerate(rows, 1):
            hotspots.append({
                'rank': rank,
                'road_id': row[0],
                'road_name': row[1] or 'Unknown Road',
                'avg_congestion': round(row[2], 3) if row[2] else 0,
                'occurrence_count': row[3] or 0,
                'jammed_count': row[4] or 0,
                'coordinates': {
                    'longitude': row[5],
                    'latitude': row[6]
                }
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'date_from': date_from,
            'date_to': date_to,
            'region': region,
            'hotspots': hotspots
        }), 200

    except Exception as e:
        print(f"Hotspots error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@trends_bp.route('/road-details/<int:road_id>', methods=['GET'])
def get_road_details(road_id):
    """
    Get detailed historical trends for a specific road.

    Path Parameters:
    - road_id: The road node ID

    Query Parameters:
    - date_from: Start date
    - date_to: End date
    - timescale: Time aggregation
    """
    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        timescale = request.args.get('timescale', 'hourly').lower()

        trunc_map = {
            'hourly': 'hour',
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month'
        }
        trunc_value = trunc_map.get(timescale, 'hour')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get road info
        cursor.execute("""
            SELECT road_name, road_id, highway_type, length_meters,
                   ST_X(ST_Centroid(geometry)) as longitude,
                   ST_Y(ST_Centroid(geometry)) as latitude
            FROM road_nodes WHERE id = %s
        """, (road_id,))

        road_info = cursor.fetchone()
        if not road_info:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Road not found'}), 404

        # Get historical data
        cursor.execute(f"""
            SELECT
                DATE_TRUNC('{trunc_value}', timestamp) as time_bucket,
                AVG(congestion_index) as avg_congestion,
                AVG(speed_kmh) as avg_speed,
                COUNT(*) as sample_count
            FROM congestion_states
            WHERE road_node_id = %s
            AND timestamp >= %s AND timestamp <= %s::date + INTERVAL '1 day'
            GROUP BY DATE_TRUNC('{trunc_value}', timestamp)
            ORDER BY time_bucket ASC;
        """, (road_id, date_from, date_to))

        rows = cursor.fetchall()

        history = []
        for row in rows:
            history.append({
                'timestamp': row[0].isoformat() if row[0] else None,
                'avg_congestion': round(row[1], 3) if row[1] else 0,
                'avg_speed': round(row[2], 1) if row[2] else 0,
                'sample_count': row[3] or 0
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'road': {
                'id': road_id,
                'name': road_info[0],
                'road_id': road_info[1],
                'highway_type': road_info[2],
                'length_meters': road_info[3],
                'coordinates': {
                    'longitude': road_info[4],
                    'latitude': road_info[5]
                }
            },
            'history': history
        }), 200

    except Exception as e:
        print(f"Road details error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@trends_bp.route('/regions', methods=['GET'])
def get_regions():
    """
    Get available Singapore regions with their boundaries.
    """
    regions = []
    for name, bounds in SINGAPORE_REGIONS.items():
        regions.append({
            'name': name,
            'bounds': bounds,
            'center': {
                'latitude': (bounds['lat_min'] + bounds['lat_max']) / 2,
                'longitude': (bounds['lon_min'] + bounds['lon_max']) / 2
            }
        })

    return jsonify({
        'success': True,
        'regions': regions
    }), 200


@trends_bp.route('/summary', methods=['GET'])
def get_summary():
    """
    Get overall traffic summary statistics.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get today's stats
        cursor.execute("""
            SELECT
                AVG(congestion_index) as avg_congestion,
                COUNT(DISTINCT road_node_id) as roads_monitored,
                SUM(CASE WHEN congestion_state = 'jammed' THEN 1 ELSE 0 END) as jammed_count,
                SUM(CASE WHEN congestion_state = 'heavy' THEN 1 ELSE 0 END) as heavy_count
            FROM congestion_states
            WHERE timestamp >= CURRENT_DATE;
        """)
        today = cursor.fetchone()

        # Get last 7 days average
        cursor.execute("""
            SELECT AVG(congestion_index) as week_avg
            FROM congestion_states
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days';
        """)
        week = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'today': {
                'avg_congestion': round(today[0], 3) if today[0] else 0,
                'roads_monitored': today[1] or 0,
                'jammed_roads': today[2] or 0,
                'heavy_congestion_roads': today[3] or 0
            },
            'last_7_days': {
                'avg_congestion': round(week[0], 3) if week[0] else 0
            }
        }), 200

    except Exception as e:
        print(f"Summary error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

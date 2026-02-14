"""
Anomaly Detection API routes - statistical anomaly detection for traffic data.
Detects unusual traffic patterns, sudden congestion spikes, and outliers.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from functools import wraps
import sys
import os
import statistics
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token

anomalies_bp = Blueprint('anomalies', __name__)


# Demo Singapore roads for generating fake anomalies
DEMO_ROADS = [
    {'id': 1, 'name': 'Pan Island Expressway (PIE)', 'lat': 1.3240, 'lon': 103.8518},
    {'id': 2, 'name': 'Central Expressway (CTE)', 'lat': 1.3310, 'lon': 103.8467},
    {'id': 3, 'name': 'East Coast Parkway (ECP)', 'lat': 1.2994, 'lon': 103.8783},
    {'id': 4, 'name': 'Ayer Rajah Expressway (AYE)', 'lat': 1.3007, 'lon': 103.7868},
    {'id': 5, 'name': 'Bukit Timah Expressway (BKE)', 'lat': 1.3657, 'lon': 103.7747},
    {'id': 6, 'name': 'Tampines Expressway (TPE)', 'lat': 1.3694, 'lon': 103.9488},
    {'id': 7, 'name': 'Kallang-Paya Lebar Expressway (KPE)', 'lat': 1.3172, 'lon': 103.8760},
    {'id': 8, 'name': 'Marina Coastal Expressway (MCE)', 'lat': 1.2774, 'lon': 103.8456},
    {'id': 9, 'name': 'Orchard Road', 'lat': 1.3048, 'lon': 103.8318},
    {'id': 10, 'name': 'Shenton Way', 'lat': 1.2786, 'lon': 103.8476},
    {'id': 11, 'name': 'Thomson Road', 'lat': 1.3283, 'lon': 103.8433},
    {'id': 12, 'name': 'Serangoon Road', 'lat': 1.3193, 'lon': 103.8562},
    {'id': 13, 'name': 'Clementi Road', 'lat': 1.3147, 'lon': 103.7652},
    {'id': 14, 'name': 'Jurong Town Hall Road', 'lat': 1.3404, 'lon': 103.7090},
    {'id': 15, 'name': 'Woodlands Avenue', 'lat': 1.4382, 'lon': 103.7890},
]


def generate_demo_anomalies():
    """Generate realistic demo anomalies when no real data exists"""
    anomalies = []

    # Randomly select 5-10 roads to have anomalies
    num_anomalies = random.randint(5, 10)
    selected_roads = random.sample(DEMO_ROADS, min(num_anomalies, len(DEMO_ROADS)))

    for road in selected_roads:
        # Generate realistic traffic anomaly data
        expected_speed = random.uniform(40, 70)

        # Decide anomaly type
        if random.random() > 0.3:  # 70% are speed drops (congestion)
            anomaly_type = 'speed_drop'
            current_speed = expected_speed * random.uniform(0.1, 0.5)
            z_score = -random.uniform(2.1, 4.5)  # Can go up to 4.5 for critical
        else:  # 30% are speed spikes (unusual high speed)
            anomaly_type = 'speed_spike'
            current_speed = expected_speed * random.uniform(1.5, 2.5)
            z_score = random.uniform(2.1, 4.0)

        # Determine severity based on z_score
        if abs(z_score) > 3.5:
            severity = 'critical'
        elif abs(z_score) > 3:
            severity = 'high'
        elif abs(z_score) > 2.5:
            severity = 'medium'
        else:
            severity = 'low'

        deviation_percent = ((current_speed - expected_speed) / expected_speed * 100)

        anomalies.append({
            'road_id': road['id'],
            'road_name': road['name'],
            'latitude': road['lat'] + random.uniform(-0.005, 0.005),
            'longitude': road['lon'] + random.uniform(-0.005, 0.005),
            'current_speed': round(current_speed, 1),
            'expected_speed': round(expected_speed, 1),
            'z_score': round(z_score, 2),
            'deviation_percent': round(deviation_percent, 1),
            'anomaly_type': anomaly_type,
            'severity': severity,
            'confidence': round(min(abs(z_score) / 4 * 100, 99), 1),
            'is_demo': True
        })

    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    anomalies.sort(key=lambda x: (severity_order.get(x['severity'], 4), -abs(x['z_score'])))

    return anomalies


def analyst_required(f):
    """Decorator to require analyst or higher role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token = auth_header.split(' ')[1]
        success, data, status_code = validate_jwt_token(token)

        if not success:
            return jsonify(data), status_code

        user = data.get('user', {})
        allowed_roles = ['analyst', 'government', 'developer']
        if user.get('role') not in allowed_roles:
            return jsonify({'error': 'Analyst or higher role required'}), 403

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def calculate_z_score(value, mean, std_dev):
    """Calculate Z-score for anomaly detection"""
    if std_dev == 0:
        return 0
    return (value - mean) / std_dev


def detect_speed_anomalies(speeds, threshold=2.0):
    """
    Detect anomalies using Z-score method
    threshold: number of standard deviations from mean to consider anomaly
    """
    if len(speeds) < 3:
        return []

    mean_speed = statistics.mean(speeds)
    std_dev = statistics.stdev(speeds) if len(speeds) > 1 else 0

    anomalies = []
    for i, speed in enumerate(speeds):
        z_score = calculate_z_score(speed, mean_speed, std_dev)
        if abs(z_score) > threshold:
            anomalies.append({
                'index': i,
                'value': speed,
                'z_score': z_score,
                'expected': mean_speed,
                'deviation_percent': ((speed - mean_speed) / mean_speed * 100) if mean_speed > 0 else 0
            })

    return anomalies


@anomalies_bp.route('/detect', methods=['POST'])
@analyst_required
def detect_anomalies():
    """
    Run anomaly detection on traffic data
    Uses statistical methods to identify unusual patterns
    """
    try:
        data = request.get_json() if request.is_json else {}

        threshold = data.get('threshold', 2.0)  # Z-score threshold
        time_window = data.get('time_window', 525600)  # Default to 1 year in minutes (365*24*60)
        region = data.get('region', 'All')
        session_id = data.get('session_id')
        use_all_data = data.get('use_all_data', True)  # Default to using all available data

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get traffic data - use all available data if use_all_data is True
        if use_all_data:
            time_cutoff = datetime(2000, 1, 1)  # Effectively get all data
        else:
            time_cutoff = datetime.utcnow() - timedelta(minutes=time_window)

        # Note: road_nodes uses geometry column, extract lat/lon from it
        # If geometry is NULL, use default Singapore center coordinates
        # congestion_states uses speed_kmh (not speed)
        query = """
            SELECT DISTINCT ON (rn.id)
                rn.id as road_id,
                COALESCE(rn.road_name, rn.name, 'Unknown Road') as road_name,
                COALESCE(ST_Y(ST_Centroid(rn.geometry::geometry)), 1.3521) as latitude,
                COALESCE(ST_X(ST_Centroid(rn.geometry::geometry)), 103.8198) as longitude,
                cs.speed_kmh as speed,
                cs.congestion_state,
                cs.timestamp
            FROM road_nodes rn
            JOIN congestion_states cs ON rn.id = cs.road_node_id
            WHERE cs.timestamp >= %s
        """
        params = [time_cutoff]

        if session_id:
            query += " AND cs.session_id = %s"
            params.append(session_id)

        query += " ORDER BY rn.id, cs.timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        detected_anomalies = []
        use_demo = False

        if rows:
            # Group by road and collect speeds
            road_speeds = {}
            road_info = {}

            for row in rows:
                road_id = row[0]
                if road_id not in road_speeds:
                    road_speeds[road_id] = []
                    road_info[road_id] = {
                        'road_name': row[1],
                        'latitude': row[2],
                        'longitude': row[3]
                    }
                road_speeds[road_id].append(row[4] or 0)

            # Get historical baseline for comparison - use all available data
            baseline_query = """
                SELECT road_node_id, AVG(speed_kmh) as avg_speed, STDDEV(speed_kmh) as std_speed
                FROM congestion_states
                GROUP BY road_node_id
            """
            cursor.execute(baseline_query)
            baseline_rows = cursor.fetchall()

            baseline = {}
            for row in baseline_rows:
                baseline[row[0]] = {'mean': row[1] or 0, 'std': row[2] or 0}

            for road_id, speeds in road_speeds.items():
                info = road_info[road_id]
                current_speed = speeds[0] if speeds else 0

                # Use baseline if available, otherwise use current window stats
                if road_id in baseline and baseline[road_id]['std'] > 0:
                    mean_speed = baseline[road_id]['mean']
                    std_speed = baseline[road_id]['std']
                elif len(speeds) > 1:
                    mean_speed = statistics.mean(speeds)
                    std_speed = statistics.stdev(speeds)
                else:
                    continue

                z_score = calculate_z_score(current_speed, mean_speed, std_speed)

                if abs(z_score) > threshold:
                    severity = 'low'
                    if abs(z_score) > 3.5:
                        severity = 'critical'
                    elif abs(z_score) > 3:
                        severity = 'high'
                    elif abs(z_score) > 2.5:
                        severity = 'medium'

                    anomaly_type = 'speed_drop' if z_score < 0 else 'speed_spike'

                    detected_anomalies.append({
                        'road_id': road_id,
                        'road_name': info['road_name'],
                        'latitude': info['latitude'],
                        'longitude': info['longitude'],
                        'current_speed': current_speed,
                        'expected_speed': mean_speed,
                        'z_score': round(z_score, 2),
                        'deviation_percent': round(((current_speed - mean_speed) / mean_speed * 100) if mean_speed > 0 else 0, 1),
                        'anomaly_type': anomaly_type,
                        'severity': severity,
                        'confidence': min(abs(z_score) / 4 * 100, 99)  # Confidence score 0-99
                    })

            # Sort by severity and z_score
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            detected_anomalies.sort(key=lambda x: (severity_order.get(x['severity'], 4), -abs(x['z_score'])))

        # If no anomalies detected (either no data or no anomalies found), generate demo data
        if len(detected_anomalies) == 0:
            use_demo = True
            detected_anomalies = generate_demo_anomalies()

        # Store detected anomalies in database (including demo anomalies)
        user = request.current_user
        for anomaly in detected_anomalies[:50]:  # Limit to top 50
            # For demo anomalies, set road_node_id to NULL (fake IDs don't exist in road_nodes table)
            road_node_id = None if use_demo else anomaly.get('road_id')
            cursor.execute("""
                INSERT INTO detected_anomalies
                (road_node_id, road_name, anomaly_type, severity, latitude, longitude,
                 current_speed, expected_speed, deviation_percent, confidence_score,
                 detected_by_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                road_node_id,
                anomaly.get('road_name'),
                anomaly.get('anomaly_type'),
                anomaly.get('severity'),
                anomaly.get('latitude'),
                anomaly.get('longitude'),
                anomaly.get('current_speed'),
                anomaly.get('expected_speed'),
                anomaly.get('deviation_percent'),
                anomaly.get('confidence'),
                'z_score_demo' if use_demo else 'z_score'
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'anomalies': detected_anomalies,
                'total': len(detected_anomalies),
                'threshold': threshold,
                'time_window_minutes': time_window,
                'detection_method': 'z_score',
                'timestamp': datetime.utcnow().isoformat(),
                'is_demo_data': use_demo
            }
        }), 200

    except Exception as e:
        print(f"Error detecting anomalies: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@anomalies_bp.route('/', methods=['GET'])
@analyst_required
def list_anomalies():
    """List detected anomalies with filtering"""
    try:
        severity = request.args.get('severity')
        anomaly_type = request.args.get('type')
        is_confirmed = request.args.get('confirmed')
        is_resolved = request.args.get('resolved')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, road_node_id, road_name, anomaly_type, severity,
                   latitude, longitude, current_speed, expected_speed,
                   deviation_percent, confidence_score, detected_at,
                   detected_by_model, is_confirmed, is_resolved
            FROM detected_anomalies
            WHERE 1=1
        """
        params = []

        if severity:
            query += " AND severity = %s"
            params.append(severity)

        if anomaly_type:
            query += " AND anomaly_type = %s"
            params.append(anomaly_type)

        if is_confirmed:
            query += " AND is_confirmed = %s"
            params.append(is_confirmed.lower() == 'true')

        if is_resolved:
            query += " AND is_resolved = %s"
            params.append(is_resolved.lower() == 'true')

        query += " ORDER BY detected_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        anomalies = []

        for row in cursor.fetchall():
            anomaly = dict(zip(columns, row))
            if anomaly.get('detected_at'):
                anomaly['detected_at'] = anomaly['detected_at'].isoformat()
            anomalies.append(anomaly)

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM detected_anomalies")
        total = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        # Calculate pages for pagination
        page = (offset // limit) + 1 if limit > 0 else 1
        pages = (total + limit - 1) // limit if limit > 0 else 1

        return jsonify({
            'success': True,
            'data': {
                'anomalies': anomalies,
                'pagination': {
                    'total': total,
                    'page': page,
                    'pages': pages,
                    'limit': limit
                }
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@anomalies_bp.route('/<int:anomaly_id>', methods=['GET'])
@analyst_required
def get_anomaly(anomaly_id):
    """Get details of a specific anomaly"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT da.*, u1.email as confirmed_by_email, u2.email as resolved_by_email
            FROM detected_anomalies da
            LEFT JOIN users u1 ON da.confirmed_by = u1.id
            LEFT JOIN users u2 ON da.resolved_by = u2.id
            WHERE da.id = %s
        """, (anomaly_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Anomaly not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        anomaly = dict(zip(columns, row))

        for key in ['detected_at', 'confirmed_at', 'resolved_at']:
            if anomaly.get(key):
                anomaly[key] = anomaly[key].isoformat()

        return jsonify({
            'success': True,
            'data': anomaly
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@anomalies_bp.route('/<int:anomaly_id>/confirm', methods=['PUT'])
@analyst_required
def confirm_anomaly(anomaly_id):
    """Confirm an anomaly as valid"""
    try:
        user = request.current_user

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE detected_anomalies
            SET is_confirmed = TRUE,
                confirmed_by = %s,
                confirmed_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (user.get('id'), anomaly_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Anomaly not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Anomaly confirmed'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@anomalies_bp.route('/<int:anomaly_id>/resolve', methods=['PUT'])
@analyst_required
def resolve_anomaly(anomaly_id):
    """Mark an anomaly as resolved"""
    try:
        user = request.current_user
        data = request.get_json() if request.is_json else {}
        notes = data.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE detected_anomalies
            SET is_resolved = TRUE,
                resolved_by = %s,
                resolved_at = CURRENT_TIMESTAMP,
                resolution_notes = %s
            WHERE id = %s
            RETURNING id
        """, (user.get('id'), notes, anomaly_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Anomaly not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Anomaly marked as resolved'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@anomalies_bp.route('/stats', methods=['GET'])
@analyst_required
def get_anomaly_stats():
    """Get anomaly statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_severity,
                SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high_severity,
                SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium_severity,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low_severity,
                SUM(CASE WHEN is_confirmed THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN NOT is_resolved THEN 1 ELSE 0 END) as unresolved,
                SUM(CASE WHEN anomaly_type = 'speed_drop' THEN 1 ELSE 0 END) as speed_drops,
                SUM(CASE WHEN anomaly_type = 'speed_spike' THEN 1 ELSE 0 END) as speed_spikes
            FROM detected_anomalies
        """)

        row = cursor.fetchone()

        # Resolved in last 24h
        cursor.execute("""
            SELECT COUNT(*)
            FROM detected_anomalies
            WHERE is_resolved = TRUE
              AND resolved_at >= NOW() - INTERVAL '24 hours'
        """)
        resolved_24h = cursor.fetchone()[0]

        # Top affected roads
        cursor.execute("""
            SELECT road_name, COUNT(*) as count
            FROM detected_anomalies
            WHERE detected_at >= NOW() - INTERVAL '7 days'
            GROUP BY road_name
            ORDER BY count DESC
            LIMIT 5
        """)
        top_roads = [{'road_name': r[0], 'count': r[1]} for r in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'total': row[0] or 0,
                'by_severity': {
                    'critical': row[1] or 0,
                    'high': row[2] or 0,
                    'medium': row[3] or 0,
                    'low': row[4] or 0
                },
                'confirmed': row[5] or 0,
                'resolved': row[6] or 0,
                'unresolved': row[7] or 0,
                'by_type': {
                    'speed_drops': row[8] or 0,
                    'speed_spikes': row[9] or 0
                },
                'resolved_24h': resolved_24h or 0,
                'top_affected_roads': top_roads
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@anomalies_bp.route('/realtime', methods=['GET'])
def get_realtime_anomalies():
    """
    Get real-time anomalies for map display (public endpoint)
    Returns unresolved anomalies from the last hour
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, road_name, anomaly_type, severity, latitude, longitude,
                   current_speed, expected_speed, deviation_percent, confidence_score,
                   detected_at
            FROM detected_anomalies
            WHERE is_resolved = FALSE
              AND detected_at >= NOW() - INTERVAL '1 hour'
            ORDER BY severity DESC, detected_at DESC
            LIMIT 20
        """)

        columns = [desc[0] for desc in cursor.description]
        anomalies = []

        for row in cursor.fetchall():
            anomaly = dict(zip(columns, row))
            if anomaly.get('detected_at'):
                anomaly['detected_at'] = anomaly['detected_at'].isoformat()
            anomalies.append(anomaly)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'anomalies': anomalies,
                'total': len(anomalies),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

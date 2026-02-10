"""
System Logs API routes - log viewer with flag/resolve functionality.
Provides monitoring and audit trail for system activities.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from functools import wraps
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token

logs_bp = Blueprint('logs', __name__)

# Log levels
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

# Log sources
LOG_SOURCES = [
    'auth', 'api', 'database', 'scheduler', 'model',
    'upload', 'bottleneck', 'weather', 'transport', 'system'
]


def developer_required(f):
    """Decorator to require developer role"""
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
        if user.get('role') not in ['developer', 'government']:
            return jsonify({'error': 'Developer or Government role required'}), 403

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def log_event(level, source, message, details=None, user_id=None, request_id=None, ip_address=None):
    """Helper function to create a log entry"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO system_logs
            (log_level, source, message, details, user_id, request_id, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (level, source, message, details, user_id, request_id, ip_address))

        log_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return log_id
    except Exception as e:
        print(f"Error logging event: {e}")
        return None


@logs_bp.route('/', methods=['GET'])
@developer_required
def list_logs():
    """
    List system logs with filtering
    Supports pagination, level filtering, source filtering, date range
    """
    try:
        # Pagination
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = (page - 1) * limit

        # Filters
        level = request.args.get('level')
        source = request.args.get('source')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search = request.args.get('search')
        flagged_only = request.args.get('flagged_only', 'false').lower() == 'true'
        unresolved_only = request.args.get('unresolved_only', 'false').lower() == 'true'

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT sl.*, u.email as user_email
            FROM system_logs sl
            LEFT JOIN users u ON sl.user_id = u.id
            WHERE 1=1
        """
        params = []

        if level:
            query += " AND sl.log_level = %s"
            params.append(level.upper())

        if source:
            query += " AND sl.source = %s"
            params.append(source)

        if date_from:
            query += " AND sl.timestamp >= %s"
            params.append(date_from)

        if date_to:
            query += " AND sl.timestamp <= %s"
            params.append(date_to)

        if search:
            query += " AND (sl.message ILIKE %s OR sl.details::text ILIKE %s)"
            search_pattern = f'%{search}%'
            params.extend([search_pattern, search_pattern])

        if flagged_only:
            query += " AND sl.is_flagged = TRUE"

        if unresolved_only:
            query += " AND sl.is_flagged = TRUE AND sl.is_resolved = FALSE"

        # Get total count
        count_query = query.replace("SELECT sl.*, u.email as user_email", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Add ordering and pagination
        query += " ORDER BY sl.timestamp DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        logs = []

        for row in cursor.fetchall():
            log = dict(zip(columns, row))
            # Convert datetime objects
            for key in ['timestamp', 'flagged_at', 'resolved_at']:
                if log.get(key):
                    log[key] = log[key].isoformat()
            logs.append(log)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'pages': (total + limit - 1) // limit
                }
            }
        }), 200

    except Exception as e:
        print(f"Error listing logs: {e}")
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/<int:log_id>', methods=['GET'])
@developer_required
def get_log(log_id):
    """Get details of a specific log entry"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sl.*,
                   u1.email as user_email,
                   u2.email as flagged_by_email,
                   u3.email as resolved_by_email
            FROM system_logs sl
            LEFT JOIN users u1 ON sl.user_id = u1.id
            LEFT JOIN users u2 ON sl.flagged_by = u2.id
            LEFT JOIN users u3 ON sl.resolved_by = u3.id
            WHERE sl.id = %s
        """, (log_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Log entry not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        log = dict(zip(columns, row))

        for key in ['timestamp', 'flagged_at', 'resolved_at']:
            if log.get(key):
                log[key] = log[key].isoformat()

        return jsonify({
            'success': True,
            'data': log
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/<int:log_id>/flag', methods=['PUT'])
@developer_required
def flag_log(log_id):
    """Flag a log entry for review"""
    try:
        user = request.current_user

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE system_logs
            SET is_flagged = TRUE,
                flagged_by = %s,
                flagged_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (user.get('id'), log_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Log entry not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Log entry flagged for review'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/<int:log_id>/unflag', methods=['PUT'])
@developer_required
def unflag_log(log_id):
    """Remove flag from a log entry"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE system_logs
            SET is_flagged = FALSE,
                flagged_by = NULL,
                flagged_at = NULL
            WHERE id = %s
            RETURNING id
        """, (log_id,))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Log entry not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Log entry unflagged'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/<int:log_id>/resolve', methods=['PUT'])
@developer_required
def resolve_log(log_id):
    """Mark a flagged log entry as resolved"""
    try:
        user = request.current_user
        data = request.get_json() if request.is_json else {}
        notes = data.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE system_logs
            SET is_resolved = TRUE,
                resolved_by = %s,
                resolved_at = CURRENT_TIMESTAMP,
                resolution_notes = %s
            WHERE id = %s AND is_flagged = TRUE
            RETURNING id
        """, (user.get('id'), notes, log_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Log entry not found or not flagged'}), 404

        return jsonify({
            'success': True,
            'message': 'Log entry marked as resolved'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/stats', methods=['GET'])
@developer_required
def get_log_stats():
    """Get log statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Overall counts by level
        cursor.execute("""
            SELECT log_level, COUNT(*) as count
            FROM system_logs
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY log_level
        """)
        by_level = {row[0]: row[1] for row in cursor.fetchall()}

        # Counts by source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM system_logs
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY source
            ORDER BY count DESC
        """)
        by_source = [{'source': row[0], 'count': row[1]} for row in cursor.fetchall()]

        # Flagged and resolved stats
        cursor.execute("""
            SELECT
                SUM(CASE WHEN is_flagged THEN 1 ELSE 0 END) as flagged,
                SUM(CASE WHEN is_flagged AND NOT is_resolved THEN 1 ELSE 0 END) as unresolved,
                SUM(CASE WHEN is_resolved THEN 1 ELSE 0 END) as resolved
            FROM system_logs
        """)
        flag_stats = cursor.fetchone()

        # Recent activity (last 24h hourly breakdown)
        cursor.execute("""
            SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*) as count
            FROM system_logs
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour
        """)
        hourly_activity = [
            {'hour': row[0].isoformat(), 'count': row[1]}
            for row in cursor.fetchall()
        ]

        # Error rate (last 24h)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN log_level IN ('ERROR', 'CRITICAL') THEN 1 ELSE 0 END) as errors
            FROM system_logs
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """)
        error_row = cursor.fetchone()
        error_rate = (error_row[1] / error_row[0] * 100) if error_row[0] > 0 else 0

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'by_level': {level: by_level.get(level, 0) for level in LOG_LEVELS},
                'by_source': by_source,
                'flagged': flag_stats[0] or 0,
                'unresolved': flag_stats[1] or 0,
                'resolved': flag_stats[2] or 0,
                'hourly_activity': hourly_activity,
                'error_rate_24h': round(error_rate, 2)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/create', methods=['POST'])
def create_log():
    """
    Create a new log entry (internal/service use)
    This endpoint is typically called by other services
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()

        level = data.get('level', 'INFO').upper()
        if level not in LOG_LEVELS:
            return jsonify({'error': f'Invalid log level. Must be one of: {LOG_LEVELS}'}), 400

        source = data.get('source', 'system')
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        log_id = log_event(
            level=level,
            source=source,
            message=message,
            details=data.get('details'),
            user_id=data.get('user_id'),
            request_id=data.get('request_id'),
            ip_address=request.remote_addr
        )

        if log_id:
            return jsonify({
                'success': True,
                'message': 'Log entry created',
                'data': {'id': log_id}
            }), 201
        else:
            return jsonify({'error': 'Failed to create log entry'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@logs_bp.route('/levels', methods=['GET'])
def get_log_levels():
    """Get available log levels"""
    return jsonify({
        'success': True,
        'data': LOG_LEVELS
    }), 200


@logs_bp.route('/sources', methods=['GET'])
def get_log_sources():
    """Get available log sources"""
    return jsonify({
        'success': True,
        'data': LOG_SOURCES
    }), 200


@logs_bp.route('/cleanup', methods=['DELETE'])
@developer_required
def cleanup_old_logs():
    """Delete logs older than specified days (default 90)"""
    try:
        days = int(request.args.get('days', 90))

        if days < 7:
            return jsonify({'error': 'Minimum retention period is 7 days'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM system_logs
            WHERE timestamp < NOW() - INTERVAL '%s days'
              AND is_flagged = FALSE
            RETURNING id
        """, (days,))

        deleted_count = cursor.rowcount
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} log entries older than {days} days'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

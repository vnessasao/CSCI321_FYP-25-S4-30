"""
Algorithm Management API for Traffic Analysis system.
Provides endpoints for viewing, suspending, and activating traffic analysis algorithms.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token
from utils.permission_handler import permission_required

algorithms_bp = Blueprint('algorithms', __name__)


def developer_required(f):
    """Decorator to require developer role."""
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
        if user.get('role') != 'developer':
            return jsonify({'error': 'Developer access required'}), 403

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


@algorithms_bp.route('/', methods=['GET'])
@permission_required('view_algorithms')
def list_algorithms(current_user):
    """
    List all available algorithms.
    Requires view_algorithms permission.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, display_name, description, model_type,
                   is_active, suspended_at, suspended_reason,
                   parameters, created_at, updated_at
            FROM algorithms
            ORDER BY name ASC
        """)

        rows = cursor.fetchall()
        algorithms = []

        for row in rows:
            algorithms.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2] or row[1],
                'description': row[3],
                'model_type': row[4],
                'is_active': row[5],
                'suspended_at': row[6].isoformat() if row[6] else None,
                'suspended_reason': row[7],
                'parameters': row[8] or {},
                'created_at': row[9].isoformat() if row[9] else None,
                'updated_at': row[10].isoformat() if row[10] else None
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'algorithms': algorithms,
            'count': len(algorithms)
        }), 200

    except Exception as e:
        print(f"List algorithms error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@algorithms_bp.route('/<int:algorithm_id>', methods=['GET'])
def get_algorithm(algorithm_id):
    """Get a specific algorithm by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, display_name, description, model_type,
                   is_active, suspended_at, suspended_reason,
                   parameters, created_at, updated_at
            FROM algorithms
            WHERE id = %s
        """, (algorithm_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Algorithm not found'}), 404

        algorithm = {
            'id': row[0],
            'name': row[1],
            'display_name': row[2] or row[1],
            'description': row[3],
            'model_type': row[4],
            'is_active': row[5],
            'suspended_at': row[6].isoformat() if row[6] else None,
            'suspended_reason': row[7],
            'parameters': row[8] or {},
            'created_at': row[9].isoformat() if row[9] else None,
            'updated_at': row[10].isoformat() if row[10] else None
        }

        return jsonify({'success': True, 'algorithm': algorithm}), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@algorithms_bp.route('/<int:algorithm_id>/suspend', methods=['PUT'])
@permission_required('suspend_algorithm')
def suspend_algorithm(algorithm_id, current_user):
    """
    Suspend an algorithm (developer only).

    Expected JSON: {
        'reason': str (required)
    }
    """
    try:
        data = request.get_json()
        reason = data.get('reason', '').strip() if data else ''

        if not reason:
            return jsonify({'error': 'Suspension reason is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if algorithm exists
        cursor.execute("SELECT id, name, is_active FROM algorithms WHERE id = %s", (algorithm_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Algorithm not found'}), 404

        if not result[2]:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Algorithm is already suspended'}), 400

        # Suspend the algorithm
        cursor.execute("""
            UPDATE algorithms
            SET is_active = FALSE, suspended_at = NOW(), suspended_reason = %s, updated_at = NOW()
            WHERE id = %s
        """, (reason, algorithm_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Algorithm "{result[1]}" has been suspended',
            'algorithm_id': algorithm_id
        }), 200

    except Exception as e:
        print(f"Suspend algorithm error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@algorithms_bp.route('/<int:algorithm_id>/activate', methods=['PUT'])
@permission_required('activate_algorithm')
def activate_algorithm(algorithm_id, current_user):
    """Activate a suspended algorithm (developer only)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if algorithm exists
        cursor.execute("SELECT id, name, is_active FROM algorithms WHERE id = %s", (algorithm_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Algorithm not found'}), 404

        if result[2]:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Algorithm is already active'}), 400

        # Activate the algorithm
        cursor.execute("""
            UPDATE algorithms
            SET is_active = TRUE, suspended_at = NULL, suspended_reason = NULL, updated_at = NOW()
            WHERE id = %s
        """, (algorithm_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Algorithm "{result[1]}" has been activated',
            'algorithm_id': algorithm_id
        }), 200

    except Exception as e:
        print(f"Activate algorithm error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@algorithms_bp.route('/<int:algorithm_id>/parameters', methods=['PUT'])
@permission_required('manage_algorithms')
def update_parameters(algorithm_id, current_user):
    """
    Update algorithm parameters.

    Expected JSON: {
        'parameters': object
    }
    """
    try:
        data = request.get_json()
        if not data or 'parameters' not in data:
            return jsonify({'error': 'Parameters object is required'}), 400

        parameters = data['parameters']
        if not isinstance(parameters, dict):
            return jsonify({'error': 'Parameters must be an object'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if algorithm exists
        cursor.execute("SELECT id, name FROM algorithms WHERE id = %s", (algorithm_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Algorithm not found'}), 404

        # Update parameters (merge with existing)
        import json
        cursor.execute("""
            UPDATE algorithms
            SET parameters = parameters || %s::jsonb, updated_at = NOW()
            WHERE id = %s
        """, (json.dumps(parameters), algorithm_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Parameters updated for algorithm "{result[1]}"',
            'algorithm_id': algorithm_id
        }), 200

    except Exception as e:
        print(f"Update parameters error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@algorithms_bp.route('/active', methods=['GET'])
def list_active_algorithms():
    """List only active algorithms."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, display_name, description, model_type, parameters
            FROM algorithms
            WHERE is_active = TRUE
            ORDER BY name ASC
        """)

        rows = cursor.fetchall()
        algorithms = []

        for row in rows:
            algorithms.append({
                'id': row[0],
                'name': row[1],
                'display_name': row[2] or row[1],
                'description': row[3],
                'model_type': row[4],
                'parameters': row[5] or {}
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'algorithms': algorithms,
            'count': len(algorithms)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@algorithms_bp.route('/stats', methods=['GET'])
def get_algorithm_stats():
    """Get algorithm usage statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as suspended
            FROM algorithms
        """)

        row = cursor.fetchone()

        # Get model type breakdown
        cursor.execute("""
            SELECT model_type, COUNT(*) as count
            FROM algorithms
            GROUP BY model_type
        """)

        type_rows = cursor.fetchall()
        by_type = {r[0]: r[1] for r in type_rows}

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total': row[0] or 0,
                'active': row[1] or 0,
                'suspended': row[2] or 0,
                'by_type': by_type
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

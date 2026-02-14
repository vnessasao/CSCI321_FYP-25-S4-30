"""
User Management API for Traffic Analysis system.
Provides endpoints for managing user accounts (admin only).
Includes super user functionality for government admin control.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from argon2 import PasswordHasher
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token

users_bp = Blueprint('users', __name__)
ph = PasswordHasher()

VALID_ROLES = ['public', 'government', 'developer', 'analyst']


def admin_required(f):
    """Decorator to require super admin or developer access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization token required'}), 401

        token = auth_header.split(' ')[1]
        success, data, status_code = validate_jwt_token(token)

        if not success:
            return jsonify(data), status_code

        user = data.get('user', {})
        role = user.get('role')
        user_id = user.get('id')

        # Check if user is developer (full access) or super admin
        if role == 'developer':
            request.current_user = user
            return f(*args, **kwargs)

        if role == 'government':
            # Check if user is super admin
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT is_super_admin FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0]:
                user['is_super_admin'] = True
                request.current_user = user
                return f(*args, **kwargs)

        return jsonify({'error': 'Admin access required'}), 403

    return decorated


@users_bp.route('/', methods=['GET'])
@admin_required
def list_users():
    """
    List all users (admin only).

    Query Parameters:
    - role: Filter by role
    - status: 'active', 'suspended', 'all' (default: 'all')
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)
    """
    try:
        role_filter = request.args.get('role')
        status = request.args.get('status', 'all')
        page = max(1, int(request.args.get('page', 1)))
        limit = min(100, max(1, int(request.args.get('limit', 20))))
        offset = (page - 1) * limit

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query with filters
        where_clauses = []
        params = []

        if role_filter and role_filter in VALID_ROLES:
            where_clauses.append("role = %s")
            params.append(role_filter)

        if status == 'active':
            where_clauses.append("is_active = TRUE AND (is_suspended = FALSE OR is_suspended IS NULL)")
        elif status == 'suspended':
            where_clauses.append("is_suspended = TRUE")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Get total count
        count_query = f"SELECT COUNT(*) FROM users {where_sql}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Get users
        query = f"""
            SELECT id, email, role, name, is_active, is_super_admin,
                   is_suspended, suspended_at, suspended_reason,
                   last_login, created_at
            FROM users
            {where_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        users = []
        for row in rows:
            users.append({
                'id': row[0],
                'email': row[1],
                'role': row[2],
                'name': row[3],
                'is_active': row[4],
                'is_super_admin': row[5] or False,
                'is_suspended': row[6] or False,
                'suspended_at': row[7].isoformat() if row[7] else None,
                'suspended_reason': row[8],
                'last_login': row[9].isoformat() if row[9] else None,
                'created_at': row[10].isoformat() if row[10] else None
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'users': users,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'total_pages': (total_count + limit - 1) // limit
            }
        }), 200

    except Exception as e:
        print(f"List users error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get a specific user by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, role, name, is_active, is_super_admin,
                   is_suspended, suspended_at, suspended_reason,
                   last_login, created_at
            FROM users WHERE id = %s
        """, (user_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'User not found'}), 404

        user = {
            'id': row[0],
            'email': row[1],
            'role': row[2],
            'name': row[3],
            'is_active': row[4],
            'is_super_admin': row[5] or False,
            'is_suspended': row[6] or False,
            'suspended_at': row[7].isoformat() if row[7] else None,
            'suspended_reason': row[8],
            'last_login': row[9].isoformat() if row[9] else None,
            'created_at': row[10].isoformat() if row[10] else None
        }

        return jsonify({'success': True, 'user': user}), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/', methods=['POST'])
@admin_required
def create_user():
    """
    Create a new user (admin only).

    Expected JSON: {
        'email': str,
        'password': str,
        'role': str,
        'name': str (optional)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', '').lower()
        name = data.get('name', '').strip()

        # Validate inputs
        if not email or not password or not role:
            return jsonify({'error': 'Email, password, and role are required'}), 400

        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400

        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400

        # Hash password and create user
        password_hash = ph.hash(password)

        cursor.execute("""
            INSERT INTO users (email, password_hash, role, name, is_active, is_suspended)
            VALUES (%s, %s, %s, %s, TRUE, FALSE)
            RETURNING id, created_at
        """, (email, password_hash, role, name or None))

        result = cursor.fetchone()
        user_id = result[0]
        created_at = result[1]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': user_id,
                'email': email,
                'role': role,
                'name': name,
                'created_at': created_at.isoformat() if created_at else None
            }
        }), 201

    except Exception as e:
        print(f"Create user error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """
    Update a user (admin only).

    Expected JSON: {
        'name': str (optional),
        'role': str (optional),
        'is_active': bool (optional)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id, is_super_admin FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # Prevent modifying super admin
        if result[1] and not request.current_user.get('is_super_admin'):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Cannot modify super admin account'}), 403

        # Build update query
        updates = []
        params = []

        if 'name' in data:
            updates.append("name = %s")
            params.append(data['name'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                cursor.close()
                conn.close()
                return jsonify({'error': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'}), 400
            updates.append("role = %s")
            params.append(data['role'])

        if 'is_active' in data:
            updates.append("is_active = %s")
            params.append(bool(data['is_active']))

        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'User updated successfully'
        }), 200

    except Exception as e:
        print(f"Update user error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<int:user_id>/suspend', methods=['PUT'])
@admin_required
def suspend_user(user_id):
    """
    Suspend or unsuspend a user account.

    Expected JSON: {
        'suspend': bool,
        'reason': str (required if suspending)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        suspend = data.get('suspend', True)
        reason = data.get('reason', '').strip()

        if suspend and not reason:
            return jsonify({'error': 'Reason is required when suspending'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists and is not super admin
        cursor.execute("SELECT id, is_super_admin, email FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        if result[1]:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Cannot suspend super admin account'}), 403

        if suspend:
            cursor.execute("""
                UPDATE users
                SET is_suspended = TRUE, suspended_at = NOW(), suspended_reason = %s
                WHERE id = %s
            """, (reason, user_id))
            message = f"User {result[2]} has been suspended"
        else:
            cursor.execute("""
                UPDATE users
                SET is_suspended = FALSE, suspended_at = NULL, suspended_reason = NULL
                WHERE id = %s
            """, (user_id,))
            message = f"User {result[2]} has been unsuspended"

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': message
        }), 200

    except Exception as e:
        print(f"Suspend user error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Deactivate a user account (soft delete).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists and is not super admin
        cursor.execute("SELECT id, is_super_admin, email FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        if result[1]:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Cannot delete super admin account'}), 403

        # Soft delete - deactivate the user
        cursor.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'User {result[2]} has been deactivated'
        }), 200

    except Exception as e:
        print(f"Delete user error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@users_bp.route('/stats', methods=['GET'])
@admin_required
def get_user_stats():
    """Get user statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                role,
                COUNT(*) as total,
                SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN is_suspended = TRUE THEN 1 ELSE 0 END) as suspended
            FROM users
            GROUP BY role
        """)

        rows = cursor.fetchall()
        stats_by_role = {}
        total_users = 0
        total_active = 0
        total_suspended = 0

        for row in rows:
            stats_by_role[row[0]] = {
                'total': row[1],
                'active': row[2] or 0,
                'suspended': row[3] or 0
            }
            total_users += row[1]
            total_active += row[2] or 0
            total_suspended += row[3] or 0

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'total_active': total_active,
                'total_suspended': total_suspended,
                'by_role': stats_by_role
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

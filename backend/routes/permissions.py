"""
Access Permissions API routes - Permission CRUD and role management.
Manages user permissions and role-permission mappings.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from functools import wraps
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token

permissions_bp = Blueprint('permissions', __name__)

# Valid roles
VALID_ROLES = ['public', 'government', 'analyst', 'developer']


def admin_required(f):
    """Decorator to require government or developer role"""
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
        if user.get('role') not in ['government', 'developer']:
            return jsonify({'error': 'Admin role required'}), 403

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


@permissions_bp.route('/', methods=['GET'])
@admin_required
def list_permissions():
    """List all permissions"""
    try:
        category = request.args.get('category')
        active_only = request.args.get('active_only', 'false').lower() == 'true'

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, name, display_name, description, category,
                   is_active, is_suspended, suspended_at, suspended_reason,
                   created_at, updated_at
            FROM permissions
            WHERE 1=1
        """
        params = []

        if category:
            query += " AND category = %s"
            params.append(category)

        if active_only:
            query += " AND is_active = TRUE AND (is_suspended = FALSE OR is_suspended IS NULL)"

        query += " ORDER BY category, name"

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        permissions = []

        for row in cursor.fetchall():
            perm = dict(zip(columns, row))
            for key in ['suspended_at', 'created_at', 'updated_at']:
                if perm.get(key):
                    perm[key] = perm[key].isoformat()
            permissions.append(perm)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'permissions': permissions,
                'total': len(permissions)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/<int:permission_id>', methods=['GET'])
@admin_required
def get_permission(permission_id):
    """Get a specific permission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, u.email as suspended_by_email
            FROM permissions p
            LEFT JOIN users u ON p.suspended_by = u.id
            WHERE p.id = %s
        """, (permission_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Permission not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        permission = dict(zip(columns, row))

        for key in ['suspended_at', 'created_at', 'updated_at']:
            if permission.get(key):
                permission[key] = permission[key].isoformat()

        return jsonify({
            'success': True,
            'data': permission
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/', methods=['POST'])
@admin_required
def create_permission():
    """Create a new permission"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()

        name = data.get('name', '').strip().lower().replace(' ', '_')
        display_name = data.get('display_name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', 'general').strip().lower()

        if not name:
            return jsonify({'error': 'Permission name is required'}), 400
        if not display_name:
            return jsonify({'error': 'Display name is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if permission already exists
        cursor.execute("SELECT id FROM permissions WHERE name = %s", (name,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Permission with this name already exists'}), 400

        cursor.execute("""
            INSERT INTO permissions (name, display_name, description, category)
            VALUES (%s, %s, %s, %s)
            RETURNING id, created_at
        """, (name, display_name, description, category))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Permission created successfully',
            'data': {
                'id': result[0],
                'name': name,
                'created_at': result[1].isoformat()
            }
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/<int:permission_id>', methods=['PUT'])
@admin_required
def update_permission(permission_id):
    """Update a permission"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if permission exists
        cursor.execute("SELECT id FROM permissions WHERE id = %s", (permission_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Permission not found'}), 404

        updates = []
        params = []

        if 'display_name' in data:
            updates.append("display_name = %s")
            params.append(data['display_name'])

        if 'description' in data:
            updates.append("description = %s")
            params.append(data['description'])

        if 'category' in data:
            updates.append("category = %s")
            params.append(data['category'])

        if 'is_active' in data:
            updates.append("is_active = %s")
            params.append(data['is_active'])

        if not updates:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No fields to update'}), 400

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(permission_id)

        cursor.execute(f"""
            UPDATE permissions
            SET {', '.join(updates)}
            WHERE id = %s
        """, params)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Permission updated successfully'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/<int:permission_id>/suspend', methods=['PUT'])
@admin_required
def suspend_permission(permission_id):
    """Suspend a permission"""
    try:
        user = request.current_user
        data = request.get_json() if request.is_json else {}
        reason = data.get('reason', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE permissions
            SET is_suspended = TRUE,
                suspended_at = CURRENT_TIMESTAMP,
                suspended_by = %s,
                suspended_reason = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (user.get('id'), reason, permission_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Permission not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Permission suspended'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/<int:permission_id>/activate', methods=['PUT'])
@admin_required
def activate_permission(permission_id):
    """Activate a suspended permission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE permissions
            SET is_suspended = FALSE,
                suspended_at = NULL,
                suspended_by = NULL,
                suspended_reason = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (permission_id,))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Permission not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Permission activated'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/<int:permission_id>', methods=['DELETE'])
@admin_required
def delete_permission(permission_id):
    """Delete a permission (soft delete by deactivating)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if permission is used by any role
        cursor.execute("""
            SELECT COUNT(*) FROM role_permissions WHERE permission_id = %s
        """, (permission_id,))
        usage_count = cursor.fetchone()[0]

        if usage_count > 0:
            # Soft delete - deactivate instead of deleting
            cursor.execute("""
                UPDATE permissions
                SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            """, (permission_id,))
        else:
            # Hard delete if not in use
            cursor.execute("""
                DELETE FROM permissions WHERE id = %s RETURNING id
            """, (permission_id,))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Permission not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Permission deleted' if usage_count == 0 else 'Permission deactivated (in use by roles)'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== Role-Permission Management ==========

@permissions_bp.route('/roles', methods=['GET'])
@admin_required
def list_roles_with_permissions():
    """List all roles with their permissions"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        result = {}
        for role in VALID_ROLES:
            cursor.execute("""
                SELECT p.id, p.name, p.display_name, p.description, p.category
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role = %s AND p.is_active = TRUE
                ORDER BY p.category, p.name
            """, (role,))

            columns = [desc[0] for desc in cursor.description]
            permissions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            result[role] = permissions

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'roles': result,
                'available_roles': VALID_ROLES
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/roles/<role>', methods=['GET'])
@admin_required
def get_role_permissions(role):
    """Get permissions for a specific role"""
    try:
        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {VALID_ROLES}'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.id, p.name, p.display_name, p.description, p.category
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role = %s AND p.is_active = TRUE
            ORDER BY p.category, p.name
        """, (role,))

        columns = [desc[0] for desc in cursor.description]
        permissions = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'role': role,
                'permissions': permissions,
                'total': len(permissions)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/roles/<role>', methods=['PUT'])
@admin_required
def update_role_permissions(role):
    """Update permissions for a role"""
    try:
        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {VALID_ROLES}'}), 400

        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        permission_ids = data.get('permission_ids', [])

        if not isinstance(permission_ids, list):
            return jsonify({'error': 'permission_ids must be an array'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove existing permissions
        cursor.execute("DELETE FROM role_permissions WHERE role = %s", (role,))

        # Add new permissions
        for perm_id in permission_ids:
            cursor.execute("""
                INSERT INTO role_permissions (role, permission_id)
                VALUES (%s, %s)
                ON CONFLICT (role, permission_id) DO NOTHING
            """, (role, perm_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Permissions updated for role: {role}'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/roles/<role>/add', methods=['POST'])
@admin_required
def add_permission_to_role(role):
    """Add a permission to a role"""
    try:
        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {VALID_ROLES}'}), 400

        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        permission_id = data.get('permission_id')

        if not permission_id:
            return jsonify({'error': 'permission_id is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO role_permissions (role, permission_id)
            VALUES (%s, %s)
            ON CONFLICT (role, permission_id) DO NOTHING
            RETURNING id
        """, (role, permission_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if result:
            return jsonify({
                'success': True,
                'message': 'Permission added to role'
            }), 201
        else:
            return jsonify({
                'success': True,
                'message': 'Permission already assigned to role'
            }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/roles/<role>/remove', methods=['POST'])
@admin_required
def remove_permission_from_role(role):
    """Remove a permission from a role"""
    try:
        if role not in VALID_ROLES:
            return jsonify({'error': f'Invalid role. Must be one of: {VALID_ROLES}'}), 400

        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        permission_id = data.get('permission_id')

        if not permission_id:
            return jsonify({'error': 'permission_id is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM role_permissions
            WHERE role = %s AND permission_id = %s
            RETURNING id
        """, (role, permission_id))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Permission removed from role' if result else 'Permission was not assigned to role'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@permissions_bp.route('/categories', methods=['GET'])
def get_permission_categories():
    """Get list of permission categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count
            FROM permissions
            WHERE is_active = TRUE
            GROUP BY category
            ORDER BY category
        """)

        categories = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': categories
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

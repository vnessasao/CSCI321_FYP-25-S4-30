"""
Permission checking middleware for route protection.
Verifies if user's role has the required permission.
"""

from flask import request, jsonify
from functools import wraps
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token


def permission_required(permission_name):
    """
    Decorator to require specific permission for route access.
    Checks if user's role has the required permission in the database.
    
    Args:
        permission_name (str): Name of the permission required (e.g., 'view_backups', 'create_backup')
    
    Returns:
        decorator: Function decorator that validates JWT and checks permission
    
    Example:
        @app.route('/backups')
        @permission_required('view_backups')
        def get_backups(current_user):
            # current_user is automatically injected
            return jsonify(backups)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Extract and validate JWT token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Authorization token required'}), 401

            token = auth_header.split(' ')[1]
            success, data, status_code = validate_jwt_token(token)

            if not success:
                return jsonify(data), status_code

            user = data.get('user', {})
            user_role = user.get('role')

            # Developer role has all permissions (bypass check)
            if user_role == 'developer':
                kwargs['current_user'] = user
                return f(*args, **kwargs)

            # Check if user's role has the required permission
            try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM role_permissions rp
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE rp.role = %s 
                    AND p.name = %s 
                    AND p.is_active = TRUE
                    AND rp.is_suspended = FALSE
                """, (user_role, permission_name))

                has_permission = cursor.fetchone()[0] > 0

                cursor.close()
                conn.close()

                if not has_permission:
                    return jsonify({
                        'error': 'Permission denied',
                        'message': f'Your role ({user_role}) does not have the required permission: {permission_name}'
                    }), 403

                # Add current_user to kwargs for use in route function
                kwargs['current_user'] = user

            except Exception as e:
                return jsonify({
                    'error': 'Permission check failed',
                    'message': str(e)
                }), 500

            return f(*args, **kwargs)
        return decorated
    return decorator


def has_permission(user_role, permission_name):
    """
    Helper function to check if a role has a specific permission.
    Can be used within route handlers for conditional logic.
    
    Args:
        user_role (str): User's role (e.g., 'public', 'analyst')
        permission_name (str): Permission to check
    
    Returns:
        bool: True if role has permission, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) 
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role = %s 
            AND p.name = %s 
            AND p.is_active = TRUE
            AND rp.is_suspended = FALSE
        """, (user_role, permission_name))

        result = cursor.fetchone()[0] > 0

        cursor.close()
        conn.close()

        return result

    except Exception:
        return False


def get_user_permissions(user_role):
    """
    Get all permissions for a user's role.
    Useful for frontend to conditionally show/hide UI elements.
    
    Args:
        user_role (str): User's role
    
    Returns:
        list: List of permission names the role has
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role = %s 
            AND p.is_active = TRUE
            AND rp.is_suspended = FALSE
            ORDER BY p.name
        """, (user_role,))

        permissions = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return permissions

    except Exception:
        return []

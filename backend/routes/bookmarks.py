"""
Bookmarks routes for the Traffic Analysis system.
Handles user location bookmarks with authentication.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.jwt_handler import validate_jwt_token
from database_config import get_db_connection

# Create Blueprint
bookmarks_bp = Blueprint('bookmarks', __name__)


def require_auth(f):
    """Decorator to require JWT authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization token provided'}), 401

        # Extract token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401

        # Validate token
        success, response_data, status_code = validate_jwt_token(token)
        if not success:
            return jsonify(response_data), status_code

        # Add user info to request context
        request.user_id = response_data['user']['id']
        request.user_email = response_data['user']['email']
        request.user_role = response_data['user']['role']

        return f(*args, **kwargs)

    return decorated_function


@bookmarks_bp.route('/bookmarks', methods=['GET'])
@require_auth
def get_bookmarks():
    """
    Get all bookmarks for the authenticated user.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, latitude, longitude, address, notes, created_at, updated_at
            FROM bookmarks
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (request.user_id,))

        bookmarks = []
        for row in cursor.fetchall():
            bookmarks.append({
                'id': row[0],
                'name': row[1],
                'latitude': float(row[2]),
                'longitude': float(row[3]),
                'address': row[4],
                'notes': row[5],
                'created_at': row[6].isoformat() if row[6] else None,
                'updated_at': row[7].isoformat() if row[7] else None
            })

        cursor.close()
        conn.close()

        return jsonify({
            'bookmarks': bookmarks,
            'count': len(bookmarks)
        }), 200

    except Exception as e:
        print(f"Get bookmarks error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/bookmarks', methods=['POST'])
@require_auth
def add_bookmark():
    """
    Add a new bookmark for the authenticated user.
    Expected JSON: {'name': str, 'latitude': float, 'longitude': float, 'address': str (optional), 'notes': str (optional)}
    """
    try:
        # Check Content-Type header
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        name = data.get('name', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        # Validate required fields
        if not name:
            return jsonify({'error': 'Name is required'}), 400

        if latitude is None or longitude is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400

        # Validate coordinates
        try:
            latitude = float(latitude)
            longitude = float(longitude)

            # Singapore bounds validation
            if not (1.16 <= latitude <= 1.48 and 103.6 <= longitude <= 104.0):
                return jsonify({'error': 'Coordinates must be within Singapore bounds'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid latitude or longitude format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if bookmark already exists at this location
        cursor.execute("""
            SELECT id FROM bookmarks
            WHERE user_id = %s AND latitude = %s AND longitude = %s
        """, (request.user_id, latitude, longitude))

        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'error': 'You have already bookmarked this location'}), 400

        # Insert new bookmark
        cursor.execute("""
            INSERT INTO bookmarks (user_id, name, latitude, longitude, address, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (request.user_id, name, latitude, longitude, address or None, notes or None))

        bookmark_id, created_at = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Bookmark added successfully',
            'bookmark': {
                'id': bookmark_id,
                'name': name,
                'latitude': latitude,
                'longitude': longitude,
                'address': address,
                'notes': notes,
                'created_at': created_at.isoformat() if created_at else None
            }
        }), 201

    except Exception as e:
        print(f"Add bookmark error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/bookmarks/<int:bookmark_id>', methods=['DELETE'])
@require_auth
def delete_bookmark(bookmark_id):
    """
    Delete a bookmark by ID (only if it belongs to the authenticated user).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if bookmark exists and belongs to user
        cursor.execute("""
            SELECT id FROM bookmarks
            WHERE id = %s AND user_id = %s
        """, (bookmark_id, request.user_id))

        bookmark = cursor.fetchone()
        if not bookmark:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Bookmark not found or does not belong to you'}), 404

        # Delete the bookmark
        cursor.execute("""
            DELETE FROM bookmarks
            WHERE id = %s AND user_id = %s
        """, (bookmark_id, request.user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Bookmark deleted successfully'
        }), 200

    except Exception as e:
        print(f"Delete bookmark error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/bookmarks/check', methods=['POST'])
@require_auth
def check_bookmark():
    """
    Check if a location is already bookmarked.
    Expected JSON: {'latitude': float, 'longitude': float}
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if latitude is None or longitude is None:
            return jsonify({'error': 'Latitude and longitude are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name FROM bookmarks
            WHERE user_id = %s AND latitude = %s AND longitude = %s
        """, (request.user_id, float(latitude), float(longitude)))

        bookmark = cursor.fetchone()
        cursor.close()
        conn.close()

        if bookmark:
            return jsonify({
                'bookmarked': True,
                'bookmark_id': bookmark[0],
                'name': bookmark[1]
            }), 200
        else:
            return jsonify({
                'bookmarked': False
            }), 200

    except Exception as e:
        print(f"Check bookmark error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# ========== Route Bookmarks ==========

@bookmarks_bp.route('/route-bookmarks', methods=['GET'])
@require_auth
def get_route_bookmarks():
    """
    Get all route bookmarks for the authenticated user.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, start_name, start_address, start_lat, start_lon,
                   end_name, end_address, end_lat, end_lon, notes, is_favorite,
                   created_at, updated_at
            FROM route_bookmarks
            WHERE user_id = %s
            ORDER BY is_favorite DESC, created_at DESC
        """, (request.user_id,))

        routes = []
        for row in cursor.fetchall():
            routes.append({
                'id': row[0],
                'name': row[1],
                'start': {
                    'name': row[2],
                    'address': row[3],
                    'lat': float(row[4]),
                    'lon': float(row[5])
                },
                'end': {
                    'name': row[6],
                    'address': row[7],
                    'lat': float(row[8]),
                    'lon': float(row[9])
                },
                'notes': row[10],
                'is_favorite': row[11],
                'created_at': row[12].isoformat() if row[12] else None,
                'updated_at': row[13].isoformat() if row[13] else None
            })

        cursor.close()
        conn.close()

        return jsonify({
            'routes': routes,
            'count': len(routes)
        }), 200

    except Exception as e:
        print(f"Get route bookmarks error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/route-bookmarks', methods=['POST'])
@require_auth
def add_route_bookmark():
    """
    Add a new route bookmark for the authenticated user.
    Expected JSON: {
        'name': str,
        'start': {'name': str, 'address': str, 'lat': float, 'lon': float},
        'end': {'name': str, 'address': str, 'lat': float, 'lon': float},
        'notes': str (optional),
        'is_favorite': bool (optional)
    }
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        name = data.get('name', '').strip()
        start = data.get('start')
        end = data.get('end')
        notes = data.get('notes', '').strip()
        is_favorite = data.get('is_favorite', False)

        # Validate required fields
        if not name:
            return jsonify({'error': 'Route name is required'}), 400

        if not start or not end:
            return jsonify({'error': 'Start and end locations are required'}), 400

        # Validate start location
        if not all(k in start for k in ['name', 'lat', 'lon']):
            return jsonify({'error': 'Start location must include name, lat, and lon'}), 400

        # Validate end location
        if not all(k in end for k in ['name', 'lat', 'lon']):
            return jsonify({'error': 'End location must include name, lat, and lon'}), 400

        # Validate coordinates
        try:
            start_lat = float(start['lat'])
            start_lon = float(start['lon'])
            end_lat = float(end['lat'])
            end_lon = float(end['lon'])

            # Singapore bounds validation
            if not (1.16 <= start_lat <= 1.48 and 103.6 <= start_lon <= 104.0):
                return jsonify({'error': 'Start coordinates must be within Singapore bounds'}), 400
            if not (1.16 <= end_lat <= 1.48 and 103.6 <= end_lon <= 104.0):
                return jsonify({'error': 'End coordinates must be within Singapore bounds'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid coordinate format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert new route bookmark
        cursor.execute("""
            INSERT INTO route_bookmarks
            (user_id, name, start_name, start_address, start_lat, start_lon,
             end_name, end_address, end_lat, end_lon, notes, is_favorite)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (
            request.user_id, name,
            start['name'], start.get('address', ''), start_lat, start_lon,
            end['name'], end.get('address', ''), end_lat, end_lon,
            notes or None, is_favorite
        ))

        route_id, created_at = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Route bookmark added successfully',
            'route': {
                'id': route_id,
                'name': name,
                'start': start,
                'end': end,
                'notes': notes,
                'is_favorite': is_favorite,
                'created_at': created_at.isoformat() if created_at else None
            }
        }), 201

    except Exception as e:
        print(f"Add route bookmark error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/route-bookmarks/<int:route_id>', methods=['DELETE'])
@require_auth
def delete_route_bookmark(route_id):
    """
    Delete a route bookmark by ID (only if it belongs to the authenticated user).
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if route bookmark exists and belongs to user
        cursor.execute("""
            SELECT id FROM route_bookmarks
            WHERE id = %s AND user_id = %s
        """, (route_id, request.user_id))

        route = cursor.fetchone()
        if not route:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Route bookmark not found or does not belong to you'}), 404

        # Delete the route bookmark
        cursor.execute("""
            DELETE FROM route_bookmarks
            WHERE id = %s AND user_id = %s
        """, (route_id, request.user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Route bookmark deleted successfully'
        }), 200

    except Exception as e:
        print(f"Delete route bookmark error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bookmarks_bp.route('/route-bookmarks/<int:route_id>/favorite', methods=['PATCH'])
@require_auth
def toggle_route_favorite(route_id):
    """
    Toggle favorite status of a route bookmark.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if route belongs to user and toggle favorite
        cursor.execute("""
            UPDATE route_bookmarks
            SET is_favorite = NOT is_favorite, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s
            RETURNING is_favorite
        """, (route_id, request.user_id))

        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Route bookmark not found or does not belong to you'}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Favorite status updated',
            'is_favorite': result[0]
        }), 200

    except Exception as e:
        print(f"Toggle favorite error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

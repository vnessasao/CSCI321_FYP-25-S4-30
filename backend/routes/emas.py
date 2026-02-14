"""
EMAS routes for managing EMAS incidents
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import psycopg2
from database_config import get_db_connection
from utils.jwt_handler import token_required

emas_bp = Blueprint('emas', __name__)


@emas_bp.route('/emas/incidents', methods=['GET'])
@token_required(allowed_roles=['government', 'developer', 'analyst'])
def get_emas_incidents(current_user):
    """Get all EMAS incidents"""
    try:
        status = request.args.get('status', 'all')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            if status == 'all':
                cursor.execute("""
                    SELECT e.id, e.location, e.description, e.incident_type, e.status,
                           e.latitude, e.longitude, e.reported_at, e.cleared_at, e.updated_at,
                           e.roadwork_id, r.start_time as roadwork_start, r.end_time as roadwork_end
                    FROM emas_incidents e
                    LEFT JOIN roadwork_events r ON e.roadwork_id = r.id
                    ORDER BY e.reported_at DESC
                """)
            else:
                cursor.execute("""
                    SELECT e.id, e.location, e.description, e.incident_type, e.status,
                           e.latitude, e.longitude, e.reported_at, e.cleared_at, e.updated_at,
                           e.roadwork_id, r.start_time as roadwork_start, r.end_time as roadwork_end
                    FROM emas_incidents e
                    LEFT JOIN roadwork_events r ON e.roadwork_id = r.id
                    WHERE e.status = %s
                    ORDER BY e.reported_at DESC
                """, (status,))

            incidents = cursor.fetchall()

            result = []
            for incident in incidents:
                result.append({
                    'id': incident[0],
                    'location': incident[1],
                    'description': incident[2],
                    'type': incident[3],
                    'status': incident[4],
                    'latitude': incident[5],
                    'longitude': incident[6],
                    'time': incident[7].isoformat() if incident[7] else None,
                    'cleared_at': incident[8].isoformat() if incident[8] else None,
                    'updated_at': incident[9].isoformat() if incident[9] else None,
                    'roadwork_id': incident[10],
                    'roadwork_start': incident[11].isoformat() if incident[11] else None,
                    'roadwork_end': incident[12].isoformat() if incident[12] else None
                })

            return jsonify({
                'success': True,
                'data': result
            }), 200

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Database error: {str(e)}'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@emas_bp.route('/emas/incidents', methods=['POST'])
@token_required(allowed_roles=['government', 'developer'])
def create_emas_incident(current_user):
    """Create a new EMAS incident"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        if not data.get('location'):
            return jsonify({
                'success': False,
                'message': 'Location is required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO emas_incidents (location, description, incident_type, latitude, longitude, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, reported_at
            """, (
                data['location'],
                data.get('description', ''),
                data.get('type', 'General'),
                data.get('latitude'),
                data.get('longitude'),
                current_user['id']
            ))

            result = cursor.fetchone()
            conn.commit()

            return jsonify({
                'success': True,
                'message': 'EMAS incident created successfully',
                'data': {
                    'id': result[0],
                    'reported_at': result[1].isoformat()
                }
            }), 201

        except psycopg2.Error as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': f'Database error: {str(e)}'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@emas_bp.route('/emas/incidents/<int:incident_id>/status', methods=['PUT'])
@token_required(allowed_roles=['government', 'developer'])
def update_emas_status(current_user, incident_id):
    """Update EMAS incident status"""
    try:
        data = request.get_json()

        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': 'Status is required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if incident exists
            cursor.execute("SELECT id FROM emas_incidents WHERE id = %s", (incident_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Incident not found'
                }), 404

            new_status = data['status']

            if new_status == 'Cleared':
                cursor.execute("""
                    UPDATE emas_incidents
                    SET status = %s, cleared_at = CURRENT_TIMESTAMP, cleared_by = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (new_status, current_user['id'], incident_id))
            else:
                cursor.execute("""
                    UPDATE emas_incidents
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (new_status, incident_id))

            conn.commit()

            return jsonify({
                'success': True,
                'message': f'Incident status updated to {new_status}'
            }), 200

        except Exception as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': f'Database error: {str(e)}'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@emas_bp.route('/emas/incidents/<int:incident_id>', methods=['DELETE'])
@token_required(allowed_roles=['government', 'developer'])
def delete_emas_incident(current_user, incident_id):
    """Delete an EMAS incident"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM emas_incidents WHERE id = %s RETURNING id", (incident_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({
                    'success': False,
                    'message': 'Incident not found'
                }), 404

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Incident deleted successfully'
            }), 200

        except Exception as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': f'Database error: {str(e)}'
            }), 500

        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500

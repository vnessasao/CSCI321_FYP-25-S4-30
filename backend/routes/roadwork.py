"""
Roadwork routes for managing roadwork events
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import psycopg2
from database_config import get_db_connection
from utils.jwt_handler import token_required

roadwork_bp = Blueprint('roadwork', __name__)


@roadwork_bp.route('/roadwork', methods=['GET'])
@token_required(allowed_roles=['government', 'developer'])
def get_roadwork_events(current_user):
    """Get all roadwork events"""
    try:
        status = request.args.get('status', 'all')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            if status == 'all':
                cursor.execute("""
                    SELECT id, location, description, start_time, end_time,
                           is_emas, status, created_by, created_at
                    FROM roadwork_events
                    ORDER BY start_time DESC
                """)
            else:
                cursor.execute("""
                    SELECT id, location, description, start_time, end_time,
                           is_emas, status, created_by, created_at
                    FROM roadwork_events
                    WHERE status = %s
                    ORDER BY start_time DESC
                """, (status,))

            events = cursor.fetchall()

            result = []
            for event in events:
                result.append({
                    'id': event[0],
                    'location': event[1],
                    'description': event[2],
                    'startTime': event[3].isoformat() if event[3] else None,
                    'endTime': event[4].isoformat() if event[4] else None,
                    'emas': event[5],
                    'status': event[6],
                    'created_by': event[7],
                    'created_at': event[8].isoformat() if event[8] else None
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


@roadwork_bp.route('/roadwork', methods=['POST'])
@token_required(allowed_roles=['government', 'developer'])
def create_roadwork_event(current_user):
    """Create a new roadwork event"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['location', 'startTime', 'endTime']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'{field} is required'
                }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO roadwork_events (location, description, start_time, end_time, is_emas, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                data['location'],
                data.get('description', ''),
                data['startTime'],
                data['endTime'],
                data.get('emasIncident', False),
                current_user['id']
            ))

            result = cursor.fetchone()
            roadwork_id = result[0]
            created_at = result[1]

            emas_incident_id = None

            # If EMAS incident checkbox is checked, create an EMAS incident
            if data.get('emasIncident', False):
                cursor.execute("""
                    INSERT INTO emas_incidents (location, description, incident_type, status, roadwork_id, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    data['location'],
                    f"Roadwork event at {data['location']}",
                    'Roadwork',
                    'Active',
                    roadwork_id,
                    current_user['id']
                ))
                emas_result = cursor.fetchone()
                emas_incident_id = emas_result[0]

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Roadwork event created successfully' + (' with EMAS incident' if emas_incident_id else ''),
                'data': {
                    'id': roadwork_id,
                    'created_at': created_at.isoformat(),
                    'emas_incident_id': emas_incident_id
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


@roadwork_bp.route('/roadwork/<int:event_id>', methods=['PUT'])
@token_required(allowed_roles=['government', 'developer'])
def update_roadwork_event(current_user, event_id):
    """Update a roadwork event"""
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if event exists
            cursor.execute("SELECT id FROM roadwork_events WHERE id = %s", (event_id,))
            if not cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Event not found'
                }), 404

            updates = []
            values = []

            if 'location' in data:
                updates.append("location = %s")
                values.append(data['location'])
            if 'description' in data:
                updates.append("description = %s")
                values.append(data['description'])
            if 'startTime' in data:
                updates.append("start_time = %s")
                values.append(data['startTime'])
            if 'endTime' in data:
                updates.append("end_time = %s")
                values.append(data['endTime'])
            if 'status' in data:
                updates.append("status = %s")
                values.append(data['status'])
            if 'emasIncident' in data:
                updates.append("is_emas = %s")
                values.append(data['emasIncident'])

            if not updates:
                return jsonify({
                    'success': False,
                    'message': 'No fields to update'
                }), 400

            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(event_id)

            cursor.execute(f"""
                UPDATE roadwork_events
                SET {', '.join(updates)}
                WHERE id = %s
            """, values)

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Event updated successfully'
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


@roadwork_bp.route('/roadwork/<int:event_id>', methods=['DELETE'])
@token_required(allowed_roles=['government', 'developer'])
def delete_roadwork_event(current_user, event_id):
    """Delete a roadwork event"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM roadwork_events WHERE id = %s RETURNING id", (event_id,))
            result = cursor.fetchone()

            if not result:
                return jsonify({
                    'success': False,
                    'message': 'Event not found'
                }), 404

            conn.commit()

            return jsonify({
                'success': True,
                'message': 'Event deleted successfully'
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

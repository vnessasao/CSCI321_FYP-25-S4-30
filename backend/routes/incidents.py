"""
Incidents routes for handling incident reports
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import psycopg2
import pytz
from database_config import get_db_connection
from utils.jwt_handler import token_required
from utils.permission_handler import permission_required

incidents_bp = Blueprint('incidents', __name__)

def validate_incident_data(data):
    """Validate incident data before inserting into database"""
    errors = []
    
    # Check required fields
    required_fields = ['user_id', 'incident_type', 'location', 'date', 'time', 'period', 'description']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Field '{field}' is required")
    
    # Timezone is optional, default to UTC
    if 'timezone' not in data or not data['timezone']:
        data['timezone'] = 'UTC'
    
    if errors:
        return errors
    
    # Validate incident type
    valid_types = ['Accident', 'Vehicle breakdown', 'Roadworks', 'Obstruction']
    if data['incident_type'] not in valid_types:
        errors.append(f"Invalid incident type. Must be one of: {', '.join(valid_types)}")
    
    # Validate period
    if data['period'] not in ['AM', 'PM']:
        errors.append("Period must be 'AM' or 'PM'")
    
    # Parse and validate date
    try:
        incident_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except ValueError:
        errors.append("Invalid date format. Use YYYY-MM-DD")
        return errors
    
    # Validate timezone
    try:
        user_timezone = pytz.timezone(data['timezone'])
    except pytz.UnknownTimeZoneError:
        errors.append(f"Invalid timezone: {data['timezone']}. Use format like 'Asia/Kolkata', 'America/New_York', etc.")
        return errors
    
    # Parse and validate time
    try:
        # Convert 12-hour time with AM/PM to 24-hour format
        time_str = f"{data['time']} {data['period']}"
        parsed_time = datetime.strptime(time_str, '%H:%M %p').time()
            
    except ValueError:
        errors.append("Invalid time format. Use HH:MM")
        return errors
    
    # Validate description length
    if len(data['description'].strip()) < 5:
        errors.append("Description must be at least 5 characters long")
    
    if len(data['description'].strip()) > 1000:
        errors.append("Description cannot exceed 1000 characters")
    
    return errors

def user_exists(user_id):
    """Check if user exists in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        return result is not None
    except Exception:
        return False
    finally:
        cursor.close()
        conn.close()

@incidents_bp.route('/incidents', methods=['POST'])
@permission_required('report_incident')
def create_incident(current_user):
    """Create a new incident report"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Add current user ID to the data
        data['user_id'] = current_user['id']
        
        # Validate the incident data
        validation_errors = validate_incident_data(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'message': 'Validation failed',
                'errors': validation_errors
            }), 400
        
        # Verify user exists
        if not user_exists(data['user_id']):
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # Convert user input to UTC datetime
        time_str = f"{data['time']} {data['period']}"
        
        # Parse the local time
        local_time = datetime.strptime(time_str, '%H:%M %p').time()
        
        # Combine date and time
        local_datetime = datetime.combine(datetime.strptime(data['date'], '%Y-%m-%d').date(), local_time)
        
        # Convert to user's timezone
        user_timezone = pytz.timezone(data.get('timezone', 'UTC'))
        localized_datetime = user_timezone.localize(local_datetime)
        
        # Convert to UTC
        utc_datetime = localized_datetime.astimezone(pytz.UTC)
        
        # Extract UTC date and time for database
        utc_date = utc_datetime.date()
        utc_time = utc_datetime.time()
        
        # Insert incident into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            insert_data = (
                data['user_id'],
                data['incident_type'],
                data['location'],
                utc_date,
                utc_time,
                data['description'].strip()
            )
            
            cursor.execute("""
                INSERT INTO incidents (user_id, incident_type, location, date, time, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, insert_data)
            
            result = cursor.fetchone()
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Incident reported successfully',
                'data': {
                    'id': result[0],
                    'created_at': result[1].isoformat()
                }
            }), 201
            
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'fk_incidents_user_id' in str(e):
                return jsonify({
                    'success': False,
                    'message': 'Invalid user ID'
                }), 400
            else:
                return jsonify({
                    'success': False,
                    'message': 'Database constraint violation'
                }), 400
                
        except psycopg2.Error as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': 'Database error'
            }), 500
            
        except Exception as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'message': 'Internal server error'
            }), 500
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@incidents_bp.route('/incidents', methods=['GET'])
@token_required()
def get_user_incidents(current_user):
    """Get all incidents reported by the current user"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, incident_type, location, date, time, description, created_at
                FROM incidents 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (current_user['id'],))
            
            incidents = cursor.fetchall()
            
            # Format the results
            result = []
            for incident in incidents:
                result.append({
                    'id': incident[0],
                    'incident_type': incident[1],
                    'location': incident[2],
                    'date': incident[3].strftime('%Y-%m-%d'),
                    'time': incident[4].strftime('%H:%M'),
                    'description': incident[5],
                    'created_at': incident[6].isoformat()
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

@incidents_bp.route('/incidents/<int:incident_id>', methods=['GET'])
@token_required()
def get_incident(current_user, incident_id):
    """Get a specific incident by ID (only if it belongs to the current user)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, incident_type, location, date, time, description, created_at
                FROM incidents 
                WHERE id = %s AND user_id = %s
            """, (incident_id, current_user['id']))
            
            incident = cursor.fetchone()
            
            if not incident:
                return jsonify({
                    'success': False,
                    'message': 'Incident not found'
                }), 404
            
            result = {
                'id': incident[0],
                'incident_type': incident[1],
                'location': incident[2],
                'date': incident[3].strftime('%Y-%m-%d'),
                'time': incident[4].strftime('%H:%M'),
                'description': incident[5],
                'created_at': incident[6].isoformat()
            }
            
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

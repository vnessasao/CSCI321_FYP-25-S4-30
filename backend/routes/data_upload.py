"""
Data Upload Routes
Handles file uploads for road networks and GPS trajectories with session management
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging
import uuid
from database_config import DatabaseConfig
import sys

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.preprocessing_service import PreprocessingService
from utils.permission_handler import permission_required

logger = logging.getLogger(__name__)

# Create blueprint
data_upload_bp = Blueprint('data_upload', __name__, url_prefix='/api/upload')

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sessions')
ALLOWED_ROAD_EXTENSIONS = {'geojson', 'json'}
ALLOWED_GPS_EXTENSIONS = {'csv'}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_db_connection():
    """Get database connection"""
    db_config = DatabaseConfig()
    return db_config.get_db_connection()


@data_upload_bp.route('/create-session', methods=['POST'])
@permission_required('upload_traffic_data')
def create_session(current_user):
    """Create a new upload session"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Set all previous sessions to inactive
        cursor.execute("""
            UPDATE upload_sessions
            SET is_active = FALSE
            WHERE is_active = TRUE
        """)

        # Create new session
        cursor.execute("""
            INSERT INTO upload_sessions (status, is_active)
            VALUES ('pending', TRUE)
            RETURNING session_id, created_at
        """)

        result = cursor.fetchone()
        session_id = str(result[0])
        created_at = result[1]

        conn.commit()

        # Create session folder
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)

        logger.info(f"Created new upload session: {session_id}")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'created_at': created_at.isoformat(),
            'status': 'pending'
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating session: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to create session: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/road-network', methods=['POST'])
@permission_required('upload_traffic_data')
def upload_road_network(current_user):
    """Upload road network GeoJSON file"""
    conn = None
    cursor = None

    try:
        # Check if session_id is provided
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400

        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename, ALLOWED_ROAD_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_ROAD_EXTENSIONS)}'
            }), 400

        # Secure the filename
        filename = secure_filename(file.filename)

        # Save file to session folder
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)

        file_path = os.path.join(session_folder, 'roads.geojson')
        file.save(file_path)

        # Update session in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE upload_sessions
            SET road_network_filename = %s
            WHERE session_id = %s
        """, (filename, session_id))

        conn.commit()

        logger.info(f"Uploaded road network for session {session_id}: {filename}")

        return jsonify({
            'success': True,
            'message': 'Road network uploaded successfully',
            'filename': filename,
            'session_id': session_id
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error uploading road network: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to upload road network: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/gps-trajectories', methods=['POST'])
@permission_required('upload_traffic_data')
def upload_gps_trajectories(current_user):
    """Upload GPS trajectories CSV file"""
    conn = None
    cursor = None

    try:
        # Check if session_id is provided
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400

        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename, ALLOWED_GPS_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_GPS_EXTENSIONS)}'
            }), 400

        # Secure the filename
        filename = secure_filename(file.filename)

        # Save file to session folder
        session_folder = os.path.join(UPLOAD_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)

        file_path = os.path.join(session_folder, 'gps_trajectories.csv')
        file.save(file_path)

        # Update session in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE upload_sessions
            SET gps_trajectories_filename = %s
            WHERE session_id = %s
        """, (filename, session_id))

        conn.commit()

        logger.info(f"Uploaded GPS trajectories for session {session_id}: {filename}")

        return jsonify({
            'success': True,
            'message': 'GPS trajectories uploaded successfully',
            'filename': filename,
            'session_id': session_id
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error uploading GPS trajectories: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to upload GPS trajectories: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/preprocess', methods=['POST'])
def preprocess_data():
    """Preprocess uploaded data"""
    conn = None
    cursor = None

    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400

        # Verify session exists and has both files
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT road_network_filename, gps_trajectories_filename, status
            FROM upload_sessions
            WHERE session_id = %s
        """, (session_id,))

        session = cursor.fetchone()

        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        road_filename, gps_filename, status = session

        if not road_filename or not gps_filename:
            return jsonify({
                'success': False,
                'error': 'Both road network and GPS trajectories must be uploaded first'
            }), 400

        if status == 'preprocessing':
            return jsonify({
                'success': False,
                'error': 'Preprocessing is already in progress'
            }), 400

        # Update status to preprocessing
        import datetime
        cursor.execute("""
            UPDATE upload_sessions
            SET status = 'preprocessing',
                preprocessing_started_at = %s
            WHERE session_id = %s
        """, (datetime.datetime.now(), session_id))

        conn.commit()

        # Start preprocessing
        logger.info(f"Starting preprocessing for session {session_id}")

        preprocessing_service = PreprocessingService()
        start_time = datetime.datetime.now()

        try:
            # Load road network
            road_count = preprocessing_service.load_road_network_from_geojson(session_id)
            logger.info(f"Loaded {road_count} roads for session {session_id}")

            # Build road graph
            preprocessing_service.build_road_graph(session_id)
            logger.info(f"Built road graph for session {session_id}")

            # Process GPS trajectories
            gps_count = preprocessing_service.process_gps_trajectories(session_id)
            logger.info(f"Processed {gps_count} GPS points for session {session_id}")

            end_time = datetime.datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            # Update session status to ready
            cursor.execute("""
                UPDATE upload_sessions
                SET status = 'ready',
                    preprocessing_completed_at = %s,
                    road_count = %s,
                    gps_point_count = %s
                WHERE session_id = %s
            """, (end_time, road_count, gps_count, session_id))

            conn.commit()

            logger.info(f"Preprocessing completed for session {session_id}")

            return jsonify({
                'success': True,
                'message': 'Preprocessing completed successfully',
                'session_id': session_id,
                'road_count': road_count,
                'gps_point_count': gps_count,
                'processing_time_seconds': round(processing_time, 2)
            }), 200

        except Exception as preprocessing_error:
            # Update status to failed
            cursor.execute("""
                UPDATE upload_sessions
                SET status = 'failed',
                    error_message = %s
                WHERE session_id = %s
            """, (str(preprocessing_error), session_id))

            conn.commit()

            logger.error(f"Preprocessing failed for session {session_id}: {str(preprocessing_error)}")

            return jsonify({
                'success': False,
                'error': f'Preprocessing failed: {str(preprocessing_error)}'
            }), 500

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error in preprocess endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to preprocess data: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/session-status/<session_id>', methods=['GET'])
def get_session_status(session_id):
    """Get the status of an upload session"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                session_id,
                created_at,
                status,
                road_network_filename,
                gps_trajectories_filename,
                road_count,
                gps_point_count,
                preprocessing_started_at,
                preprocessing_completed_at,
                error_message,
                is_active
            FROM upload_sessions
            WHERE session_id = %s
        """, (session_id,))

        session = cursor.fetchone()

        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        session_data = {
            'session_id': str(session[0]),
            'created_at': session[1].isoformat() if session[1] else None,
            'status': session[2],
            'road_network_filename': session[3],
            'gps_trajectories_filename': session[4],
            'road_count': session[5],
            'gps_point_count': session[6],
            'preprocessing_started_at': session[7].isoformat() if session[7] else None,
            'preprocessing_completed_at': session[8].isoformat() if session[8] else None,
            'error_message': session[9],
            'is_active': session[10]
        }

        return jsonify({
            'success': True,
            'session': session_data
        }), 200

    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get session status: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/status', methods=['GET'])
def get_upload_status():
    """Get overall upload status (legacy endpoint)"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get active session
        cursor.execute("""
            SELECT
                session_id,
                status,
                road_count,
                gps_point_count
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if session:
            return jsonify({
                'success': True,
                'has_active_session': True,
                'session_id': str(session[0]),
                'status': session[1],
                'road_count': session[2] or 0,
                'gps_count': session[3] or 0
            }), 200
        else:
            return jsonify({
                'success': True,
                'has_active_session': False,
                'road_count': 0,
                'gps_count': 0
            }), 200

    except Exception as e:
        logger.error(f"Error getting upload status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get upload status: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/active-session-info', methods=['GET'])
def get_active_session_info():
    """Get information about the active session including whether it's pre-inserted data"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get active session
        cursor.execute("""
            SELECT 
                session_id,
                status,
                roads_file,
                gps_file,
                road_count,
                gps_point_count
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])
        status = session[1]
        roads_file = session[2]
        gps_file = session[3]
        road_count = session[4]
        gps_count = session[5]

        # Check if this is the pre-inserted session
        # Pre-inserted sessions either have session_id = 'sample' or have NULL file paths
        is_preinserted = (session_id == 'sample' or (roads_file is None and gps_file is None))

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': status,
            'is_preinserted': is_preinserted,
            'road_count': road_count or 0,
            'gps_count': gps_count or 0
        }), 200

    except Exception as e:
        logger.error(f"Error getting active session info: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get active session info: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@data_upload_bp.route('/restore-preinserted', methods=['POST'])
@permission_required('upload_traffic_data')
def restore_preinserted_data(current_user):
    """Restore the pre-inserted (sample) data session as active"""
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find the pre-inserted session (the one with session_id = 'sample' or the oldest one)
        cursor.execute("""
            SELECT session_id, status
            FROM upload_sessions
            WHERE session_id = 'sample'
               OR (roads_file IS NULL AND gps_file IS NULL AND status = 'ready')
            ORDER BY created_at ASC
            LIMIT 1
        """)

        preinserted_session = cursor.fetchone()

        if not preinserted_session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No pre-inserted data session found'
            }), 404

        preinserted_session_id = preinserted_session[0]
        session_status = preinserted_session[1]

        if session_status != 'ready':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Pre-inserted session is not ready. Current status: {session_status}'
            }), 400

        # Set all sessions to inactive
        cursor.execute("""
            UPDATE upload_sessions
            SET is_active = FALSE
            WHERE is_active = TRUE
        """)

        # Set the pre-inserted session as active
        cursor.execute("""
            UPDATE upload_sessions
            SET is_active = TRUE
            WHERE session_id = %s
        """, (preinserted_session_id,))

        conn.commit()

        logger.info(f"Pre-inserted data session {preinserted_session_id} restored as active")

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Pre-inserted data restored successfully',
            'session_id': preinserted_session_id
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error restoring pre-inserted data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to restore pre-inserted data: {str(e)}'
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

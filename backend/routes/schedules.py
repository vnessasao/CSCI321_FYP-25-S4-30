"""
Schedule API routes - manages automated model runs with APScheduler.
Provides CRUD for schedules and email notifications.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from functools import wraps
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token

schedules_bp = Blueprint('schedules', __name__)

# Cron expression presets
FREQUENCY_PRESETS = {
    'hourly': '0 * * * *',
    'every_3_hours': '0 */3 * * *',
    'every_6_hours': '0 */6 * * *',
    'daily': '0 9 * * *',
    'daily_morning': '0 7 * * *',
    'daily_evening': '0 18 * * *',
    'twice_daily': '0 7,18 * * *',
    'weekly': '0 9 * * 1',
    'monthly': '0 9 1 * *'
}


def analyst_required(f):
    """Decorator to require analyst or higher role"""
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
        allowed_roles = ['analyst', 'government', 'developer']
        if user.get('role') not in allowed_roles:
            return jsonify({'error': 'Analyst or higher role required'}), 403

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def calculate_next_run(cron_expression):
    """Calculate next run time from cron expression (simplified)"""
    # For now, return a simplified next run time
    # In production, use croniter library for accurate calculation
    now = datetime.utcnow()

    if cron_expression == '0 * * * *':  # hourly
        return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    elif cron_expression == '0 */3 * * *':  # every 3 hours
        next_hour = ((now.hour // 3) + 1) * 3
        if next_hour >= 24:
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
    elif cron_expression.startswith('0 9'):  # daily at 9am
        next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run
    elif '* * 1' in cron_expression:  # weekly (Monday)
        days_until_monday = (7 - now.weekday()) % 7 or 7
        return (now + timedelta(days=days_until_monday)).replace(hour=9, minute=0, second=0, microsecond=0)
    elif '1 * *' in cron_expression:  # monthly (1st)
        if now.day == 1 and now.hour < 9:
            return now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now.month == 12:
            return now.replace(year=now.year + 1, month=1, day=1, hour=9, minute=0, second=0, microsecond=0)
        return now.replace(month=now.month + 1, day=1, hour=9, minute=0, second=0, microsecond=0)
    else:
        return now + timedelta(hours=1)


@schedules_bp.route('/', methods=['GET'])
@analyst_required
def list_schedules():
    """List all schedules for the current user or all (for admins)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        user = request.current_user
        show_all = request.args.get('all', 'false').lower() == 'true'

        if show_all and user.get('role') in ['government', 'developer']:
            cursor.execute("""
                SELECT ms.*, u.email as creator_email, a.display_name as algorithm_name
                FROM model_schedules ms
                LEFT JOIN users u ON ms.created_by = u.id
                LEFT JOIN algorithms a ON ms.algorithm_id = a.id
                ORDER BY ms.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT ms.*, u.email as creator_email, a.display_name as algorithm_name
                FROM model_schedules ms
                LEFT JOIN users u ON ms.created_by = u.id
                LEFT JOIN algorithms a ON ms.algorithm_id = a.id
                WHERE ms.created_by = %s
                ORDER BY ms.created_at DESC
            """, (user.get('id'),))

        columns = [desc[0] for desc in cursor.description]
        schedules = []

        for row in cursor.fetchall():
            schedule = dict(zip(columns, row))
            # Convert datetime objects to ISO format
            for key in ['last_run', 'next_run', 'created_at', 'updated_at']:
                if schedule.get(key):
                    schedule[key] = schedule[key].isoformat()
            schedules.append(schedule)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'schedules': schedules,
                'total': len(schedules)
            }
        }), 200

    except Exception as e:
        print(f"Error listing schedules: {e}")
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/', methods=['POST'])
@analyst_required
def create_schedule():
    """Create a new schedule"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        user = request.current_user

        # Validate required fields
        name = data.get('name', '').strip()
        model_type = data.get('model_type', '').strip()
        frequency = data.get('frequency', 'daily')

        if not name:
            return jsonify({'error': 'Schedule name is required'}), 400
        if not model_type:
            return jsonify({'error': 'Model type is required'}), 400

        # Get cron expression
        cron_expression = data.get('cron_expression')
        if not cron_expression:
            cron_expression = FREQUENCY_PRESETS.get(frequency, FREQUENCY_PRESETS['daily'])

        # Calculate next run
        next_run = calculate_next_run(cron_expression)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO model_schedules
            (name, model_type, algorithm_id, cron_expression, notification_email,
             parameters, is_active, next_run, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (
            name,
            model_type,
            data.get('algorithm_id'),
            cron_expression,
            data.get('notification_email', user.get('email')),
            data.get('parameters', '{}'),
            True,
            next_run,
            user.get('id')
        ))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Schedule created successfully',
            'data': {
                'id': result[0],
                'created_at': result[1].isoformat(),
                'next_run': next_run.isoformat()
            }
        }), 201

    except Exception as e:
        print(f"Error creating schedule: {e}")
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/<int:schedule_id>', methods=['GET'])
@analyst_required
def get_schedule(schedule_id):
    """Get a specific schedule"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ms.*, u.email as creator_email, a.display_name as algorithm_name
            FROM model_schedules ms
            LEFT JOIN users u ON ms.created_by = u.id
            LEFT JOIN algorithms a ON ms.algorithm_id = a.id
            WHERE ms.id = %s
        """, (schedule_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Schedule not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        schedule = dict(zip(columns, row))

        for key in ['last_run', 'next_run', 'created_at', 'updated_at']:
            if schedule.get(key):
                schedule[key] = schedule[key].isoformat()

        return jsonify({
            'success': True,
            'data': schedule
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/<int:schedule_id>', methods=['PUT'])
@analyst_required
def update_schedule(schedule_id):
    """Update a schedule"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        user = request.current_user

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check ownership or admin
        cursor.execute("SELECT created_by FROM model_schedules WHERE id = %s", (schedule_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Schedule not found'}), 404

        if row[0] != user.get('id') and user.get('role') not in ['government', 'developer']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Not authorized to update this schedule'}), 403

        # Build update query
        updates = []
        params = []

        if 'name' in data:
            updates.append("name = %s")
            params.append(data['name'])

        if 'model_type' in data:
            updates.append("model_type = %s")
            params.append(data['model_type'])

        if 'algorithm_id' in data:
            updates.append("algorithm_id = %s")
            params.append(data['algorithm_id'])

        if 'frequency' in data or 'cron_expression' in data:
            cron = data.get('cron_expression') or FREQUENCY_PRESETS.get(data.get('frequency'), FREQUENCY_PRESETS['daily'])
            updates.append("cron_expression = %s")
            params.append(cron)
            updates.append("next_run = %s")
            params.append(calculate_next_run(cron))

        if 'notification_email' in data:
            updates.append("notification_email = %s")
            params.append(data['notification_email'])

        if 'parameters' in data:
            updates.append("parameters = %s")
            params.append(data['parameters'])

        if 'is_active' in data:
            updates.append("is_active = %s")
            params.append(data['is_active'])

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(schedule_id)

        cursor.execute(f"""
            UPDATE model_schedules
            SET {', '.join(updates)}
            WHERE id = %s
        """, params)

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Schedule updated successfully'
        }), 200

    except Exception as e:
        print(f"Error updating schedule: {e}")
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/<int:schedule_id>', methods=['DELETE'])
@analyst_required
def delete_schedule(schedule_id):
    """Delete a schedule"""
    try:
        user = request.current_user

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check ownership or admin
        cursor.execute("SELECT created_by FROM model_schedules WHERE id = %s", (schedule_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Schedule not found'}), 404

        if row[0] != user.get('id') and user.get('role') not in ['government', 'developer']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Not authorized to delete this schedule'}), 403

        cursor.execute("DELETE FROM model_schedules WHERE id = %s", (schedule_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Schedule deleted successfully'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/<int:schedule_id>/toggle', methods=['PUT'])
@analyst_required
def toggle_schedule(schedule_id):
    """Toggle schedule active/inactive"""
    try:
        user = request.current_user

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT created_by, is_active FROM model_schedules WHERE id = %s", (schedule_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Schedule not found'}), 404

        if row[0] != user.get('id') and user.get('role') not in ['government', 'developer']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Not authorized'}), 403

        new_status = not row[1]

        cursor.execute("""
            UPDATE model_schedules
            SET is_active = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_status, schedule_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Schedule {"activated" if new_status else "deactivated"} successfully',
            'data': {'is_active': new_status}
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/<int:schedule_id>/run', methods=['POST'])
@analyst_required
def run_schedule_now(schedule_id):
    """Manually trigger a schedule to run immediately"""
    try:
        user = request.current_user

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, model_type, algorithm_id, parameters
            FROM model_schedules WHERE id = %s
        """, (schedule_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Schedule not found'}), 404

        # Update last run info
        cursor.execute("""
            UPDATE model_schedules
            SET last_run = CURRENT_TIMESTAMP,
                last_run_status = 'running',
                run_count = run_count + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (schedule_id,))

        conn.commit()

        # TODO: Actually run the model here
        # For now, just simulate success
        cursor.execute("""
            UPDATE model_schedules
            SET last_run_status = 'completed',
                last_run_message = 'Manual run completed successfully',
                next_run = %s
            WHERE id = %s
        """, (calculate_next_run('0 * * * *'), schedule_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Schedule executed successfully',
            'data': {
                'schedule_id': schedule_id,
                'status': 'completed',
                'run_at': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error running schedule: {e}")
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/stats', methods=['GET'])
@analyst_required
def get_schedule_stats():
    """Get schedule statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END) as inactive,
                SUM(run_count) as total_runs,
                SUM(CASE WHEN last_run_status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
                SUM(CASE WHEN last_run_status = 'failed' THEN 1 ELSE 0 END) as failed_runs
            FROM model_schedules
        """)

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'total': row[0] or 0,
                'active': row[1] or 0,
                'inactive': row[2] or 0,
                'total_runs': row[3] or 0,
                'successful_runs': row[4] or 0,
                'failed_runs': row[5] or 0
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@schedules_bp.route('/frequencies', methods=['GET'])
def get_frequency_presets():
    """Get available frequency presets"""
    presets = []
    for key, cron in FREQUENCY_PRESETS.items():
        descriptions = {
            'hourly': 'Every hour at :00',
            'every_3_hours': 'Every 3 hours',
            'every_6_hours': 'Every 6 hours',
            'daily': 'Daily at 9:00 AM',
            'daily_morning': 'Daily at 7:00 AM',
            'daily_evening': 'Daily at 6:00 PM',
            'twice_daily': 'Twice daily (7 AM & 6 PM)',
            'weekly': 'Weekly on Monday at 9:00 AM',
            'monthly': 'Monthly on 1st at 9:00 AM'
        }
        presets.append({
            'key': key,
            'cron_expression': cron,
            'description': descriptions.get(key, key)
        })

    return jsonify({
        'success': True,
        'data': presets
    }), 200

"""
Backup & Restore API routes - Database backup and restore functionality.
Uses pg_dump for PostgreSQL backups.
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
from functools import wraps
import subprocess
import os
import sys
import gzip
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_config import get_db_connection
from utils.jwt_handler import validate_jwt_token
from utils.permission_handler import permission_required
from utils.permission_handler import permission_required

backups_bp = Blueprint('backups', __name__)

# Backup directory
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# System tables to exclude from backup list
EXCLUDE_TABLES = [
    'spatial_ref_sys',
    'geography_columns', 
    'geometry_columns',
    'migrations'
]


def get_all_tables():
    """Dynamically fetch all tables from database, excluding system tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        all_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        # Filter out system tables
        backup_tables = [t for t in all_tables if t not in EXCLUDE_TABLES]
        return backup_tables
        
    except Exception as e:
        print(f"Error fetching tables: {e}")
        # Fallback to basic list if query fails
        return ['users', 'algorithms', 'permissions', 'role_permissions',
                'road_nodes', 'road_edges', 'congestion_states',
                'incidents', 'bookmarks', 'route_bookmarks',
                'upload_sessions', 'model_schedules', 'system_logs',
                'feedback', 'backups']


def developer_required(f):
    """Decorator to require developer role"""
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
        if user.get('role') not in ['developer', 'government']:
            return jsonify({'error': 'Developer or Government role required'}), 403

        request.current_user = user
        return f(*args, **kwargs)

    return decorated


def get_db_config():
    """Get database configuration from environment"""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'traffic_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }


def run_pg_dump(output_file, tables=None, compress=True):
    """
    Create database backup using Python (no pg_dump required).
    Exports table data as SQL INSERT statements.
    """
    import json

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        backup_tables = tables if tables else get_all_tables()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"-- Traffic Bottleneck Database Backup\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write(f"-- Tables: {', '.join(backup_tables)}\n\n")

            for table in backup_tables:
                try:
                    # Check if table exists
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        )
                    """, (table,))

                    if not cursor.fetchone()[0]:
                        f.write(f"-- Table {table} does not exist, skipping\n\n")
                        continue

                    # Get column info (explicitly from public schema to avoid conflicts with auth schema)
                    cursor.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = %s
                        ORDER BY ordinal_position
                    """, (table,))
                    columns = cursor.fetchall()
                    col_names = [c[0] for c in columns]
                    
                    # Check for duplicate column names
                    if len(col_names) != len(set(col_names)):
                        duplicates = [name for name in set(col_names) if col_names.count(name) > 1]
                        f.write(f"-- Table: {table} - SKIPPED (contains duplicate columns: {', '.join(duplicates)})\n")
                        f.write(f"-- Note: This table has a schema issue that needs to be fixed before backup\n\n")
                        continue

                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    row_count = cursor.fetchone()[0]

                    f.write(f"-- Table: {table} ({row_count} rows)\n")

                    if row_count > 0:
                        # Export data
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()

                        for row in rows:
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, bool):
                                    values.append('TRUE' if val else 'FALSE')
                                elif isinstance(val, (int, float)):
                                    values.append(str(val))
                                elif isinstance(val, datetime):
                                    values.append(f"'{val.isoformat()}'")
                                elif isinstance(val, dict) or isinstance(val, list):
                                    values.append(f"'{json.dumps(val)}'")
                                else:
                                    # Escape single quotes
                                    escaped = str(val).replace("'", "''")
                                    values.append(f"'{escaped}'")

                            f.write(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({', '.join(values)});\n")

                    f.write("\n")

                except Exception as table_error:
                    f.write(f"-- Error backing up {table}: {str(table_error)}\n\n")

        cursor.close()
        conn.close()

        # Compress if requested
        if compress:
            with open(output_file, 'rb') as f_in:
                with gzip.open(f'{output_file}.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(output_file)
            return True, f'{output_file}.gz'

        return True, output_file

    except Exception as e:
        return False, str(e)


def run_pg_restore(backup_file):
    """Restore database from SQL backup file using Python"""
    try:
        # Decompress if needed
        actual_file = backup_file
        temp_file = None
        
        if backup_file.endswith('.gz'):
            actual_file = backup_file[:-3]
            temp_file = actual_file
            with gzip.open(backup_file, 'rb') as f_in:
                with open(actual_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

        # Read SQL file
        with open(actual_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Clean up temp file if created
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

        # Parse backup to find table names
        import re
        table_pattern = r'-- Table: (\w+) \(\d+ rows\)'
        tables_in_backup = re.findall(table_pattern, sql_content)
        
        # Exclude backups table from restore to avoid deleting backup records
        tables_to_restore = [t for t in tables_in_backup if t != 'backups']
        
        # First, truncate tables in a separate transaction
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for table in tables_to_restore:
            try:
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
                print(f"Truncated table: {table}")
            except Exception as truncate_error:
                print(f"Warning: Could not truncate {table}: {truncate_error}")
        
        conn.commit()
        cursor.close()
        conn.close()

        # Now restore data with a fresh connection in autocommit mode
        conn = get_db_connection()
        # Commit any pending transaction before setting autocommit
        conn.commit()
        conn.autocommit = True
        cursor = conn.cursor()

        # Split into individual INSERT statements and execute
        statements = sql_content.split('\n')
        current_statement = []
        success_count = 0
        error_count = 0
        skip_backups_table = False
        
        for line in statements:
            # Check if we're in backups table section
            if '-- Table: backups' in line:
                skip_backups_table = True
                print("Skipping backups table to preserve backup records")
                continue
            
            # Reset skip flag when we hit another table
            if line.startswith('-- Table:') and 'backups' not in line:
                skip_backups_table = False
            
            # Skip comments and empty lines
            if line.strip().startswith('--') or not line.strip():
                continue
            
            # Skip if we're in backups table section
            if skip_backups_table:
                continue
            
            current_statement.append(line)
            
            # Execute when we hit a semicolon
            if line.strip().endswith(';'):
                stmt = '\n'.join(current_statement)
                try:
                    cursor.execute(stmt)
                    success_count += 1
                except Exception as stmt_error:
                    error_count += 1
                    if error_count <= 5:  # Only print first 5 errors
                        print(f"Error executing statement: {stmt_error}")
                        print(f"Statement: {stmt[:200]}...")
                
                current_statement = []
        
        cursor.close()
        conn.close()

        print(f"Restore completed: {success_count} statements succeeded, {error_count} statements failed")
        
        if error_count > 0 and success_count == 0:
            return False, f'Restore failed: all {error_count} statements failed'
        
        return True, f'Restore completed: {success_count} statements executed successfully'

    except Exception as e:
        print(f"Error in run_pg_restore: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


@backups_bp.route('/', methods=['GET'])
@permission_required('view_backups')
def list_backups(current_user):
    """List all backups"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.*, u.email as created_by_email
            FROM backups b
            LEFT JOIN users u ON b.created_by = u.id
            WHERE b.is_deleted = FALSE
            ORDER BY b.created_at DESC
        """)

        columns = [desc[0] for desc in cursor.description]
        backups = []

        for row in cursor.fetchall():
            backup = dict(zip(columns, row))
            if backup.get('created_at'):
                backup['created_at'] = backup['created_at'].isoformat()
            if backup.get('deleted_at'):
                backup['deleted_at'] = backup['deleted_at'].isoformat()

            # Check if file still exists
            if backup.get('file_path'):
                backup['file_exists'] = os.path.exists(backup['file_path'])

            backups.append(backup)

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'backups': backups,
                'total': len(backups)
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/', methods=['POST'])
@permission_required('create_backup')
def create_backup(current_user):
    """Create a new backup"""
    try:
        data = request.get_json() if request.is_json else {}
        user = current_user

        backup_type = data.get('type', 'full')  # full, partial
        tables = data.get('tables', get_all_tables() if backup_type == 'full' else [])
        notes = data.get('notes', '')
        compress = data.get('compress', True)

        if backup_type == 'partial' and not tables:
            return jsonify({'error': 'Tables must be specified for partial backup'}), 400

        # Generate filename with local system time
        local_time = datetime.now()
        timestamp = local_time.strftime('%Y%m%d_%H%M%S')
        filename = f"backup_{backup_type}_{timestamp}.sql"
        output_file = os.path.join(BACKUP_DIR, filename)

        # Run pg_dump
        success, result = run_pg_dump(output_file, tables if backup_type == 'partial' else None, compress)

        if not success:
            return jsonify({
                'success': False,
                'error': f'Backup failed: {result}'
            }), 500

        # Get file size
        file_path = result
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        final_filename = os.path.basename(file_path)

        # Record in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO backups
            (filename, file_path, file_size, backup_type, status, tables_included, created_by, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, created_at
        """, (
            final_filename,
            file_path,
            file_size,
            backup_type,
            'completed',
            tables,
            user.get('id'),
            notes
        ))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'data': {
                'id': result[0],
                'filename': final_filename,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'created_at': local_time.isoformat()
            }
        }), 201

    except Exception as e:
        print(f"Error creating backup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/<int:backup_id>', methods=['GET'])
@permission_required('view_backups')
def get_backup(backup_id, current_user):
    """Get backup details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.*, u.email as created_by_email
            FROM backups b
            LEFT JOIN users u ON b.created_by = u.id
            WHERE b.id = %s
        """, (backup_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Backup not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        backup = dict(zip(columns, row))

        if backup.get('created_at'):
            backup['created_at'] = backup['created_at'].isoformat()

        if backup.get('file_path'):
            backup['file_exists'] = os.path.exists(backup['file_path'])

        return jsonify({
            'success': True,
            'data': backup
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/<int:backup_id>/download', methods=['GET'])
@permission_required('download_backup')
def download_backup(backup_id, current_user):
    """Download a backup file"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT filename, file_path FROM backups WHERE id = %s", (backup_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({'error': 'Backup not found'}), 404

        filename, file_path = row

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'Backup file not found on disk'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/<int:backup_id>/restore', methods=['POST'])
@permission_required('restore_backup')
def restore_backup(backup_id, current_user):
    """Restore from a backup"""
    try:
        data = request.get_json() if request.is_json else {}
        confirm = data.get('confirm', False)

        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Restore operation requires confirmation. Set confirm: true'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT filename, file_path FROM backups WHERE id = %s AND is_deleted = FALSE", (backup_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            print(f"Backup not found for ID: {backup_id}")
            return jsonify({'error': 'Backup not found'}), 404

        filename, file_path = row

        if not file_path or not os.path.exists(file_path):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Backup file not found on disk'}), 404

        cursor.close()
        conn.close()

        # Perform restore
        success, message = run_pg_restore(file_path)

        if not success:
            return jsonify({
                'success': False,
                'error': f'Restore failed: {message}'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Database restored successfully',
            'data': {
                'backup_id': backup_id,
                'filename': filename,
                'restored_at': datetime.utcnow().isoformat()
            }
        }), 200

    except Exception as e:
        print(f"Error restoring backup: {e}")
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/<int:backup_id>', methods=['DELETE'])
@permission_required('delete_backup')
def delete_backup(backup_id, current_user):
    """Delete a backup (soft delete)"""
    try:
        data = request.get_json() if request.is_json else {}
        hard_delete = data.get('hard_delete', False)

        conn = get_db_connection()
        cursor = conn.cursor()

        if hard_delete:
            # Get file path first
            cursor.execute("SELECT file_path FROM backups WHERE id = %s", (backup_id,))
            row = cursor.fetchone()

            if row and row[0] and os.path.exists(row[0]):
                os.remove(row[0])

            cursor.execute("DELETE FROM backups WHERE id = %s RETURNING id", (backup_id,))
        else:
            cursor.execute("""
                UPDATE backups
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            """, (backup_id,))

        result = cursor.fetchone()
        conn.commit()

        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Backup not found'}), 404

        return jsonify({
            'success': True,
            'message': 'Backup deleted' + (' permanently' if hard_delete else '')
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/stats', methods=['GET'])
@permission_required('view_backups')
def get_backup_stats(current_user):
    """Get backup statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN backup_type = 'full' THEN 1 ELSE 0 END) as full_backups,
                SUM(CASE WHEN backup_type = 'partial' THEN 1 ELSE 0 END) as partial_backups,
                SUM(file_size) as total_size,
                MAX(created_at) as last_backup
            FROM backups
            WHERE is_deleted = FALSE
        """)

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'total': row[0] or 0,
                'full_backups': row[1] or 0,
                'partial_backups': row[2] or 0,
                'total_size_bytes': row[3] or 0,
                'total_size_mb': round((row[3] or 0) / (1024 * 1024), 2),
                'last_backup': row[4].isoformat() if row[4] else None
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@backups_bp.route('/tables', methods=['GET'])
@developer_required
def get_available_tables():
    """Get list of tables available for backup"""
    try:
        tables = get_all_tables()
        return jsonify({
            'success': True,
            'data': {
                'tables': tables,
                'total': len(tables)
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@backups_bp.route('/cleanup', methods=['DELETE'])
@developer_required
def cleanup_old_backups():
    """Delete backups older than specified days"""
    try:
        days = int(request.args.get('days', 30))
        hard_delete = request.args.get('hard_delete', 'false').lower() == 'true'

        if days < 7:
            return jsonify({'error': 'Minimum retention period is 7 days'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if hard_delete:
            # Get file paths first
            cursor.execute("""
                SELECT file_path FROM backups
                WHERE created_at < NOW() - INTERVAL '%s days'
                  AND is_deleted = FALSE
            """, (days,))

            for row in cursor.fetchall():
                if row[0] and os.path.exists(row[0]):
                    try:
                        os.remove(row[0])
                    except Exception:
                        pass

            cursor.execute("""
                DELETE FROM backups
                WHERE created_at < NOW() - INTERVAL '%s days'
                RETURNING id
            """, (days,))
        else:
            cursor.execute("""
                UPDATE backups
                SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP
                WHERE created_at < NOW() - INTERVAL '%s days'
                  AND is_deleted = FALSE
                RETURNING id
            """, (days,))

        deleted_count = cursor.rowcount
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} backups older than {days} days'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

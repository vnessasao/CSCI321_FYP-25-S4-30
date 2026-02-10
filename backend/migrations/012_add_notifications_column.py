"""
Migration: Add last_checked_notifications column to users table
"""

import psycopg2
from datetime import datetime


def run(connection):
    """Execute the migration"""
    cursor = connection.cursor()
    
    try:
        print("Adding last_checked_notifications column to users table...")
        
        # Add last_checked_notifications column
        cursor.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS last_checked_notifications TIMESTAMP DEFAULT NULL
        """)
        
        print("✓ Successfully added last_checked_notifications column")
        
        connection.commit()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error during migration: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


def rollback(connection):
    """Rollback the migration"""
    cursor = connection.cursor()
    
    try:
        print("Rolling back: Removing last_checked_notifications column...")
        
        cursor.execute("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS last_checked_notifications
        """)
        
        connection.commit()
        print("✓ Rollback successful")
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error during rollback: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()


if __name__ == '__main__':
    # For testing
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from database_config import get_db_connection
    
    conn = get_db_connection()
    success = run(conn)
    conn.close()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")

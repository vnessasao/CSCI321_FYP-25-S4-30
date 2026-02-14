"""
Migration 003: Fix incidents datetime constraint
Created: December 11, 2025
"""

def up(cursor):
    """Fix the datetime constraint to properly handle time comparisons"""
    # Drop the problematic constraint
    cursor.execute("""
        ALTER TABLE incidents 
        DROP CONSTRAINT IF EXISTS chk_incidents_datetime_not_future;
    """)
    
    # Add a simpler constraint that just checks the date
    # We'll handle time validation in the application layer
    cursor.execute("""
        ALTER TABLE incidents 
        ADD CONSTRAINT chk_incidents_datetime_not_future 
        CHECK (date <= CURRENT_DATE);
    """)

def down(cursor):
    """Revert to the original constraint"""
    cursor.execute("""
        ALTER TABLE incidents 
        DROP CONSTRAINT IF EXISTS chk_incidents_datetime_not_future;
    """)
    
    cursor.execute("""
        ALTER TABLE incidents 
        ADD CONSTRAINT chk_incidents_datetime_not_future 
        CHECK (
            date < CURRENT_DATE OR 
            (date = CURRENT_DATE AND time <= CURRENT_TIME)
        );
    """)

if __name__ == "__main__":
    # This allows running the migration directly
    import sys
    sys.path.append('..')
    from database_config import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        up(cursor)
        conn.commit()
        print("Migration 003: incidents datetime constraint fixed successfully")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.close()
        conn.close()
"""
Migration 002: Create incidents table
Created: December 11, 2025
"""

def up(cursor):
    """Create the incidents table"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            incident_type TEXT NOT NULL CHECK (incident_type IN ('Accident', 'Vehicle breakdown', 'Roadworks', 'Obstruction')),
            location TEXT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            CONSTRAINT fk_incidents_user_id 
                FOREIGN KEY (user_id) 
                REFERENCES users(id) 
                ON DELETE CASCADE,
            CONSTRAINT chk_incidents_date_not_future 
                CHECK (date <= CURRENT_DATE),
            CONSTRAINT chk_incidents_datetime_not_future 
                CHECK (
                    date < CURRENT_DATE OR 
                    (date = CURRENT_DATE AND time <= CURRENT_TIME)
                )
        );
    """)
    
    # Create indexes for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_user_id ON incidents(user_id);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_date ON incidents(date);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
    """)

def down(cursor):
    """Drop the incidents table"""
    cursor.execute("DROP TABLE IF EXISTS incidents CASCADE;")

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
        print("Migration 002: incidents table created successfully")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.close()
        conn.close()
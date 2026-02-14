"""
Migration: Create users table
Creates the users table with authentication and role management fields.
"""

import os
import sys

# Add parent directory to path to import database_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


def up(cursor):
    """Create users table."""
    try:
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on email for faster lookups
        cursor.execute("""
            CREATE INDEX idx_users_email ON users(email)
        """)
        
        # Create index on role for role-based queries
        cursor.execute("""
            CREATE INDEX idx_users_role ON users(role)
        """)
        
        # Add check constraint for valid roles
        cursor.execute("""
            ALTER TABLE users ADD CONSTRAINT check_user_role 
            CHECK (role IN ('public', 'government', 'developer', 'analyst'))
        """)
        
        print("✅ Users table created successfully")
        print("   - Added email and role indexes for performance")
        print("   - Added role validation constraint")
        
    except Exception as e:
        print(f"❌ Error creating users table: {e}")
        raise e


def down(cursor):
    """Drop users table (rollback function)."""
    try:        
        # Drop table (indexes and constraints are dropped automatically)
        cursor.execute("DROP TABLE IF EXISTS users CASCADE")
        
        print("✅ Users table dropped successfully")
        
    except Exception as e:
        print(f"❌ Error dropping users table: {e}")
        raise e


if __name__ == "__main__":
    # Allow running migration directly for testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "down":
        down()
    else:
        up()
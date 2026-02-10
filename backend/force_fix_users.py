"""
Force clean users table by using explicit column selection from temp table
"""
from database_config import get_db_connection

def force_fix_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🔧 Force-fixing users table...")
        
        # Create completely new table with different name first
        print("   1. Creating new clean table (users_new)...")
        cursor.execute("DROP TABLE IF EXISTS users_new CASCADE")
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role VARCHAR(50) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                is_super_admin BOOLEAN DEFAULT FALSE,
                name VARCHAR(255),
                last_login TIMESTAMP,
                is_suspended BOOLEAN DEFAULT FALSE,
                suspended_at TIMESTAMP,
                suspended_reason TEXT,
                last_checked_notifications TIMESTAMP,
                CONSTRAINT check_user_role CHECK (role IN ('public', 'government', 'developer', 'analyst'))
            )
        """)
        
        # Copy data from old users table
        print("   2. Copying data from old users table...")
        cursor.execute("""
            INSERT INTO users_new (
                id, email, password_hash, role, is_active,
                created_at, updated_at, is_super_admin, name,
                last_login, is_suspended, suspended_at,
                suspended_reason, last_checked_notifications
            )
            SELECT DISTINCT ON (email)
                id::integer, 
                email::varchar, 
                password_hash::text, 
                role::varchar, 
                is_active::boolean,
                created_at::timestamp,
                updated_at::timestamp,
                is_super_admin::boolean,
                name::varchar,
                last_login::timestamp,
                is_suspended::boolean,
                suspended_at::timestamp,
                suspended_reason::text,
                last_checked_notifications::timestamp
            FROM users
            WHERE email IS NOT NULL
            ORDER BY email, created_at DESC
        """)
        
        count = cursor.rowcount
        print(f"   ✅ Copied {count} users")
        
        # Drop old table
        print("   3. Dropping old users table...")
        cursor.execute("DROP TABLE users CASCADE")
        
        # Rename new table
        print("   4. Renaming users_new to users...")
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        # Create sequence
        print("   5. Creating ID sequence...")
        cursor.execute("CREATE SEQUENCE IF NOT EXISTS users_id_seq")
        cursor.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users), true)")
        cursor.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq')")
        
        # Create indexes
        print("   6. Creating indexes...")
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX idx_users_role ON users(role)")
        
        conn.commit()
        
        print("\n✅ Users table forcefully fixed!")
        
        # Verify
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Final users table schema:")
        cols = cursor.fetchall()
        for idx, (col_name, data_type) in enumerate(cols, 1):
            print(f"   {idx:2d}. {col_name:30s} {data_type}")
        
        # Check for duplicates
        col_names = [c[0] for c in cols]
        duplicates = [name for name in set(col_names) if col_names.count(name) > 1]
        if duplicates:
            print(f"\n⚠️  Still has duplicates: {duplicates}")
        else:
            print(f"\n✅ SUCCESS! No duplicate columns!")
            print(f"   Total columns: {len(cols)}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    force_fix_users()

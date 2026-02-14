"""
Migration 010: Enhance users table with additional fields
- is_super_admin: For government admin control
- name: Display name
- last_login: Track last login timestamp
- is_suspended: Account suspension status
- Create hardcoded super user for demo
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection

# Import password hasher
try:
    from argon2 import PasswordHasher
    ph = PasswordHasher()
except ImportError:
    # Fallback if argon2 not available
    import hashlib
    class PasswordHasher:
        def hash(self, password):
            return hashlib.sha256(password.encode()).hexdigest()
    ph = PasswordHasher()


def up(cursor):
    """Enhance users table and create super user"""
    try:
        print("🔄 Enhancing users table...")

        # Add is_super_admin column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='is_super_admin'
                ) THEN
                    ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE;
                END IF;
            END $$;
        """)
        print("   ✅ Added is_super_admin column")

        # Add name column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='name'
                ) THEN
                    ALTER TABLE users ADD COLUMN name VARCHAR(255);
                END IF;
            END $$;
        """)
        print("   ✅ Added name column")

        # Add last_login column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='last_login'
                ) THEN
                    ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
                END IF;
            END $$;
        """)
        print("   ✅ Added last_login column")

        # Add is_suspended column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='is_suspended'
                ) THEN
                    ALTER TABLE users ADD COLUMN is_suspended BOOLEAN DEFAULT FALSE;
                END IF;
            END $$;
        """)
        print("   ✅ Added is_suspended column")

        # Add suspended_at column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='suspended_at'
                ) THEN
                    ALTER TABLE users ADD COLUMN suspended_at TIMESTAMP;
                END IF;
            END $$;
        """)
        print("   ✅ Added suspended_at column")

        # Add suspended_reason column
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='suspended_reason'
                ) THEN
                    ALTER TABLE users ADD COLUMN suspended_reason TEXT;
                END IF;
            END $$;
        """)
        print("   ✅ Added suspended_reason column")

        # Create hardcoded super user for demo
        super_user_email = 'admin@trafficsg.gov'
        super_user_password = ph.hash('SuperAdmin@2024')

        cursor.execute("""
            INSERT INTO users (email, password_hash, role, name, is_active, is_super_admin)
            VALUES (%s, %s, 'government', 'System Administrator', TRUE, TRUE)
            ON CONFLICT (email) DO UPDATE SET
                is_super_admin = TRUE,
                name = 'System Administrator';
        """, (super_user_email, super_user_password))
        print(f"   ✅ Created/updated super user: {super_user_email}")

        print("✅ Migration 010 completed successfully")

    except Exception as e:
        print(f"❌ Migration 010 failed: {e}")
        raise e


def down(cursor):
    """Remove added columns (rollback migration)"""
    try:
        print("🔄 Rolling back migration 010...")

        columns = ['is_super_admin', 'name', 'last_login', 'is_suspended',
                   'suspended_at', 'suspended_reason']

        for column in columns:
            cursor.execute(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='users' AND column_name='{column}'
                    ) THEN
                        ALTER TABLE users DROP COLUMN {column};
                    END IF;
                END $$;
            """)
            print(f"   ✅ Dropped {column} column")

        # Delete super user
        cursor.execute("DELETE FROM users WHERE email = 'admin@trafficsg.gov';")
        print("   ✅ Deleted super user")

        print("✅ Migration 010 rollback completed")

    except Exception as e:
        print(f"❌ Migration 010 rollback failed: {e}")
        raise e


if __name__ == "__main__":
    conn = get_db_connection()
    cursor = conn.cursor()

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        down(cursor)
    else:
        up(cursor)

    conn.commit()
    cursor.close()
    conn.close()

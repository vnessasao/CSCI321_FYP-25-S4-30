"""
Setup script to check database schema and grant super admin privileges.
This script will:
1. Check what columns exist in the users table
2. Add is_super_admin column if it doesn't exist
3. Grant super admin privileges to a government user
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from database_config import get_db_connection

def check_table_columns():
    """Check what columns exist in the users table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()
        cursor.close()
        conn.close()

        print("\n📋 Current columns in 'users' table:")
        print("-" * 60)
        print(f"{'Column Name':<30} {'Type':<20} {'Nullable'}")
        print("-" * 60)

        column_names = []
        for col in columns:
            column_name, data_type, is_nullable = col
            column_names.append(column_name)
            print(f"{column_name:<30} {data_type:<20} {is_nullable}")

        print("-" * 60)
        return column_names

    except Exception as e:
        print(f"❌ Error checking columns: {str(e)}")
        return []

def add_missing_columns():
    """Add missing columns to the users table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # List of columns that should exist
        required_columns = {
            'is_super_admin': 'BOOLEAN DEFAULT FALSE',
            'name': 'VARCHAR(255)',
            'last_login': 'TIMESTAMP',
            'is_suspended': 'BOOLEAN DEFAULT FALSE',
            'suspended_at': 'TIMESTAMP',
            'suspended_reason': 'TEXT'
        }

        print("\n🔄 Checking and adding missing columns...")

        for column_name, column_type in required_columns.items():
            # Check if column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'users' AND column_name = %s
                );
            """, (column_name,))

            exists = cursor.fetchone()[0]

            if not exists:
                print(f"   ➕ Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type};")
                conn.commit()
                print(f"   ✅ Added column: {column_name}")
            else:
                print(f"   ✓ Column already exists: {column_name}")

        cursor.close()
        conn.close()

        print("✅ All required columns are present")
        return True

    except Exception as e:
        print(f"❌ Error adding columns: {str(e)}")
        return False

def grant_super_admin(email):
    """Grant super admin privileges to a user."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            print(f"\n❌ Error: User with email '{email}' not found.")
            print("\n📋 Available government users:")

            cursor.execute("""
                SELECT id, email, role
                FROM users
                WHERE role = 'government'
                ORDER BY id;
            """)
            gov_users = cursor.fetchall()

            if gov_users:
                print("-" * 60)
                for u in gov_users:
                    print(f"   ID: {u[0]}, Email: {u[1]}, Role: {u[2]}")
                print("-" * 60)
            else:
                print("   No government users found.")

            cursor.close()
            conn.close()
            return False

        user_id, user_email, user_role = user
        print(f"\n✓ Found user: ID={user_id}, Email={user_email}, Role={user_role}")

        # Update user to be super admin
        cursor.execute(
            "UPDATE users SET is_super_admin = TRUE WHERE id = %s",
            (user_id,)
        )
        conn.commit()

        # Verify the change
        cursor.execute(
            "SELECT id, email, role, is_super_admin FROM users WHERE id = %s",
            (user_id,)
        )
        updated_user = cursor.fetchone()

        cursor.close()
        conn.close()

        if updated_user and updated_user[3]:
            print(f"\n✅ SUCCESS! User '{user_email}' now has super admin privileges.")
            print(f"   - User ID: {updated_user[0]}")
            print(f"   - Email: {updated_user[1]}")
            print(f"   - Role: {updated_user[2]}")
            print(f"   - Super Admin: {updated_user[3]}")
            return True
        else:
            print(f"\n❌ Failed to grant super admin privileges.")
            return False

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔐 Super Admin Setup Tool")
    print("=" * 60)

    # Step 1: Check current table structure
    print("\n[Step 1/3] Checking database schema...")
    column_names = check_table_columns()

    if not column_names:
        print("\n❌ Failed to check database schema. Exiting.")
        sys.exit(1)

    # Step 2: Add missing columns if needed
    if 'is_super_admin' not in column_names:
        print("\n[Step 2/3] Adding missing columns...")
        if not add_missing_columns():
            print("\n❌ Failed to add missing columns. Exiting.")
            sys.exit(1)
    else:
        print("\n[Step 2/3] All required columns present. Skipping.")

    # Step 3: Grant super admin privileges
    print("\n[Step 3/3] Granting super admin privileges...")

    # Get email from command line or prompt
    if len(sys.argv) > 1:
        email = sys.argv[1].strip().lower()
    else:
        print("\n📧 Enter the email of the government user:")
        print("   (or press Enter to use 'admin@trafficsg.gov')")
        email = input("   Email: ").strip().lower()

        if not email:
            email = "admin@trafficsg.gov"

    print(f"\n🔄 Processing: {email}")
    print("-" * 60)

    success = grant_super_admin(email)

    if success:
        print("\n" + "=" * 60)
        print("🎉 Setup complete! You can now:")
        print("   1. Login with the super admin account")
        print("   2. Access the Manage Users page")
        print("   3. Create and manage other users")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Setup failed. Please check the error messages above.")
        print("=" * 60)
        sys.exit(1)

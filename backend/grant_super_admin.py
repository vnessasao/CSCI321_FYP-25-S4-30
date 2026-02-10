"""
Script to grant super admin privileges to a government user.
This allows the user to access the user management features.
"""

import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(__file__))

from database_config import get_db_connection

def grant_super_admin(email):
    """Grant super admin privileges to a user by email."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id, email, role FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            print(f"❌ Error: User with email '{email}' not found.")
            cursor.close()
            conn.close()
            return False

        user_id, user_email, user_role = user
        print(f"📋 Found user: ID={user_id}, Email={user_email}, Role={user_role}")

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
            print(f"✅ Success! User '{user_email}' now has super admin privileges.")
            print(f"   - User ID: {updated_user[0]}")
            print(f"   - Email: {updated_user[1]}")
            print(f"   - Role: {updated_user[2]}")
            print(f"   - Super Admin: {updated_user[3]}")
            print("\n🎉 You can now access the Manage Users page!")
            return True
        else:
            print(f"❌ Error: Failed to grant super admin privileges.")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def list_government_users():
    """List all government users."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, email, name, is_super_admin
            FROM users
            WHERE role = 'government'
            ORDER BY id
        """)
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        if not users:
            print("No government users found in the database.")
            return []

        print("\n👥 Government Users:")
        print("-" * 80)
        print(f"{'ID':<6} {'Email':<35} {'Name':<25} {'Super Admin'}")
        print("-" * 80)

        for user in users:
            user_id, email, name, is_super_admin = user
            name_str = name if name else "N/A"
            admin_str = "✅ Yes" if is_super_admin else "❌ No"
            print(f"{user_id:<6} {email:<35} {name_str:<25} {admin_str}")

        print("-" * 80)
        return users

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return []

if __name__ == "__main__":
    print("=" * 80)
    print("🔐 Super Admin Grant Tool")
    print("=" * 80)

    # List all government users first
    users = list_government_users()

    if not users:
        print("\n❌ No government users found. Please create a government user first.")
        sys.exit(1)

    # Get email from command line or prompt
    if len(sys.argv) > 1:
        email = sys.argv[1].strip().lower()
    else:
        print("\n📧 Enter the email of the government user to grant super admin privileges:")
        print("   (or press Enter to use 'government@gmail.com')")
        email = input("   Email: ").strip().lower()

        if not email:
            email = "government@gmail.com"

    print(f"\n🔄 Granting super admin privileges to: {email}")
    print("-" * 80)

    success = grant_super_admin(email)

    if success:
        print("\n" + "=" * 80)
        print("✨ All done! Refresh the Manage Users page to see the changes.")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ Failed to grant super admin privileges.")
        print("=" * 80)
        sys.exit(1)

"""Check feedback table structure and test update"""
from database_config import get_db_connection

def check_feedback_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check table structure
        print("\n=== FEEDBACK TABLE STRUCTURE ===")
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'feedback'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[0]:<25} {col[1]:<20} {col[2]}")
        
        # Show recent feedback with status
        print("\n=== RECENT FEEDBACK (Last 10) ===")
        cursor.execute("""
            SELECT id, subject, message, status, admin_response, 
                   responded_at, created_at
            FROM feedback
            ORDER BY created_at DESC
            LIMIT 10;
        """)
        feedbacks = cursor.fetchall()
        
        for fb in feedbacks:
            print(f"\nID: {fb[0]}")
            print(f"  Subject: {fb[1]}")
            print(f"  Message: {fb[2][:50]}...")
            print(f"  Status: {fb[3]}")
            print(f"  Response: {fb[4][:50] if fb[4] else 'None'}...")
            print(f"  Responded At: {fb[5]}")
            print(f"  Created At: {fb[6]}")
        
        # Test if we can update status
        print("\n=== TESTING STATUS UPDATE ===")
        cursor.execute("""
            SELECT id, status FROM feedback 
            WHERE status = 'pending' 
            LIMIT 1;
        """)
        test_record = cursor.fetchone()
        
        if test_record:
            test_id = test_record[0]
            old_status = test_record[1]
            print(f"Found feedback ID {test_id} with status '{old_status}'")
            print("Attempting to update status to 'resolved'...")
            
            cursor.execute("""
                UPDATE feedback
                SET status = 'resolved',
                    admin_response = 'Test response',
                    responded_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, status;
            """, (test_id,))
            
            result = cursor.fetchone()
            if result:
                print(f"✓ Successfully updated! ID: {result[0]}, New Status: {result[1]}")
                
                # Rollback to not affect real data
                conn.rollback()
                print("(Changes rolled back - this was just a test)")
            else:
                print("✗ Update failed!")
        else:
            print("No pending feedback found to test with")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_feedback_table()

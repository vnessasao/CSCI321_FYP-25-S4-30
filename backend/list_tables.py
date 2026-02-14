from database_config import get_db_connection

def list_all_tables():
    """Query and display all tables in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query to get all tables in the public schema
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """
        
        cursor.execute(query)
        tables = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("TABLES IN THE DATABASE")
        print("=" * 60)
        
        if tables:
            for idx, table in enumerate(tables, 1):
                print(f"{idx:2d}. {table[0]}")
            print("=" * 60)
            print(f"Total tables: {len(tables)}")
        else:
            print("No tables found in the database.")
        
        print("=" * 60 + "\n")
        
        cursor.close()
        conn.close()
        
        return tables
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return []

if __name__ == "__main__":
    list_all_tables()

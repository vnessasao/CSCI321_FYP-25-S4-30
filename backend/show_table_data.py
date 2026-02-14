from database_config import get_db_connection
import json

def print_table_data():
    """Display first 3 records from every table in the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        print("\n" + "=" * 80)
        print("DATABASE TABLES - FIRST 3 RECORDS")
        print("=" * 80)
        
        for table in tables:
            table_name = table[0]
            
            # Skip PostGIS system tables
            if table_name in ['spatial_ref_sys', 'geography_columns', 'geometry_columns']:
                continue
            
            print(f"\n{'─' * 80}")
            print(f"TABLE: {table_name.upper()}")
            print('─' * 80)
            
            try:
                # Get column names
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """)
                columns = [col[0] for col in cursor.fetchall()]
                
                # Get first 3 records
                cursor.execute(f'SELECT * FROM {table_name} LIMIT 3;')
                records = cursor.fetchall()
                
                if records:
                    print(f"Columns: {', '.join(columns)}")
                    print()
                    
                    for idx, record in enumerate(records, 1):
                        print(f"Record {idx}:")
                        for col_name, value in zip(columns, record):
                            # Format the value for better display
                            if value is None:
                                display_value = "NULL"
                            elif isinstance(value, (dict, list)):
                                display_value = json.dumps(value, indent=2)
                            elif isinstance(value, str) and len(str(value)) > 100:
                                display_value = str(value)[:100] + "..."
                            else:
                                display_value = str(value)
                            
                            print(f"  {col_name}: {display_value}")
                        print()
                else:
                    print("  (No records found)")
                    print()
                    
            except Exception as e:
                print(f"  Error reading table: {e}")
                print()
        
        print("=" * 80)
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print_table_data()

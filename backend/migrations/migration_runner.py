"""
Migration runner for traffic bottleneck system.
Handles database schema migrations in order.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add parent directory to path to import database_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_config import get_db_connection


class MigrationRunner:
    """Handles running database migrations in order."""
    
    def __init__(self):
        self.migrations_dir = Path(__file__).parent
        
    def create_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create migrations table to track applied migrations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            print("✅ Migrations table created/verified")
            
        except Exception as e:
            print(f"❌ Error creating migrations table: {e}")
            raise e
    
    def get_applied_migrations(self):
        """Get list of already applied migrations."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT migration_name FROM migrations ORDER BY applied_at")
            applied = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return applied
            
        except Exception as e:
            print(f"❌ Error getting applied migrations: {e}")
            return []
    
    def get_pending_migrations(self):
        """Get list of migrations that haven't been applied yet."""
        applied = self.get_applied_migrations()
        
        # Get all .py files in migrations directory (except this file)
        migration_files = []
        for file in self.migrations_dir.glob("*.py"):
            if file.name != "__init__.py" and file.name != "migration_runner.py":
                migration_files.append(file.stem)
        
        # Sort migration files
        migration_files.sort()
        
        # Filter out already applied migrations
        pending = [m for m in migration_files if m not in applied]
        
        return pending
    
    def run_migration(self, migration_name):
        """Run a single migration."""
        try:
            # Import and run the migration
            migration_file = self.migrations_dir / f"{migration_name}.py"
            
            spec = importlib.util.spec_from_file_location(migration_name, migration_file)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Run the migration
            if hasattr(migration_module, 'up'):
                print(f"🔄 Running migration: {migration_name}")
                
                conn = get_db_connection()
                cursor = conn.cursor()
                migration_module.up(cursor)
                # Mark migration as applied
                cursor.execute(
                    "INSERT INTO migrations (migration_name) VALUES (%s)",
                    (migration_name,)
                )
                conn.commit()
                cursor.close()
                conn.close()
                
                print(f"✅ Migration {migration_name} completed successfully")
            else:
                print(f"❌ Migration {migration_name} has no 'up' function")
                
        except Exception as e:
            print(f"❌ Error running migration {migration_name}: {e}")
            raise e
    
    def run_all_pending(self):
        """Run all pending migrations."""
        try:
            # Ensure migrations table exists
            self.create_migrations_table()
            
            pending = self.get_pending_migrations()
            
            if not pending:
                print("✅ No pending migrations")
                return
            
            print(f"📋 Found {len(pending)} pending migration(s):")
            for migration in pending:
                print(f"   - {migration}")
            
            # Run each pending migration
            for migration in pending:
                self.run_migration(migration)
            
            print(f"✅ All {len(pending)} migration(s) completed successfully")
            
        except Exception as e:
            print(f"❌ Migration process failed: {e}")
            raise e
    
    def status(self):
        """Show migration status."""
        try:
            self.create_migrations_table()
            
            applied = self.get_applied_migrations()
            pending = self.get_pending_migrations()
            
            print("📊 Migration Status:")
            print(f"   Applied: {len(applied)}")
            print(f"   Pending: {len(pending)}")
            
            if applied:
                print("\n✅ Applied migrations:")
                for migration in applied:
                    print(f"   - {migration}")
            
            if pending:
                print("\n⏳ Pending migrations:")
                for migration in pending:
                    print(f"   - {migration}")
            
        except Exception as e:
            print(f"❌ Error getting migration status: {e}")


def main():
    """CLI interface for migration runner."""
    runner = MigrationRunner()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migration_runner.py migrate    - Run all pending migrations")
        print("  python migration_runner.py status     - Show migration status")
        return
    
    command = sys.argv[1]
    
    if command == "migrate":
        runner.run_all_pending()
    elif command == "status":
        runner.status()
    else:
        print("❌ Invalid command")


if __name__ == "__main__":
    main()
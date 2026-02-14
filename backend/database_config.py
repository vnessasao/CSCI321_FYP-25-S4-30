import os
from dotenv import load_dotenv
import psycopg

class DatabaseConfig:
    """Loads DB credentials from .env and manages DB connections."""

    def __init__(self):
        # Load .env variables into environment
        load_dotenv()

        # Fetch credentials
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.dbname = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        # Basic validation to avoid silent bugs
        if not all([self.host, self.port, self.dbname, self.user, self.password]):
            raise ValueError("Missing one or more required database environment variables.")

    def get_db_connection(self):
        """Returns a fresh psycopg connection."""
        conn = psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        # Set timezone to local system timezone
        cursor = conn.cursor()
        cursor.execute("SET timezone = 'Asia/Singapore'")
        cursor.close()
        return conn

    def init_db(self):
        """Attempts to connect once to verify DB is reachable."""
        try:
            conn = self.get_db_connection()
            conn.close()
        except Exception as e:
            raise e


# Singleton-style usage
db = DatabaseConfig()

def get_db_connection():
    """Convenience wrapper for the rest of your app."""
    return db.get_db_connection()

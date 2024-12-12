import psycopg2
from src.config.database_config import DatabaseConfig

def get_connection():
    """Create a new database connection"""
    try:
        return psycopg2.connect(
            host=DatabaseConfig.HOST,
            database=DatabaseConfig.DATABASE,
            user=DatabaseConfig.USER,
            password=DatabaseConfig.PASSWORD,
            port=DatabaseConfig.PORT
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def test_connection():
    """Test the database connection"""
    try:
        conn = get_connection()
        print("Successfully connected to the database!")
        conn.close()
        return True
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return False

def release_connection(conn):
    """
    Properly close a database connection
    
    Args:
        conn: The database connection to close
    """
    if conn is not None:
        try:
            conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")

if __name__ == "__main__":
    # You can run this file directly to test the connection
    test_connection()
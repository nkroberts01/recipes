import psycopg2
from config.database_config import DatabaseConfig

def create_database():
    """Create the recipe_manager database"""
    # Connect to default PostgreSQL database
    conn = psycopg2.connect(
        host=DatabaseConfig.HOST,
        database='postgres',
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD,
        port=DatabaseConfig.PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Create database if it doesn't exist
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'recipe_manager'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute('CREATE DATABASE recipe_manager')
            print("Database created successfully!")
        else:
            print("Database already exists.")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        cursor.close()
        conn.close()

def init_tables():
    """Initialize database tables"""
    conn = psycopg2.connect(DatabaseConfig.get_connection_string())
    cursor = conn.cursor()
    
    try:
        # Create tables
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            url TEXT,
            prep_time VARCHAR(50),
            cook_time VARCHAR(50),
            total_time VARCHAR(50),
            servings VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ingredients (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER REFERENCES recipes(id) ON DELETE CASCADE,
            section VARCHAR(50),
            quantity VARCHAR(50),
            unit VARCHAR(50),
            name VARCHAR(255),
            additional TEXT
        );
        """)
        
        conn.commit()
        print("Tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_database()
    init_tables()
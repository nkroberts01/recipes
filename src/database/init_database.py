from mimetypes import init
import psycopg2
from src.config.db_connection import get_connection
from src.config.database_config import DatabaseConfig

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

def init_tables(connection):
    with connection.cursor() as cursor:
        # Create recipes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                url TEXT,
                prep_time INTEGER,
                cook_time INTEGER,
                total_time INTEGER,
                servings VARCHAR(10)
            );
        """)
        
        # Create ingredients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id SERIAL PRIMARY KEY,
                recipe_id INT REFERENCES recipes(id) ON DELETE CASCADE,
                section VARCHAR(50),
                quantity VARCHAR(50),
                unit VARCHAR(50),
                name VARCHAR(255),
                additional TEXT
            );
        """)
        
        # Create trigger function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_total_time()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.total_time = COALESCE(NEW.prep_time, 0) + COALESCE(NEW.cook_time, 0);
                IF NEW.prep_time IS NULL AND NEW.cook_time IS NULL THEN
                    NEW.total_time = NULL;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Create trigger
        cursor.execute("""
            DROP TRIGGER IF EXISTS calculate_total_time ON recipes;
            CREATE TRIGGER calculate_total_time
                BEFORE INSERT OR UPDATE OF prep_time, cook_time
                ON recipes
                FOR EACH ROW
                EXECUTE FUNCTION update_total_time();
        """)
        
        connection.commit()

if __name__ == "__main__":
    create_database()
    init_tables(get_connection())
from src.config.database_config import DatabaseConfig
from src.config.db_connection import get_connection, test_connection
from src.database.queries import insert_recipe, get_recipes

def test():
    print("Testing connection...")
    test_connection()

if __name__ == "__main__":
    test()
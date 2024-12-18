from src.config.db_connection import get_connection, release_connection
from src.models.recipe import Recipe
from src.models.ingredient import Ingredient
from typing import List, Optional

class RecipeRepository:
    """
    Repository class for handling all database operations related to recipes and ingredients.
    """
    
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        """
        Retrieve a recipe and its ingredients by ID.
        
        Args:
            recipe_id (int): The ID of the recipe to retrieve
            
        Returns:
            Optional[Recipe]: Recipe object if found, None otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get recipe details
            cursor.execute("""
                SELECT id, title, url, prep_time, cook_time, total_time, servings
                FROM recipes
                WHERE id = %s
            """, (recipe_id,))
            
            recipe_data = cursor.fetchone()
            if not recipe_data:
                return None
                
            # Get all ingredients for this recipe
            cursor.execute("""
                SELECT section, quantity, unit, name, additional
                FROM ingredients
                WHERE recipe_id = %s
                ORDER BY section, id
            """, (recipe_id,))
            
            ingredients_data = cursor.fetchall()
            
            # Organize ingredients by section
            ingredients_dict = {}
            for ing_data in ingredients_data:
                section, quantity, unit, name, additional = ing_data
                if section not in ingredients_dict:
                    ingredients_dict[section] = []
                    
                ingredient = Ingredient(
                    name=name,
                    quantity=quantity,
                    unit=unit,
                    additional=additional,
                    section=section
                )
                ingredients_dict[section].append(ingredient)
            
            # Create Recipe object
            recipe = Recipe(
                id=recipe_data[0],
                title=recipe_data[1],
                url=recipe_data[2],
                prep_time=recipe_data[3],
                cook_time=recipe_data[4],
                total_time=recipe_data[5],
                servings=recipe_data[6],
                ingredients=ingredients_dict
            )
            
            return recipe
            
        finally:
            cursor.close()
            release_connection(conn)

    def get_recipes(self, limit: int = 10, offset: int = 0) -> List[Recipe]:
        """
        Retrieve a list of recipes with pagination.
        
        Args:
            limit (int): Maximum number of recipes to return
            offset (int): Number of recipes to skip
            
        Returns:
            List[Recipe]: List of Recipe objects
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Get paginated recipe IDs
            cursor.execute("""
                SELECT id
                FROM recipes
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            recipe_ids = cursor.fetchall()
            
            # Fetch complete recipe data for each ID
            recipes = []
            for (recipe_id,) in recipe_ids:
                recipe = self.get_recipe_by_id(recipe_id)
                if recipe:
                    recipes.append(recipe)
                    
            return recipes
            
        finally:
            cursor.close()
            release_connection(conn)

    def search_recipes(
        self,
        query: Optional[str] = None,
        max_prep_time: Optional[int] = None,
        limit: int = 10
    ) -> List[Recipe]:
        """
        Search recipes based on various criteria.
        
        Args:
            query (Optional[str]): Search term to match against recipe titles
            max_prep_time (Optional[int]): Maximum preparation time in minutes
            limit (int): Maximum number of recipes to return
            
        Returns:
            List[Recipe]: List of matching Recipe objects
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            base_query = """
                SELECT DISTINCT r.id 
                FROM recipes r
                WHERE 1=1
            """
            params = []
            
            if query:
                base_query += " AND r.title ILIKE %s"
                params.append(f"%{query}%")
            
            if max_prep_time:
                # Note: This assumes prep_time is stored in a format that can be converted to minutes
                base_query += " AND REGEXP_REPLACE(r.prep_time, '[^0-9]', '', 'g')::integer <= %s"
                params.append(max_prep_time)
            
            base_query += " LIMIT %s"
            params.append(limit)
            
            cursor.execute(base_query, params)
            recipe_ids = cursor.fetchall()
            
            return [
                recipe
                for recipe_id in recipe_ids
                if recipe_id[0] is not None
                for recipe in [self.get_recipe_by_id(recipe_id[0])]
                if recipe is not None
            ]
            
        finally:
            cursor.close()
            release_connection(conn)

    def insert_recipe(self, recipe_data: dict) -> Optional[int]:
        """
        Insert a new recipe and its ingredients into the database.
        
        Args:
            recipe_data (dict): Dictionary containing recipe details and ingredients
            
        Returns:
            Optional[int]: ID of the inserted recipe if successful, None otherwise
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            # Insert the recipe and get its ID - removed total_time from the INSERT
            cursor.execute(
                """
                INSERT INTO recipes (title, url, prep_time, cook_time, servings)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    recipe_data['title'],
                    recipe_data['url'],
                    recipe_data['prep_time'],
                    recipe_data['cook_time'],
                    recipe_data['servings']
                )
            )
            
            result = cursor.fetchone()
            if result is None:
                raise Exception("No recipe ID returned from insert")
                
            recipe_id = result[0]

            # Insert each ingredient associated with the recipe
            for section, ingredients in recipe_data['ingredients'].items():
                for ingredient in ingredients:
                    cursor.execute(
                        """
                        INSERT INTO ingredients (recipe_id, section, quantity, unit, name, additional)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            recipe_id,
                            section,
                            ingredient['quantity'],
                            ingredient['unit'],
                            ingredient['name'],
                            ingredient['additional']
                        )
                    )

            conn.commit()
            return recipe_id

        except Exception as e:
            print(f"Error inserting recipe and ingredients: {e}")
            conn.rollback()
            return None
            
        finally:
            cursor.close()
            release_connection(conn)
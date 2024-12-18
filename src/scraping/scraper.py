import requests
import time
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from src.database.queries import RecipeRepository
from src.models.recipe import Recipe
from src.models.ingredient import Ingredient

def get_recipe_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    recipe_cards = soup.select('a.comp.mntl-card-list-items.mntl-universal-card.mntl-document-card.mntl-card.card.card--no-image')
    
    recipe_links = []
    for card in recipe_cards:
        if 'href' in card.attrs:
            recipe_links.append(card['href'])
            print(f"Found recipe: {card['href']}")
    
    return recipe_links

def convert_to_minutes(time_str: str) -> Optional[int]:
    """
    Convert time string to minutes, returning None for invalid/not found values.
    
    Args:
        time_str: String representation of time (e.g., "45 minutes", "1 hour", "Not Found")
        
    Returns:
        Optional[int]: Number of minutes, or None if invalid/not found
    """
    if not time_str or time_str == 'Not Found':
        return None
    
    # Remove any extra whitespace and convert to lowercase
    time_str = time_str.strip().lower()
    
    try:
        # Handle hours
        if 'hour' in time_str or 'hr' in time_str:
            hours = int(re.findall(r'\d+', time_str)[0])
            return hours * 60
        # Handle minutes
        elif 'min' in time_str:
            return int(re.findall(r'\d+', time_str)[0])
        # Handle bare numbers (assume minutes)
        elif re.findall(r'\d+', time_str):
            return int(re.findall(r'\d+', time_str)[0])
    except (IndexError, ValueError):
        return None
        
    return None



def scrape_recipe(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # get name of recipe
    title_element = soup.find('h1', class_='article-heading text-headline-400')
    if title_element is None:
        print("Could not find title element")
        title = "Unknown Title"
    else:
        title = title_element.get_text().strip()

    # get details (prep_time, cook_time, # of servings)
    details_container = soup.find('div', class_='mm-recipes-details')
    prep_time = cook_time = servings = None

    if details_container:
        # Find each detail item
        for item in details_container.find_all('div', class_='mm-recipes-details__item'):
            label_div = item.find('div', class_='mm-recipes-details__label')
            value_div = item.find('div', class_='mm-recipes-details__value')
            
            if label_div and value_div:
                label = label_div.get_text().strip()
                value = value_div.get_text().strip()
                
                if 'Prep Time:' in label:
                    prep_time = convert_to_minutes(value)
                elif 'Cook Time:' in label:
                    cook_time = convert_to_minutes(value)
                elif 'Servings:' in label:
                    servings = value

    # get ingredients
    ingredients = {}
    ingredient_items = soup.find('div', class_='mm-recipes-structured-ingredients')
    if ingredient_items:
        current_category = 'main'
        ingredients[current_category] = []
        for item in ingredient_items.find_all(['p', 'li']):
            if item.name == 'p' and 'mm-recipes-structured-ingredients__list-heading' in item.get('class', []):
                current_category = item.text.strip()
                ingredients[current_category] = []
            elif item.name == 'li' and 'mm-recipes-structured-ingredients__list-item' in item.get('class', []):
                quantity = item.find('span', attrs={'data-ingredient-quantity': 'true'})
                quantity = quantity.text.strip() if quantity else ''
                
                unit = item.find('span', attrs={'data-ingredient-unit': 'true'})
                unit = unit.text.strip() if unit else ''
                
                name = item.find('span', attrs={'data-ingredient-name': 'true'})
                name = name.text.strip() if name else ''
                
                additional = item.p.text.strip()
                additional = ' '.join(additional.split()[len(quantity.split()) + len(unit.split()) + len(name.split()):])
                
                ingredient = {
                    'quantity': quantity,
                    'unit': unit,
                    'name': name,
                    'additional': additional.strip()
                }
                ingredients[current_category].append(ingredient)

        if not ingredients['main']:
            del ingredients['main']

    return {
        'title': title,
        'url': url,
        'ingredients': ingredients,
        'prep_time': prep_time,
        'cook_time': cook_time,
        'servings': servings
    }

def scrape_and_store_recipes(
    start_url: str = 'https://www.allrecipes.com/recipes/16492/everyday-cooking/special-collections/allrecipes-allstars/',
    num_recipes: int = 50,
    delay: float = 1.0
) -> List[str]:
    """
    Scrape recipes from AllRecipes and store them in the database.
    
    Args:
        start_url (str): The starting URL to scrape recipes from
        num_recipes (int): Maximum number of recipes to scrape
        delay (float): Delay between requests in seconds
        
    Returns:
        List[str]: List of processed recipe titles
    """
    print(f"Starting recipe scraping process. Target: {num_recipes} recipes")
    
    # Initialize repository
    repo = RecipeRepository()
    processed_recipes = []
    errors = []
    
    try:
        # Get recipe links
        print("Fetching recipe links...")
        links = get_recipe_links(start_url)
        
        if not links:
            print("No recipe links found!")
            return []
            
        print(f"Found {len(links)} recipe links")
        
        # Process each link up to num_recipes
        for i, link in enumerate(links[:num_recipes]):
            try:
                print(f"\nProcessing recipe {i+1}/{num_recipes}: {link}")
                
                # Scrape the recipe
                recipe_data = scrape_recipe(link)
                if not recipe_data:
                    print(f"Failed to scrape recipe from {link}")
                    continue
                
                # Insert into database
                recipe_id = repo.insert_recipe(recipe_data)
                if recipe_id:
                    processed_recipes.append(recipe_data['title'])
                    print(f"Successfully stored recipe: {recipe_data['title']}")
                else:
                    print(f"Failed to store recipe: {recipe_data['title']}")
                
                # Respect the website by waiting between requests
                time.sleep(delay)
                
            except Exception as e:
                error_msg = f"Error processing {link}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                continue
        
    except Exception as e:
        print(f"Fatal error in scraping process: {str(e)}")
        
    finally:
        # Print summary
        print("\n=== Scraping Summary ===")
        print(f"Total recipes processed: {len(processed_recipes)}")
        print(f"Total errors: {len(errors)}")
        if errors:
            print("\nErrors encountered:")
            for error in errors[:5]:  # Show first 5 errors
                print(f"- {error}")
            if len(errors) > 5:
                print(f"...and {len(errors) - 5} more errors")
                
        return processed_recipes

if __name__ == "__main__":
    # Example usage:
    processed_recipes = scrape_and_store_recipes(
        num_recipes=100,  # Start with a small number for testing
        delay=0.5  # Be nice to the website
    )
    
    print("\nProcessed Recipes:")
    for title in processed_recipes:
        print(f"- {title}")
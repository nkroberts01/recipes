import requests
import time
from bs4 import BeautifulSoup
from src.database.queries import insert_recipe, get_recipes
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
    prep_time = cook_time = total_time = servings = 'Not Found'

    if details_container:
        # Find each detail item
        for item in details_container.find_all('div', class_='mm-recipes-details__item'):
            label_div = item.find('div', class_='mm-recipes-details__label')
            value_div = item.find('div', class_='mm-recipes-details__value')
            
            if label_div and value_div:
                label = label_div.get_text().strip()
                value = value_div.get_text().strip()
                
                if 'Prep Time:' in label:
                    prep_time = value
                elif 'Cook Time:' in label:
                    cook_time = value
                elif 'Total Time:' in label:
                    total_time = value
                elif 'Servings:' in label:
                    servings = value

    # get ingredients, organized by item (ex. sauce may be separate from meatballs)
    ingredients = {}
    ingredient_items = soup.find('div', class_='mm-recipes-structured-ingredients')
    if ingredient_items:
        current_category = 'main'
        ingredients[current_category] = []
        for item in ingredient_items.find_all(['p', 'li']):
            if item.name == 'p' and 'mm-recipes-structured-ingredients__list-heading' in item.get('class', []):
                current_category = item.text.strip()
                #print(current_category)
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
        'total_time': total_time,
        'servings': servings
    }

def main(main_url='https://www.allrecipes.com/recipes/16492/everyday-cooking/special-collections/allrecipes-allstars/', num_recipes=50):
    links = get_recipe_links(main_url)
    recipes = []
    for link in links[:num_recipes]:
        recipe = scrape_recipe(link)
        print(recipe)
        insert_recipe(recipe)
        recipes.append(recipe)
    return recipes

recipes = main()
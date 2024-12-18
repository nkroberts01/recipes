from typing import List, Dict, Set, Optional
import numpy as np
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')

@dataclass
class UserPreferences:
    """Class to hold user input preferences"""
    available_ingredients: Optional[List[str]] = None  # Ingredients user has
    max_time: Optional[int] = None          # Maximum total time in minutes
    excluded_ingredients: Optional[List[str]] = None   # Ingredients to avoid
    preferred_ingredients: Optional[List[str]] = None  # Ingredients they particularly like

class IngredientProcessor:
    """Handles ingredient text processing and similarity matching"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            ngram_range=(1, 2),  # Use both unigrams and bigrams
            min_df=1
        )
        self.ingredient_vectors = None
        self.processed_ingredients = []

    def preprocess_ingredient(self, text: str) -> str:
        """Clean and normalize ingredient text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove quantities and common unit words
        units = r'\d+\/?\d*\s*(?:cup|tablespoon|teaspoon|pound|ounce|oz|lb|g|kg|ml|c|tbsp|tsp|cups|tablespoons|teaspoons|pounds|ounces)s?\b'
        text = re.sub(units, '', text)
        
        # Remove parenthetical text
        text = re.sub(r'\([^)]*\)', '', text)
        
        # Remove common prep instructions
        prep_words = r'\b(?:chopped|diced|minced|sliced|grated|for serving|to serve|optional|to taste)\b'
        text = re.sub(prep_words, '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        tokens = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token.isalnum() and token not in self.stop_words
        ]
        
        return ' '.join(tokens)

    def fit_transform_ingredients(self, ingredients: List[str]):
        """Process and vectorize a list of ingredients"""
        self.processed_ingredients = [self.preprocess_ingredient(ing) for ing in ingredients]
        self.ingredient_vectors = self.vectorizer.fit_transform(self.processed_ingredients)
        
    def transform_ingredients(self, ingredients: List[str]):
        """Transform new ingredients using existing vocabulary"""
        processed = [self.preprocess_ingredient(ing) for ing in ingredients]
        return self.vectorizer.transform(processed)

    def find_similar_ingredients(self, query: str, threshold: float = 0.3) -> List[tuple]:
        """Find similar ingredients above similarity threshold"""
        processed_query = self.preprocess_ingredient(query)
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate cosine similarity
        similarities = (self.ingredient_vectors @ query_vector.T).toarray().flatten()
        
        # Get ingredients above threshold
        similar = [
            (self.processed_ingredients[i], similarities[i])
            for i in range(len(similarities))
            if similarities[i] > threshold
        ]
        
        return sorted(similar, key=lambda x: x[1], reverse=True)

class EnhancedRecipeRecommender:
    def __init__(self, recipe_repository):
        self.recipe_repository = recipe_repository
        self.ingredient_processor = IngredientProcessor()
        self.initialize_ingredient_vectors()
    
    def get_recipe_ingredients(self, recipe) -> Set[str]:
        """Extract all ingredient names from a recipe."""
        ingredients = set()
        for section in recipe.ingredients.values():
            for ingredient in section:
                # Convert ingredient name to lowercase for better matching
                ingredients.add(ingredient.name.lower())
        return ingredients

    def initialize_ingredient_vectors(self):
        """Initialize the ingredient processor with all ingredients from the database"""
        all_recipes = self.recipe_repository.get_recipes(limit=1000)
        all_ingredients = set()
        
        # Collect all unique ingredients
        for recipe in all_recipes:
            for section in recipe.ingredients.values():
                for ingredient in section:
                    all_ingredients.add(ingredient.name)
        
        # Process and vectorize all ingredients
        self.ingredient_processor.fit_transform_ingredients(list(all_ingredients))

    def calculate_ingredient_similarity(self, user_ingredients: List[str], recipe_ingredients: Set[str]) -> float:
        """Calculate similarity score between user ingredients and recipe ingredients"""
        matches = 0
        total_recipe_ingredients = len(recipe_ingredients)
        
        for user_ing in user_ingredients:
            similar_ingredients = self.ingredient_processor.find_similar_ingredients(user_ing)
            
            # Check if any similar ingredients are in the recipe
            for recipe_ing in recipe_ingredients:
                recipe_similar = self.ingredient_processor.find_similar_ingredients(recipe_ing)
                
                # If any similar ingredients match with high similarity, count it
                if any(sim[1] > 0.5 for sim in similar_ingredients):
                    matches += 1
                    break
        
        return matches / total_recipe_ingredients if total_recipe_ingredients > 0 else 0.0

    def calculate_recipe_score(self, recipe, preferences: UserPreferences, ingredient_score: float) -> Dict:
        """Calculate overall recipe score based on various factors"""
        scores = {
            'ingredient_match': ingredient_score,
            'time_score': 0.0,
            'preference_score': 0.0,
            'exclusion_penalty': 0.0,
            'total_score': 0.0
        }
        
        # Time score
        if preferences.max_time and recipe.total_time:
            if recipe.total_time <= preferences.max_time:
                scores['time_score'] = 1.0
            else:
                time_diff = recipe.total_time - preferences.max_time
                scores['time_score'] = max(0, 1 - (time_diff / preferences.max_time))
        
        # Preference score
        if preferences.preferred_ingredients:
            recipe_ingredients = self.get_recipe_ingredients(recipe)
            preferred = set(ing.lower() for ing in preferences.preferred_ingredients)
            matches = recipe_ingredients.intersection(preferred)
            scores['preference_score'] = len(matches) / len(preferred) if preferred else 0
        
        # Exclusion penalty
        if preferences.excluded_ingredients:
            recipe_ingredients = self.get_recipe_ingredients(recipe)
            excluded = set(ing.lower() for ing in preferences.excluded_ingredients)
            matches = recipe_ingredients.intersection(excluded)
            scores['exclusion_penalty'] = len(matches)
        
        # Calculate total score with weights
        weights = {
            'ingredient_match': 0.4,
            'time_score': 0.3,
            'preference_score': 0.3,
            'exclusion_penalty': -1.0
        }
        
        scores['total_score'] = (
            scores['ingredient_match'] * weights['ingredient_match'] +
            scores['time_score'] * weights['time_score'] +
            scores['preference_score'] * weights['preference_score'] +
            scores['exclusion_penalty'] * weights['exclusion_penalty']
        )
        
        return scores

    def get_recommendations(
        self,
        preferences: UserPreferences,
        num_recommendations: int = 5
    ) -> List[Dict]:
        """Get recommendations with enhanced ingredient matching"""
        all_recipes = self.recipe_repository.get_recipes(limit=1000)
        scored_recipes = []
        
        for recipe in all_recipes:
            recipe_ingredients = self.get_recipe_ingredients(recipe)
            
            # Calculate ingredient similarity using NLP
            ingredient_score = self.calculate_ingredient_similarity(
                preferences.available_ingredients,
                recipe_ingredients
            ) if preferences.available_ingredients else 0.0
            
            # Calculate overall score
            scores = self.calculate_recipe_score(recipe, preferences, ingredient_score)
            
            if scores['total_score'] > 0:
                scored_recipes.append({
                    'recipe': recipe,
                    'scores': scores,
                    'matching_ingredients': self.get_matching_ingredients(
                        preferences.available_ingredients or [],
                        recipe_ingredients
                    )
                })
        
        scored_recipes.sort(key=lambda x: x['scores']['total_score'], reverse=True)
        return scored_recipes[:num_recommendations]

    def get_matching_ingredients(self, user_ingredients: List[str], recipe_ingredients: Set[str]) -> Dict[str, List[str]]:
        """Get detailed ingredient matches for explanation"""
        matches = {}
        for user_ing in user_ingredients:
            similar = []
            for recipe_ing in recipe_ingredients:
                similarity = self.ingredient_processor.find_similar_ingredients(recipe_ing)
                if similarity and similarity[0][1] > 0.3:
                    similar.append(recipe_ing)
            if similar:
                matches[user_ing] = similar
        return matches
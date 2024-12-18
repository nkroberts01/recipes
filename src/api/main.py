from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from src.database.queries import RecipeRepository
from src.models.recipe import Recipe
from src.recommender.recipe_recommender import EnhancedRecipeRecommender, UserPreferences

app = FastAPI(title="Recipe Manager API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize repositories and recommender
recipe_repo = RecipeRepository()
recommender = EnhancedRecipeRecommender(recipe_repo)

# Pydantic models for recommendation endpoint
class RecommendationRequest(BaseModel):
    available_ingredients: Optional[List[str]] = None
    max_time: Optional[int] = None
    excluded_ingredients: Optional[List[str]] = None
    preferred_ingredients: Optional[List[str]] = None
    num_recommendations: Optional[int] = 5

class RecipeRecommendation(BaseModel):
    id: int
    title: str
    total_score: float
    prep_time: Optional[int]
    cook_time: Optional[int]
    total_time: Optional[int]
    matching_ingredients: dict
    url: Optional[str]

class RecommendationResponse(BaseModel):
    recommendations: List[RecipeRecommendation]

# Existing endpoints
@app.get("/")
async def root():
    return {"message": "Welcome to the Recipe Manager API"}

@app.get("/recipes", response_model=List[dict])
async def get_recipes(skip: int = 0, limit: int = 10):
    """Get a list of recipes with pagination"""
    try:
        recipes = recipe_repo.get_recipes(limit=limit, offset=skip)
        return [recipe.to_dict() for recipe in recipes if recipe]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recipes/{recipe_id}", response_model=dict)
async def get_recipe(recipe_id: int):
    """Get a specific recipe by ID"""
    try:
        recipe = recipe_repo.get_recipe_by_id(recipe_id)
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return recipe.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recipes/search", response_model=List[dict])
async def search_recipes(
    query: Optional[str] = None,
    max_prep_time: Optional[int] = None,
    limit: int = 10
):
    """Search recipes by title and/or max prep time"""
    try:
        recipes = recipe_repo.search_recipes(
            query=query,
            max_prep_time=max_prep_time,
            limit=limit
        )
        return [recipe.to_dict() for recipe in recipes if recipe]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New recommendation endpoint
@app.post("/recipes/recommend", response_model=RecommendationResponse)
async def get_recipe_recommendations(request: RecommendationRequest):
    """
    Get recipe recommendations based on user preferences.
    
    Example request:
    ```json
    {
        "available_ingredients": ["chicken", "garlic", "onion"],
        "max_time": 45,
        "excluded_ingredients": ["mushrooms"],
        "preferred_ingredients": ["chicken"],
        "num_recommendations": 3
    }
    ```
    """
    try:
        # Convert request to UserPreferences
        preferences = UserPreferences(
            available_ingredients=request.available_ingredients,
            max_time=request.max_time,
            excluded_ingredients=request.excluded_ingredients,
            preferred_ingredients=request.preferred_ingredients
        )
        
        # Get recommendations
        recommendations = recommender.get_recommendations(
            preferences=preferences,
            num_recommendations=request.num_recommendations or 5
        )
        
        # Format response
        response_data = {
            "recommendations": [
                {
                    "id": rec["recipe"].id,
                    "title": rec["recipe"].title,
                    "total_score": rec["scores"]["total_score"],
                    "prep_time": rec["recipe"].prep_time,
                    "cook_time": rec["recipe"].cook_time,
                    "total_time": rec["recipe"].total_time,
                    "matching_ingredients": rec["matching_ingredients"],
                    "url": rec["recipe"].url
                }
                for rec in recommendations
            ]
        }
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
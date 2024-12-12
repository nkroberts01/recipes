from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from src.database.queries import RecipeRepository
from src.models.recipe import Recipe

app = FastAPI(title="Recipe Manager API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recipe repository
recipe_repo = RecipeRepository()

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
        # You'll need to implement this method in your RecipeRepository
        recipes = recipe_repo.search_recipes(
            query=query,
            max_prep_time=max_prep_time,
            limit=limit
        )
        return [recipe.to_dict() for recipe in recipes if recipe]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
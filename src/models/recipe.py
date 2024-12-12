from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from src.models.ingredient import Ingredient

@dataclass
class Recipe:
    title: str
    url: Optional[str]
    prep_time: str
    cook_time: str
    total_time: str
    servings: str
    ingredients: Dict[str, List[Ingredient]]
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "total_time": self.total_time,
            "servings": self.servings,
            "ingredients": {
                section: [ing.to_dict() for ing in ingredients]
                for section, ingredients in self.ingredients.items()
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Recipe':
        ingredients = {
            section: [Ingredient.from_dict(ing) for ing in section_ingredients]
            for section, section_ingredients in data["ingredients"].items()
        }
        
        return cls(
            id=data.get("id"),
            title=data["title"],
            url=data.get("url"),
            prep_time=data["prep_time"],
            cook_time=data["cook_time"],
            total_time=data["total_time"],
            servings=data["servings"],
            ingredients=ingredients,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
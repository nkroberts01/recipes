from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class Ingredient:
    name: str
    quantity: str
    unit: str
    additional: str = ""
    section: str = "main"
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "additional": self.additional,
            "section": self.section
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Ingredient':
        return cls(
            name=data["name"],
            quantity=data["quantity"],
            unit=data["unit"],
            additional=data.get("additional", ""),
            section=data.get("section", "main")
        )
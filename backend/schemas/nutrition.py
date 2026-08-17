from pydantic import BaseModel, Field
from typing import List,Optional
from datetime import datetime

class FoodNutrition(BaseModel):
    food_name: str = Field(...,description="Name of the food item")
    quantity: str = Field(...,description='Quantity of the food')
    calories: float = Field(...,ge=0,description="Calories in kcal")
    protein_g: float = Field(...,ge=0,description="Protein in grams")
    carbohydrates_g: float = Field(...,ge=0,description='Carbohydrates in grams')
    fat_g: float = Field(..., ge=0, description="Fat in grams")
    fiber_g: float = Field(..., ge=0, description="Fiber in grams")
    sugar_g: float = Field(..., ge=0, description="Sugar in grams")
    sodium_mg: float = Field(..., ge=0, description="Sodium in milligrams")
    is_estimated: bool = Field(default=True, description="Whether values are AI-estimated")

    class Config:
        json_scheme_extra = {
            "example": {
                "food_name": "Basmati Rice",
                "quantity": "180 g",
                "calories": 234.0,
                "protein_g": 4.9,
                "carbohydrates_g": 50.4,
                "fat_g": 0.4,
                "fiber_g": 0.7,
                "sugar_g": 0.1,
                "sodium_mg": 1.8,
                "is_estimated": True
            }
        }

class TotalNutrition(BaseModel):
    total_calories: float = Field(...,ge=0,description='Total calories in kcal')
    protein_g: float = Field(...,ge=0,description='Total protein in grams')
    carbohydrates_g: float = Field(...,ge=0,description='Total carbohydrates in grams')
    fat_g: float = Field(..., ge=0, description="Total fat in grams")
    fiber_g: float = Field(..., ge=0, description="Total fiber in grams")
    sugar_g: float = Field(..., ge=0, description="Total sugar in grams")
    sodium_mg: float = Field(..., ge=0, description="Total sodium in milligrams")

    class Config:
        json_schema_extra = {
            "example": {
                "total_calories": 520.0,
                "protein_g": 31.0,
                "carbohydrates_g": 58.0,
                "fat_g": 18.0,
                "fiber_g": 7.0,
                "sugar_g": 5.2,
                "sodium_mg": 450.0
            }
        }

class NutritionResponse(BaseModel):
    food_nutrition: List[FoodNutrition] = Field(...,description='Nutrition per food item')
    total_nutrition: TotalNutrition = Field(...,description='Aggregated meal nutrition')
    disclaimer: str = Field(
        default='Nutritional values are estimates based on image analysis.'
                'Actual values may vary. Not suitable for medical or dietary planning purpose.',
                description='Disclaimer about estimation accuracy'
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow,description='Analysis timestamp')
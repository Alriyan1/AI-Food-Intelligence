from pydantic import BaseModel,Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class DifficultyLevel(str,Enum):
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'


class DietType(str,Enum):
    VEGETARIAN = "vegetarian"
    NON_VEGETARIAN = "non_vegetarian"
    VEGAN = "vegan"
    EGGETARIAN = "eggetarian"

class FitnessGoal(str,Enum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"

class CuisineType(str,Enum):
    INDIAN = "indian"
    CHINESE = "chinese"
    ITALIAN = "italian"
    MEXICAN = "mexican"
    ANY = "any"

class Ingredient(BaseModel):
    name: str = Field(...,description='Ingredient name')
    quantity: str = Field(..., description="Ingredient quantity (e.g., '200 g)")
    unit: str = Field(default="",description='Unit of measurement')

class RecipeStep(BaseModel):
    step_number: int = Field(..., ge=1, description="Step number")
    instruction: str = Field(..., description="Cooking instruction")

class Recipe(BaseModel):
    recipe_id: str = Field(...,description="Unique recipe identifier")
    name: str = Field(...,description="Recipe name")
    description: str = Field(..., description='Short recipe description')
    ingredients: List[Ingredient] = Field(..., description="List of ingredients")
    instructions: List[RecipeStep] = Field(..., description='Step-by-step instructions')
    prep_time_minutes: int = Field(..., ge=0, description="Preparation time in minutes")
    cook_time_minutes: int = Field(..., ge=0, description="Cooking time in minutes")
    difficulty: DifficultyLevel = Field(..., description="Recipe difficulty")
    servings: int = Field(default=2, ge=1, description="Number of servings")
    calories_per_serving: float = Field(..., ge=0, description="Calories per serving")
    protein_g: float = Field(..., ge=0, description="Protein per serving in grams")
    carbohydrates_g: float = Field(..., ge=0, description="Carbs per serving in grams")
    fat_g: float = Field(..., ge=0, description="Fat per serving in grams")
    fiber_g: float = Field(..., ge=0, description="Fiber per serving in grams")
    tags: List[str] = Field(default_factory=list, description="Recipe tags")
    is_personalized: bool = Field(default=True, description="Whether recipe is personalized")

    class Config:
        json_schema_extra = {
            "example": {
                "recipe_id": "rec_001",
                "name": "Healthy Chicken Stir-Fry",
                "description": "A protein-rich stir-fry with vegetables",
                "ingredients": [
                    {"name": "Chicken Breast", "quantity": "200", "unit": "g"},
                    {"name": "Bell Peppers", "quantity": "100", "unit": "g"}
                ],
                "instructions": [
                    {"step_number": 1, "instruction": "Cut chicken into cubes"},
                    {"step_number": 2, "instruction": "Stir-fry vegetables"}
                ],
                "prep_time_minutes": 15,
                "cook_time_minutes": 20,
                "difficulty": "easy",
                "servings": 2,
                "calories_per_serving": 320.0,
                "protein_g": 28.0,
                "carbohydrates_g": 18.0,
                "fat_g": 12.0,
                "fiber_g": 4.0,
                "tags": ["high-protein", "low-carb"]
            }
        }

class UserPreferences(BaseModel):
    diet: DietType = Field(default=DietType.NON_VEGETARIAN,description='Dietary preference')
    goal: FitnessGoal = Field(default=FitnessGoal.MAINTENANCE, description='Fitness goal')
    cuisine: CuisineType = Field(default=CuisineType.ANY, description='Cuisine preferences')
    max_calories: Optional[int] = Field(default=None,ge=0,description="Maximum calories per meal")
    max_prep_time: Optional[int] = Field(default=None,ge=0,description="Maximum prep time in minutes")
    allergies: List[str] = Field(default_factory=list, description="List of allergens to avoid")
    excluded_ingredients: List[str] = Field(default_factory=list, description="Ingredients to exclude")

class RecipeGenerationRequest(BaseModel):
    detected_foods: List[str] = Field(...,description="List of detected food names")
    nutrition: dict = Field(..., description="Current meal nutrition")
    preferences: UserPreferences = Field(..., description="User dietary preferences")
    num_recipes: int = Field(default=3, ge=1, le=5, description="Number of recipes to generate")

class RecipeGenerationResponse(BaseModel):
    recipes: List[Recipe] = Field(..., description="List of generated recipes")
    timestamp: datetime = Field(default_factory=datetime.utcnow,description='Generation timestamp')
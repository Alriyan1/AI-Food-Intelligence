from pydantic import BaseModel, Field
from typing import List, Optional, Dict,Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str,Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

class BoundingBox(BaseModel):
    x_min:int
    y_min:int
    x_max:int
    y_max:int

    @property
    def width(self)->int:
        return self.x_max - self.x_min

    @property
    def height(self)->int:
        return self.y_max-self.y_min

    @property
    def area(self) -> int:
        return self.width * self.height

class DetectedFoodItem(BaseModel):
    food_id: str
    name: str
    confidence: float = Field(...,ge=0.0,le=1.0)
    bbox: Optional[BoundingBox] = None
    mask_area_pixels: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

class Ingredient(BaseModel):
    name: str
    confidence: float = Field(...,ge=0.0,le=1.0)
    source: str = Field(..., description='visual or inferred')

class PortionEstimate(BaseModel):
    weight_grams: Optional[float] = None
    weight_range_min: Optional[float] = None
    weight_range_max: Optional[float] = None
    confidence: ConfidenceLevel
    manual_override: bool = False
    user_selected_size: Optional[str] = None

class FoodAnalysis(BaseModel):
    detected_foods: List[DetectedFoodItem]
    Ingredients: List[Ingredient]
    portion: PortionEstimate
    image_quality_score: float
    processing_time_ms: float
    model_versions: Dict[str,str]
    warnings: List[str] = []

class NutritionData(BaseModel):
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    sugar: float
    sodium: float
    cholesterol: Optional[float] = None
    vitamin_a: Optional[float] = None
    vitamin_c: Optional[float] = None
    calcium: Optional[float] = None
    iron: Optional[float] = None
    potassium: Optional[float] = None

class NutritionEstimate(BaseModel):
    food_id: str
    food_name: str
    weight_grams: float
    nutrition: NutritionData
    confidence: float
    source: str
    source_id: str
    calculation_method: str
    uncertainty_range: Optional[Dict[str, float]] = None


class MealRecord(BaseModel):
    meal_id: Optional[str] = None
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    foods: List[NutritionEstimate]
    total_nutrition: NutritionData
    meal_type: str  # breakfast, lunch, dinner, snack
    notes: Optional[str] = None
    image_url: Optional[str] = None
    confidence_overall: float


class UserProfile(BaseModel):
    user_id: str
    diet: str = Field(..., description="vegetarian, non-vegetarian, vegan, etc.")
    preferred_cuisines: List[str] = ["Indian"]
    daily_calorie_target: float = 2200
    protein_target: float = 120
    carb_target: float = 250
    fat_target: float = 70
    fiber_target: float = 30
    allergies: List[str] = []
    excluded_foods: List[str] = []
    preferred_meal_types: List[str] = ["lunch", "dinner"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Recipe(BaseModel):
    recipe_id: str
    name: str
    ingredients: List[str]
    instructions: List[str]
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    nutrition_per_serving: NutritionData
    cuisine: str
    meal_type: List[str]
    dietary_tags: List[str]
    allergens: List[str]
    confidence: float


class Recommendation(BaseModel):
    item_id: str
    item_type: str  # recipe, food, alternative
    name: str
    score: float
    reason: str
    nutrition: Optional[NutritionData] = None
    metadata: Dict[str, Any] = {}


class APIResponse(BaseModel):
    success: bool
    request_id: str
    data: Optional[Any] = None
    error: Optional[str] = None
    warnings: List[str] = []
    confidence: Optional[Dict[str, float]] = None

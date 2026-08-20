import httpx
import re
from typing import List,Any,Optional,Tuple,Dict
from loguru import logger

from backend.schemas.food import DetectedFood
from backend.schemas.nutrition import FoodNutrition,TotalNutrition,NutritionResponse
from backend.config import settings


class NutritionService:

    USDA_API_BASE = "https://api.nal.usda.gov/fdc/v1"

    FOOD_KEYWORDS = {
        "rice": "rice",
        "chicken": "chicken",
        "beef": "beef",
        "fish": "fish",
        "bread": "bread",
        "pasta": "pasta",
        "salad": "salad",
        "soup": "soup",
        "curry": "curry",
        "vegetable": "vegetable",
        "fruit": "fruit",
        "milk": "milk",
        "cheese": "cheese",
        "egg": "egg",
        "potato": "potato",
        "bean": "bean",
        "lentil": "lentil",
        "tofu": "tofu",
        "paneer": "cheese",
        "roti": "bread",
        "naan": "bread",
        "chapati": "bread",
    }

    def __init__(self):
        self.api_key = getattr(settings,'USDA_API_KEY',None)
        self.timeout = settings.API_TIMEOUT_SECONDS

    async def calculate_nutrition(
            self,
            detected_foods: List[DetectedFood]
    ) -> NutritionResponse:

        food_nutrition_list = []

        for food in detected_foods:
            try:
                nutrition = await self._get_food_nutrition(food)
                food_nutrition_list.append(nutrition)
            
            except Exception as e:
                logger.error(f"Error calculating nutrition for {food.name}: {e}")
                nutrition = self._estimate_nutrition_fallback(food)
                food_nutrition_list.append(nutrition)

        total_nutrition = self._calculate_totals(food_nutrition_list)

        return NutritionResponse(
            food_nutrition=food_nutrition_list,
            total_nutrition=total_nutrition,
            disclaimer="Nutritional values are estimates based on image analysis and USDA database. "
                      "Actual values may vary based on ingredients, cooking methods, and portion sizes. "
                      "Not suitable for medical or precise dietary planning purposes."
        )
    async def _get_food_nutrition(self,food:DetectedFood)->FoodNutrition:
        quantity_grams = self._parse_quantity_to_grams(food.estimated_quantity)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            search_params = {
                "api_key": self.api_key if self.api_key else "DEMO_KEY",
                "query": food.name,
                "pageSize": 1,
                "sortBy": "dataType.keyword"
            }

            try:
                search_response = await client.get(
                    f"{self.USDA_API_BASE}/foods/search",
                    params=search_params
                )

                if search_response.status_code == 200:
                    search_data = search_response.json()
                    foods = search_data.get('foods',[])

                    if foods:
                        food_id = foods[0].get('fdcId')

                        detail_response = await client.get(
                            f"{self.USDA_API_BASE}/food/{food_id}",
                            params={'api_key':self.api_key if self.api_key else 'DEMO_KEY'}
                        )

                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            return self._parse_usda_response(detail_response,food,quantity_grams)

            except Exception as e:
                logger.warning(f"USDA API error for {food.name}: {e}")


        return self._estimate_nutrition_fallback(food)

    def _parse_usda_response(
            self,
            usda_data: Dict[str,Any],
            food: DetectedFood,
            quantity_grams: float
    ) -> FoodNutrition:

        nutrients = usda_data.get('foodNutrients',[])

        def get_nutrient_value(nutrient_name:str,default:float=0.0) -> float:

            for nut in nutrients:
                nutrient_data = nut.get('nutrient',{})
                if nutrient_name.lower() in nutrient_data.get('name',"").lower():
                    return nut.get('value',default)
            return default

        calories_per_100g = get_nutrient_value("Energy", 0)
        protein_per_100g = get_nutrient_value("Protein", 0)
        carbs_per_100g = get_nutrient_value("Carbohydrate", 0)
        fat_per_100g = get_nutrient_value("Total lipid (fat)", 0)
        fiber_per_100g = get_nutrient_value("Fiber", 0)
        sugar_per_100g = get_nutrient_value("Sugars", 0)
        sodium_per_100g = get_nutrient_value("Sodium", 0)

        scale_factor = quantity_grams / 100.0

        return FoodNutrition(
            food_name=food.name,
            quantity=food.estimated_quantity,
            calories=calories_per_100g * scale_factor,
            protein_g=protein_per_100g * scale_factor,
            carbohydrates_g=carbs_per_100g * scale_factor,
            fat_g=fat_per_100g * scale_factor,
            fiber_g=fiber_per_100g * scale_factor,
            sugar_g=sugar_per_100g * scale_factor,
            sodium_mg=sodium_per_100g * scale_factor,
            is_estimated=True
        )

    def _estimate_nutrition_fallback(self,food:DetectedFood)->FoodNutrition:

        quantity_grams = self._parse_quantity_to_grams(food.estimated_quantity)
        scale_factor = quantity_grams/100.0

        category = self._categorize_food(food.name)

        nutrition_profiles = {
            "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "sugar": 0.1, "sodium": 1},
            "chicken": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "sugar": 0, "sodium": 74},
            "beef": {"calories": 250, "protein": 26, "carbs": 0, "fat": 15, "fiber": 0, "sugar": 0, "sodium": 72},
            "fish": {"calories": 206, "protein": 22, "carbs": 0, "fat": 12, "fiber": 0, "sugar": 0, "sodium": 59},
            "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7, "sugar": 5, "sodium": 491},
            "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8, "sugar": 0.6, "sodium": 1},
            "vegetable": {"calories": 35, "protein": 2, "carbs": 7, "fat": 0.4, "fiber": 2.5, "sugar": 3, "sodium": 30},
            "fruit": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4, "sugar": 10, "sodium": 1},
            "cheese": {"calories": 402, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0, "sugar": 0.5, "sodium": 621},
            "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0, "sugar": 1.1, "sodium": 124},
            "potato": {"calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "fiber": 2.2, "sugar": 0.8, "sodium": 6},
            "bean": {"calories": 347, "protein": 21, "carbs": 63, "fat": 1.2, "fiber": 25, "sugar": 2, "sodium": 24},
            "curry": {"calories": 150, "protein": 8, "carbs": 10, "fat": 9, "fiber": 2, "sugar": 4, "sodium": 400},
            "default": {"calories": 150, "protein": 5, "carbs": 20, "fat": 6, "fiber": 2, "sugar": 3, "sodium": 200},
        }

        profile = nutrition_profiles.get(category,nutrition_profiles['default'])

        return FoodNutrition(
            food_name=food.name,
            quantity=food.estimated_quantity,
            calories=profile['calories']*scale_factor,
            protein_g=profile['protein']*scale_factor,
            carbohydrates_g=profile["carbs"] * scale_factor,
            fat_g=profile["fat"] * scale_factor,
            fiber_g=profile["fiber"] * scale_factor,
            sugar_g=profile["sugar"] * scale_factor,
            sodium_mg=profile["sodium"] * scale_factor,
            is_estimated=True
        )

    def _categorize_food(self,food_name:str)->str:
        food_lower = food_name.lower()

        for keyword, category in self.FOOD_KEYWORDS.items():
            if keyword in food_lower:
                return category

        return 'default'

    def _parse_quantity_to_grams(self,quantity_str:str)->float:

        quantity_str = quantity_str.lower().strip()

        numbers = re.findall(r"\d+(?:\.\d+)?",quantity_str)
        if not numbers:
            return 100.0

        value = float(numbers[0])

        # Determine unit and convert to grams
        if "kg" in quantity_str:
            return value * 1000
        elif "g" in quantity_str or "gram" in quantity_str:
            return value
        elif "cup" in quantity_str:
            return value * 240  # Approximate
        elif "tablespoon" in quantity_str or "tbsp" in quantity_str:
            return value * 15
        elif "teaspoon" in quantity_str or "tsp" in quantity_str:
            return value * 5
        elif "piece" in quantity_str or "pcs" in quantity_str:
            return value * 100  # Approximate
        elif "oz" in quantity_str or "ounce" in quantity_str:
            return value * 28.35
        elif "lb" in quantity_str or "pound" in quantity_str:
            return value * 453.6
        else:
            return value * 100  # Default assumption: value is in 100g units


    def _calculate_totals(self,food_nutrition_list: List[FoodNutrition])->TotalNutrition:

        return TotalNutrition(
            total_calories=sum(f.calories for f in food_nutrition_list),
            protein_g=sum(f.protein_g for f in food_nutrition_list),
            carbohydrates_g=sum(f.carbohydrates_g for f in food_nutrition_list),
            fat_g=sum(f.fat_g for f in food_nutrition_list),
            fiber_g=sum(f.fiber_g for f in food_nutrition_list),
            sugar_g=sum(f.sugar_g for f in food_nutrition_list),
            sodium_mg=sum(f.sodium_mg for f in food_nutrition_list)
        )


_nutrition_service_instance = None

def get_nutrition_service() -> NutritionService:
    global _nutrition_service_instance
    if _nutrition_service_instance is None:
        _nutrition_service_instance = NutritionService()
    return _nutrition_service_instance
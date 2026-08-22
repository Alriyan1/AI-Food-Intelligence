import json 
import uuid
import httpx
from typing import List,Dict,Any
from loguru import logger

from config import settings
from schemas.recipe import (
    Recipe,Ingredient,RecipeStep,DifficultyLevel,
    UserPreferences,RecipeGenerationResponse
)

from utils.prompts import RECIPE_GENERATION_PROMPT


class RecipeService:

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.model_name = settings.NVIDIA_MODEL_NAME
        self.api_base_url = settings.NVIDIA_API_BASE_URL
        self.timeout = settings.API_TIMEOUT_SECONDS


    async def generate_recipes(
            self,
            detected_foods: List[str],
            nutrition:Dict[str,Any],
            preferences: UserPreferences,
            num_recipes: int=3
    ) -> RecipeGenerationResponse:

        try:
            prompt = RECIPE_GENERATION_PROMPT.format(
                detected_foods=", ".join(detected_foods) if detected_foods else "Not specified",
                nutrition_info=json.dumps(nutrition,indent=2),
                diet=preferences.diet.value,
                goal=preferences.goal.value,
                cuisine=preferences.cuisine.value,
                max_calories=preferences.max_calories or "Not specified",
                max_prep_time=preferences.max_prep_time or "Not specified",
                allergies=", ".join(preferences.allergies) if preferences.allergies else "None",
                excluded_ingredients=", ".join(preferences.excluded_ingredients) if preferences.excluded_ingredients else "None",
                num_recipes=num_recipes
            )

            recipes_json = await self._call_llm(prompt)

            recipes_data = self._parse_recipes_response(recipes_json,preferences)

            return RecipeGenerationResponse(recipes=recipes_data)

        except Exception as e:
            logger.error("Recipe generation failed: {}", e)
            raise ValueError(f'Failed to generate recipes: {str(e)}')

    async def _call_llm(self,prompt:str)->str:

        headers = {
            'Authorization':f"Bearer {self.api_key}",
            'Content-Type':"application/json",
            'Accept':"application/json"
        }

        payload = {
            'model': self.model_name,
            'messages': [
                {
                    'role':'system',
                    'content':'You are a professional chef and nutritionist. Generate recipes in JSON format only.'
                },
                {
                    'role':'user',
                    'content':prompt
                }
            ],
            'temperature':0.7,
            'top_p':0.9,
            'max_token':2048,
            'stream':False
        }

        endpoint = f"{self.api_base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"NVIDIA API error: {response.status_code} - {response.text}")
                raise ValueError(f"LLM API error: {response.status_code}")

            result = response.json()
            return result.get('choices',[{}]).get('message',{}).get('content',"")

    def _parse_recipes_response(
            self,
            response_text: str,
            preferences: UserPreferences
    )-> List[Recipe]:

        json_str = self._extract_json_from_response(response_text)

        try:
            recipes_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse recipes JSON: {}", e)
            raise ValueError('Invalid recipe format from LLM')

        recipes = []
        for recipe_data in recipes_data:
            try:
                recipe = self._create_recipe(recipe_data, preferences)
                recipes.append(recipe)
            except Exception as e:
                logger.warning("Error parsing recipe: {}", e)
                continue

        return recipes

    def _create_recipe(self,recipe_data:Dict[str,Any],preferences: UserPreferences) -> Recipe:

        ingredients = []
        for ing in recipe_data.get("ingredients", []):
            ingredients.append(
                Ingredient(
                    name=ing.get("name", "Unknown"),
                    quantity=ing.get("quantity", "1"),
                    unit=ing.get("unit", "")
                )
            )

        instructions = []
        for step in recipe_data.get("instructions", []):
            instructions.append(
                RecipeStep(
                    step_number=step.get("step_number", 1),
                    instruction=step.get("instruction", "")
                )
            )

        difficulty_str = recipe_data.get("difficulty", "medium").lower()
        difficulty = DifficultyLevel(difficulty_str) if difficulty_str in ["easy", "medium", "hard"] else DifficultyLevel.MEDIUM

        return Recipe(
            recipe_id=recipe_data.get("recipe_id", f"rec_{uuid.uuid4().hex[:8]}"),
            name=recipe_data.get("name", "Untitled Recipe"),
            description=recipe_data.get("description", "A delicious recipe"),
            ingredients=ingredients,
            instructions=instructions,
            prep_time_minutes=recipe_data.get("prep_time_minutes", 15),
            cook_time_minutes=recipe_data.get("cook_time_minutes", 20),
            difficulty=difficulty,
            servings=recipe_data.get("servings", 2),
            calories_per_serving=float(recipe_data.get("calories_per_serving", 400)),
            protein_g=float(recipe_data.get("protein_g", 20)),
            carbohydrates_g=float(recipe_data.get("carbohydrates_g", 40)),
            fat_g=float(recipe_data.get("fat_g", 15)),
            fiber_g=float(recipe_data.get("fiber_g", 5)),
            tags=recipe_data.get("tags", []),
            is_personalized=True
        ) 


    def _extract_json_from_response(self, text: str) -> str:

        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()

        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            return text[start:end]

        return text.strip()

_recipe_service_instance = None


def get_recipe_service() -> RecipeService:

    global _recipe_service_instance
    if _recipe_service_instance is None:
        _recipe_service_instance = RecipeService()
    return _recipe_service_instance
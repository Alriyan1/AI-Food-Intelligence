from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.schemas.recipe import (
    RecipeGenerationRequest,
    RecipeGenerationResponse,
    UserPreferences,
    DietType,
    FitnessGoal,
    CuisineType
)

from backend.services.recipe_service import get_recipe_service

router = APIRouter(prefix="/api/generate-recipes",tags=['Recipe Generation'])

@router.post(
    "",
    response_model=dict,
    summary="Generate personalized recipes",
    description='Generate recipes based on detected foods and user preferences'
)

async def generate_recipes(
    request: RecipeGenerationRequest
)-> dict:

    logger.info(f"Generating {request.num_recipes} recipes for user with {request.preferences.diet.value} diet")

    try:
        recipe_service = get_recipe_service()

        response: RecipeGenerationResponse = await recipe_service.generate_recipes(
            detected_foods=request.detected_foods,
            nutrition=request.nutrition,
            preferences=request.preferences,
            num_recipes=request.num_recipes
        )

        recipes_data = []
        for recipe in  response.recipes:
            recipes_data.append({
                'recipe_id':recipe.recipe_id,
                'name': recipe.name,
                'description':recipe.description,
                'ingredients':[
                    {'name':ing.name,'quantity':ing.quantity,'unit':ing.unit}
                    for ing in recipe.ingredients
                ],
                'instructions':[
                    {"step_number":step.step_number,'instruction':step.instruction}
                    for step in recipe.instructions
                ],
                "prep_time_minutes": recipe.prep_time_minutes,
                "cook_time_minutes": recipe.cook_time_minutes,
                "difficulty": recipe.difficulty.value,
                "servings": recipe.servings,
                "nutrition": {
                    "calories_per_serving": round(recipe.calories_per_serving, 1),
                    "protein_g": round(recipe.protein_g, 1),
                    "carbohydrates_g": round(recipe.carbohydrates_g, 1),
                    "fat_g": round(recipe.fat_g, 1),
                    "fiber_g": round(recipe.fiber_g, 1)
                },
                "tags": recipe.tags,
                "is_personalized": recipe.is_personalized
            })

        return {
            "success": True,
            "recipes": recipes_data,
            "timestamp": response.timestamp.isoformat()
            }

    except Exception as e:
        logger.error(f"Recipe generation failed: {e}",exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Recipe generation failed: {str(e)}"
        )

@router.post(
    '/quick',
    response_model=dict,
    summary='Quick recipe generation',
    description='Generate recipes with minimal parameters'
)

async def generate_recipes_quick(
    detected_foods:list[str],
    diet:str = 'non-vegetarian',
    max_calories: int = None,
    num_recipes:int = 3
)-> dict:

    try:
        preferences = UserPreferences(
            diet = DietType(diet),
            goal=FitnessGoal.MAINTENANCE,
            cuisine=CuisineType.ANY,
            max_calories=max_calories
        )

        request = RecipeGenerationRequest(
            detected_foods=detected_foods,
            nutrition={},
            preferences=preferences,
            num_recipes=num_recipes
        )

        return await generate_recipes(request)


    except Exception as e:
        logger.error(f"Quick recipe generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recipe generation failed: {str(e)}"
        )
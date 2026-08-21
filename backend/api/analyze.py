from fastapi import APIRouter, UploadFile, File, HTTPException,Form
from fastapi.responses import JSONResponse
from loguru import logger
import time

from backend.schemas.food import FoodAnalysisResponse
from backend.schemas.nutrition import NutritionResponse
from backend.services.image_processor import validate_image,preprocess_image,encode_image_to_base64
from backend.services.food_analyzer import get_food_analyzer
from backend.services.nutrition_service import get_nutrition_service

router = APIRouter(prefix='/api/analyse-food',tags=['Food Analysis'])

@router.post(
    "",
    response_model=dict,
    summary='Analyze food image',
    description='Upload a food image to detect food items and calculate nutrition'
)

async def analyze_food(
    image: UploadFile = File(...,description='Food image to analyze')
)-> dict:

    start_time = time.time()
    logger.info(f"Received food analysis request: {image.filename}")

    try:
        image_bytes = await image.read()

        is_valid, error_msg = validate_image(image_bytes,image.content_type)
        if not is_valid:
            logger.warning(f"Image validation failed: {error_msg}")
            raise HTTPException(status_code=400,detail=error_msg)

        processed_bytes, content_type = preprocess_image(image_bytes)

        image_base64 = encode_image_to_base64(processed_bytes)

        food_analyzer = get_food_analyzer()
        food_analysis: FoodAnalysisResponse = await food_analyzer.analyze_food_image(
            image_base64=image_base64,
            image_type=content_type
        )

        nutrition_service = get_nutrition_service()
        nutrition: NutritionResponse = await nutrition_service.calculate_nutrition(
            detected_foods=food_analysis.foods
        )

        response = {
            'success': True,
            'food_analysis':{
                'foods':[
                    {
                        'name':food.name,
                        'estimated_quantity':food.estimated_quantity,
                        'confidence': food.confidence
                    }
                    for food in food_analysis.foods
                ],
                'image_quality':food_analysis.image_quality,
                'processing_time_ms':food_analysis.processing_time_ms
            },
            'nutrition':{
                'food_nutrition':[
                    {
                        "food_name": fn.food_name,
                        "quantity": fn.quantity,
                        "calories": round(fn.calories, 1),
                        "protein_g": round(fn.protein_g, 1),
                        "carbohydrates_g": round(fn.carbohydrates_g, 1),
                        "fat_g": round(fn.fat_g, 1),
                        "fiber_g": round(fn.fiber_g, 1),
                        "sugar_g": round(fn.sugar_g, 1),
                        "sodium_mg": round(fn.sodium_mg, 1),
                        "is_estimated": fn.is_estimated
                    }
                    for fn in nutrition.food_nutrition
                ],
                'total_nutrition':{
                    "total_calories": round(nutrition.total_nutrition.total_calories, 1),
                    "protein_g": round(nutrition.total_nutrition.protein_g, 1),
                    "carbohydrates_g": round(nutrition.total_nutrition.carbohydrates_g, 1),
                    "fat_g": round(nutrition.total_nutrition.fat_g, 1),
                    "fiber_g": round(nutrition.total_nutrition.fiber_g, 1),
                    "sugar_g": round(nutrition.total_nutrition.sugar_g, 1),
                    "sodium_mg": round(nutrition.total_nutrition.sodium_mg, 1)
                },
                'disclaimer':nutrition.disclaimer
            },
            'timestamp': food_analysis.timestamp.isoformat()
        }

        total_time = time.time() - start_time
        logger.info(f"Food analysis completed in {total_time:.2f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Food analysis failed; {e}",exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Food analysis failed: {str(e)}"
        )
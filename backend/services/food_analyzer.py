import json
import time
import httpx
from typing import List, Dict, Any
from loguru import logger

from backend.config import settings
from backend.schemas.food import DetectedFood,FoodAnalysisResponse
from backend.utils.prompts import VISION_LLM_FOOD_DETECTION_PROMPT

class FoodAnalyzer:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.model_name = settings.NVIDIA_MODEL_NAME
        self.api_base_url = settings.NVIDIA_API_BASE_URL
        self.timeout = settings.API_TIMEOUT_SECONDS


    async def analyze_food_image(
            self,
            image_base64: str,
            image_type: str = "image/jpeg"
    ) -> FoodAnalysisResponse:

        start_time = time.time()

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Contact-Type": "application/json",
                'Accept': "application/json"
            }

            messages = [
                {
                    'role': 'user',
                    "content": f"{VISION_LLM_FOOD_DETECTION_PROMPT}[Image provided]"
                }
            ]

            payload = {
                'model': self.model_name,
                'messages': messages,
                'temperature': 0.1,
                'top_p': 0.7,
                'max_tokens': 1024,
                'stream': False
            }

            if hasattr(settings,'NVIDIA_VISION_ENDPOINT'):
                endpoint = settings.NVIDIA_VISION_ENDPOINT
            else:
                endpoint = f"{self.api_base_url}/chat/completions"

            logger.info(f"Sending request to NVIDIA NIM API: {endpoint}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"NVIDIA API error: {response.status_code} - {response.text}")

                    raise ValueError(f"NVIDIA API error: {response.status_code}")

                result = response.json()

            assistant_message = result.get('choice',[{}])[0].get('message',{}).get("content","")

            json_str = self._extract_json_from_response(assistant_message)

            if not json_str:
                logger.error(f"Could not extract JSON from response: {assistant_message[:200]}")
                raise ValueError('Invalid response format from Vision LLM')

            parsed_response = json.loads(json_str)

            detected_foods = []
            for food_item in parsed_response.get('foods',[]):
                if food_item.get('confidence',0)>0.3:
                    detected_foods.append(
                        DetectedFood(
                            name=food_item.get("name",'Unknown Food'),
                            estimated_quality=food_item.get('estimated_quantity','Unknown'),
                            confidence=float(food_item.get('confidence',0.5))
                        )
                    )

            processing_time_ms = int((time.time()-start_time)*1000)
            logger.info(f"Detected {len(detected_foods)} food items in {processing_time_ms}ms")

            return FoodAnalysisResponse(
                foods=detected_foods,
                image_quality=parsed_response.get('image_quality','good'),
                processing_time_ms=processing_time_ms
            )

        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling NVIDIA API: {e}")
            raise ValueError('Request timeout. Please try again.')
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise ValueError("Failed to parse Vision LLM response")
        except Exception as e:
            logger.error(f"Unexpected error in food analysis: {e}")
            raise ValueError(f"Food analysis failed: {str(e)}")


    def _extract_json_from_response(self,text:str)->str:

        if "```json" in text:
            start = text.find("```json")+7
            end = text.find("```",start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```")+3
            end = text.find("```",start)
            return text[start:end].strip()

        try:
            start = text.find("{")
            end = text.rfind("}")+1
            if start >= 0 and end > start:
                return text[start:end]

        except Exception:
            pass

        return text.strip()

_food_analyzer_instance = None

def get_food_analyzer() -> FoodAnalyzer:

    global _food_analyzer_instance
    if _food_analyzer_instance is None:
        _food_analyzer_instance = FoodAnalyzer()
    return _food_analyzer_instance
import json
import re
import time
import httpx
from typing import List, Dict, Any
from loguru import logger

from config import settings
from schemas.food import DetectedFood,FoodAnalysisResponse
from utils.prompts import VISION_LLM_FOOD_DETECTION_PROMPT

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
                "Content-Type": "application/json",
                'Accept': "application/json"
            }

            messages = [
                {
                    'role': 'user',
                    "content": [
                        {
                            "type": "text",
                            "text": VISION_LLM_FOOD_DETECTION_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]

            payload = {
                'model': self.model_name,
                'messages': messages,
                'temperature': 0.1,
                'top_p': 0.7,
                'max_tokens': 512,
                'stream': False
            }

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

            assistant_message = self._content_to_text(
                result.get('choices', [{}])[0].get('message', {}).get('content', '')
            )

            json_str = self._extract_json_from_response(assistant_message)

            if json_str:
                parsed_response = json.loads(json_str)
            else:
                parsed_response = self._parse_markdown_response(assistant_message)
                if not parsed_response:
                    logger.error(f"Could not extract JSON from response: {assistant_message[:200]}")
                    raise ValueError('Invalid response format from Vision LLM')

            detected_foods = []
            for food_item in parsed_response.get('foods',[]):
                if food_item.get('confidence',0)>0.3:
                    detected_foods.append(
                        DetectedFood(
                            name=food_item.get("name",'Unknown Food'),
                            estimated_quantity=food_item.get('estimated_quantity','Unknown'),
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
            logger.error("Timeout calling NVIDIA API: {}", e)
            raise ValueError('Request timeout. Please try again.')
        except json.JSONDecodeError as e:
            logger.error("JSON parsing error: {}", e)
            raise ValueError("Failed to parse Vision LLM response")
        except Exception as e:
            logger.error("Unexpected error in food analysis: {}", e)
            raise ValueError(f"Food analysis failed: {str(e)}")


    def _content_to_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            return "\n".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()

        return str(content).strip() if content else ""

    def _parse_markdown_response(self, text: str) -> Dict[str, Any]:
        foods = []
        block_pattern = re.compile(
            r"(?:^|\n)\s*[-*]\s*\*{0,2}Food Item\s*:\s*"
            r"\*{0,2}\s*([^*\n]+?)\s*\*{0,2}\s*\n"
            r"(.*?)(?=\n\s*[-*]\s*\*{0,2}Food Item\s*:|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        quantity_pattern = re.compile(
            r"Estimated\s+Quantity\s*:\s*\*{0,2}\s*"
            r"(\d+(?:\.\d+)?)\s*(g|kg|ml|cup|cups|piece|pieces)",
            re.IGNORECASE,
        )
        confidence_pattern = re.compile(
            r"Confidence\s*:\s*\*{0,2}\s*(0?\.\d+|1(?:\.0+)?)",
            re.IGNORECASE,
        )

        for match in block_pattern.finditer(text):
            quantity_match = quantity_pattern.search(match.group(2))
            confidence_match = confidence_pattern.search(match.group(2))
            if quantity_match and confidence_match:
                foods.append({
                    "name": match.group(1).strip(),
                    "estimated_quantity": f"{quantity_match.group(1)} {quantity_match.group(2)}",
                    "confidence": float(confidence_match.group(1)),
                })

        if foods:
            return {"foods": foods, "image_quality": "good"}

        inline_pattern = re.compile(
            r"(?:^|\n)\s*[-*]\s*\*{0,2}([^:*\n]+?)\*{0,2}\s*:\s*"
            r".*?(\d+(?:\.\d+)?)\s*(g|kg|ml|cup|cups|piece|pieces)"
            r".*?(?:confidence|score).*?(0?\.\d+|1(?:\.0+)?)",
            re.IGNORECASE,
        )

        for match in inline_pattern.finditer(text):
            quantity = f"{match.group(2)} {match.group(3)}"
            confidence = float(match.group(4))
            if 0.0 <= confidence <= 1.0:
                foods.append({
                    "name": match.group(1).strip(),
                    "estimated_quantity": quantity,
                    "confidence": confidence,
                })

        if not foods:
            return {}

        return {"foods": foods, "image_quality": "good"}

    def _extract_json_from_response(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""

        candidates = []
        if "```" in text:
            for block in text.split("```")[1::2]:
                candidates.append(block.removeprefix("json").strip())
        candidates.append(text)

        decoder = json.JSONDecoder()
        for candidate in candidates:
            try:
                decoder.raw_decode(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

            for index, character in enumerate(candidate):
                if character not in "[{":
                    continue
                try:
                    _, end = decoder.raw_decode(candidate[index:])
                    return candidate[index:index + end]
                except json.JSONDecodeError:
                    continue

        return ""

_food_analyzer_instance = None

def get_food_analyzer() -> FoodAnalyzer:

    global _food_analyzer_instance
    if _food_analyzer_instance is None:
        _food_analyzer_instance = FoodAnalyzer()
    return _food_analyzer_instance
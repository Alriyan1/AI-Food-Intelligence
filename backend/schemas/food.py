from pydantic import BaseModel, Field
from typing import List,Optional
from datetime import datetime

class DetectedFood(BaseModel):
    name: str = Field(..., description='Name of the detected food item')
    estimated_quantity: str = Field(..., description="Estimated quantity (e.g., '180 g')")
    confidence: float = Field(..., ge=0.0, le=1.0, description='Detection confidence score')

    class Config:
        json_schema_extra = {
            'example': {
                'name': 'Basmati Rice',
                'estimated_quantity': '180 g',
                'confidence': 0.91
            }
        }

class FoodAnalysisRequest(BaseModel):
    image_data: bytes = Field(..., description='Base64 encoded image data')
    image_type: str = Field(..., description="Image MIME type")

class FoodAnalysisResponse(BaseModel):
    foods: List[DetectedFood] = Field(..., description="List of detected food items")
    image_quality: str = Field(default='good',description='Quality assessment of the image')
    processing_time_ms: int = Field(..., description='Processing time in milliseconds')
    timestamp: datetime = Field(default_factory=datetime.utcnow,description='Analysis timestamp')

    class Config:
        json_schema_extra = {
            "example": {
                "foods": [
                    {
                        "name": "Basmati Rice",
                        "estimated_quantity": "180 g",
                        "confidence": 0.91
                    },
                    {
                        "name": "Chicken Curry",
                        "estimated_quantity": "150 g",
                        "confidence": 0.84
                    }
                ],
                "image_quality": "good",
                "processing_time_ms": 1250
            }
        }
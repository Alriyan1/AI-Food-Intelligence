from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):

    APP_NAME: str = "FoodVision AI"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    NVIDIA_API_KEY: str 
    NVIDIA_MODEL_NAME: str = "meta/llama-3.2-11b-vision-instruct"
    NVIDIA_API_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "foodvision_ai"

    ALLOWED_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:3000"]

    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    API_TIMEOUT_SECONDS: int = 60

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    
    return Settings()


settings = get_settings()
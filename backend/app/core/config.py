from pydantic_settings import BaseSettings
from typing import Optional,List
import os

class Settings(BaseSettings):
    APP_NAME: str = 'AI Food Intelligence'
    APP_VERSION: str = '1.0.0'
    DEBUG: bool = True

    API_V1_PREFIX: str = '/api/v1'

    SECRET_KEY: str = os.getenv('SECRET_KEY','secret-key-change-in-production')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = 'ai_food_intelligence'

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    YOLO_MODEL_PATH: str = os.getenv("SAM_MODEL_PATH", "models/sam_vit_h.pt")

    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4-vision-preview")
    LLM_TEMPERATURE: float = 0.3

    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "data/vector_db")

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    RATE_LIMIT_PER_MINUTE: int = 60
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
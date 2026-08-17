from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import asyncio
from loguru import logger

client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]

async def get_database():
    return db

async def init_indexes():
    await db.users.create_index('user_id',unique=True)
    await db.users.create_index('email',unique=True)

    await db.meals.create_index('user_id')
    await db.meals.create_index('timestamp')
    await db.meals.create_index('meal_type')
    await db.meals.create_index([('user_id',1),('timestamp',-1)])

    await db.food_items.create_index('food_id',unique=True)
    await db.food_items.create_index('name')
    await db.food_items.create_index('category')

    await db.recipes.create_index("recipe_id", unique=True)
    await db.recipes.create_index("name")
    await db.recipes.create_index("cuisine")

    await db.model_predictions.create_index("request_id")
    await db.model_predictions.create_index("user_id")
    await db.model_predictions.create_index("timestamp")

    logger.info('Database indexes initialized')

async def closed_database():
    client.close()
    logger.info('Database connection closed')
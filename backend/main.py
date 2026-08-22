from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
import time

from config import settings
from api import analyze, recipes,chat

logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)

app = FastAPI(
    title=settings.APP_NAME,
    description="""
## FoodVision AI - Your Multimodal Food & Nutrition Assistant

FoodVision AI uses computer vision and AI to:
- **Identify food items** from uploaded images
- **Estimate portions** and quantities
- **Calculate nutrition** using USDA database
- **Generate personalized recipes** based on your preferences
- **Answer questions** about food and nutrition

### Important Disclaimer
⚠️ **Nutritional values are estimates** based on image analysis. Actual values may vary.
This application is for informational purposes only and should not be used for medical or precise dietary planning.
""",
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc'
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"],
)

@app.middleware('http')
async def log_requests(request: Request,call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f'{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s'
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request,exc: Exception):
    logger.error(f"Unhandled exception: {exc}",exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            'success':False,
            'error': 'Internal server error',
            'detail': str(exc) if settings.DEBUG else 'An unexpected error occured'
        }
    )

app.include_router(analyze.router)
app.include_router(recipes.router)
app.include_router(chat.router)

@app.get(
    "/api/health",
    tags=["Health"],
    summary="Health check",
    description="Check API health status"
)
async def health_check():
    
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint",
    description="Welcome message and API information"
)
async def root():
    
    return {
        "service": settings.APP_NAME,
        "description": "Your Multimodal Food & Nutrition Assistant",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "analyze_food": "/api/analyze-food",
            "generate_recipes": "/api/generate-recipes",
            "chat": "/api/chat",
            "docs": "/docs"
        },
        "disclaimer": "Nutritional values are AI estimates. Not suitable for medical purposes."
    }

@app.on_event("startup")
async def startup_event():

    logger.info(f"Starting {settings.APP_NAME}...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")
    logger.info(f"{settings.APP_NAME} is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Shutting down {settings.APP_NAME}...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG
    )
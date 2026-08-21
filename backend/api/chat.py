from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import List,Optional,Dict,Any

from backend.schemas.chat import ChatRequest,ChatResponse,ChatMessage
from backend.services.chat_service import get_chat_service

router = APIRouter(prefix="/api/chat",tags=['Chat'])

@router.post(
    "",
    response_model=dict,
    summary='Chat with food assistant',
    description='Ask questions about food, nutrition, and recipes'
)

async def chat(
    request: ChatRequest
) -> dict:

    logger.info(f"Chat request received: {request.message[:100]}...")

    try: 
        chat_service = get_chat_service()

        response: ChatResponse = await chat_service.chat(
            message=request.message,
            food_analysis=request.food_analysis,
            nutrition=request.nutrition,
            preferences=request.preferences,
            conversation_history=request.conversation_history
        )

        return {
            "success": True,
            "response": response.response,
            "conversation_id": response.conversation_id,
            "suggestions": response.suggestions,
            "timestamp": response.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Chat failed: {e}",exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.post(
    '/simple',
    response_model=dict,
    summary='Simple chat endpoint',
    description="Quick chat without complex context"
)

async def chat_simple(
    message: str,
    conversation_history: Optional[List[Dict[str,str]]] = None
) -> dict:

    try: 
        history = []
        if conversation_history:
            for msg in conversation_history:
                history.append(
                    ChatMessage(
                        role=msg.get('role','user'),
                        content=msg.get('content',"")
                    )
                )

        request = ChatRequest(
            message=message,
            conversation_history=history
        )

        return await chat(request)

    except Exception as e:
        logger.error(f"Simple chat failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )
import json
import uuid
import httpx
from typing import List,Dict,Any,Optional
from loguru import logger

from config import settings
from schemas.chat import ChatMessage,ChatResponse
from utils.prompts import CHAT_ASSISTANT_PROMPT

class ChatService:

    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.model_name = settings.NVIDIA_MODEL_NAME
        self.api_base_url = settings.NVIDIA_API_BASE_URL
        self.timeout = settings.API_TIMEOUT_SECONDS

    async def chat(
            self,
            message: str,
            food_analysis: Optional[Dict[str,Any]]=None,
            nutrition: Optional[Dict[str,Any]]=None,
            preferences: Optional[Dict[str,Any]]=None,
            conversation_history: Optional[List[ChatMessage]]=None
    ) -> ChatResponse:

        try:
            context={
                'food_analysis': json.dumps(food_analysis,indent=2) if food_analysis else 'Not available',
                'nutrition': json.dumps(nutrition,indent=2) if nutrition else 'Not available',
                'preferences': json.dumps(preferences,indent=2) if preferences else 'Not specified',
                'conversation_history': self._format_conversation_history(conversation_history or []),
                'user_message': message
            }

            prompt = CHAT_ASSISTANT_PROMPT.format(**context)

            response_text = await self._call_llm(prompt)

            response_data = self._parse_chat_response(response_text)

            return ChatResponse(
                response = response_data.get('response',"I apologize, but i couldn't process your request. Please try again."),
                conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                suggestions=response_data.get('suggestions',[])
            )

        except Exception as e:
            logger.error("Chat processing failed: {}", e)
            raise ValueError(f"Chat failed: {str(e)}")


    async def _call_llm(self,prompt:str)->str:

        headers = {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json',
            'Accept': "application/json"
        }

        payload = {
            'model': self.model_name,
            'messages': [
                {
                    'role':'system',
                    'content':"You are FoodVision AI, a friendly food and nutrition assistant. Always respond in JSON format with 'response' and 'suggestions' fields."
                },
                {
                    'role':'user',
                    'content':prompt
                }
            ],
            'temperature':0.7,
            'top_p': 0.9,
            'max_tokens': 512,
            'stream': False
        }

        endpoint = f"{self.api_base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                logger.error(f"NVIDIA API error: {response.status_code} - {response.text}")
                raise ValueError(f"LLM API error: {response.status_code}")

            result = response.json()
            return result.get('choices',[{}])[0].get('message',{}).get('content',"")

    def _parse_chat_response(self,response_text:str)-> Dict[str,Any]:

        json_str = self._extract_json_from_response(response_text)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse chat JSON: {response_text[:200]}")
            return {
                    "responce": response_text.strip(),
                    "suggestions":[
                        'Can you explain more about this?',
                        'What are some alternatives?'
                    ]
                }

    def _format_conversation_history(self,history:List[ChatMessage])->str:

        if not history:
            return 'No previous conversation'

        formatted = []
        for msg in history[-5:]:
            formatted.append(f"{msg.role}: {msg.content}")

        return "\n".join(formatted)

    def _extracted_json_from_response(self,text:str)->str:

        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return text[start:end]

        return text.strip()


# Singleton instance
_chat_service_instance = None


def get_chat_service() -> ChatService:
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
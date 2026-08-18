from pydantic import BaseModel, Field
from typing import List,Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow,description='Message timestamp')

class ChatRequest(BaseModel):
    message: str = Field(...,description="User message")
    food_analysis: Optional[dict] = Field(default=None, description='Current nutrition context')
    preferences: Optional[dict] = Field(default=None,description="User preferences")
    conversation_history: List[ChatMessage] = Field(default_factory=list,description="Chat history")

class ChatResponse(BaseModel):
    response: str = Field(..., description='AI assistant response')
    conversation_id: str = Field(..., description="Conversation identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow,description='Response timestamp')
    suggestions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
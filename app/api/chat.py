"""
AI Beauty Muse - Chat API Routes
Handles AI-powered beauty chat assistant.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
)
from app.services.chat_service import chat_service


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with AI beauty assistant.
    
    - **message**: User's message
    - **image_url**: Optional image URL for context (e.g., selfie for analysis)
    - **conversation_history**: Optional previous conversation messages
    
    Returns:
    - AI assistant's reply
    - Follow-up suggestions
    """
    try:
        # Convert conversation history to list of dicts
        history = None
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ]
        
        result = await chat_service.chat(
            message=request.message,
            image_url=request.image_url,
            conversation_history=history,
        )
        
        return ChatResponse(
            reply=result.get("reply", ""),
            suggestions=result.get("suggestions"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/suggestions")
async def get_chat_suggestions():
    """
    Get initial chat suggestions for new conversations.
    
    Returns a list of suggested questions to start the conversation.
    """
    return {
        "suggestions": [
            "幫我分析一下我的臉型適合什麼髮型？",
            "今天穿什麼顏色比較好？",
            "我想換個髮色，有什麼推薦？",
            "約會妝容有什麼建議？",
            "我是梨形身材，怎麼穿搭比較好？",
            "幫我看看這套穿搭怎麼樣？",
        ]
    }

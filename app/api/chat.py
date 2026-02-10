"""
AI Beauty Muse - Chat API Routes (Session-based)
All chat endpoints require authentication.
Chat history is managed server-side via session_id.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.models.schemas import (
    ChatSessionCreate,
    ChatSessionInfo,
    ChatSessionListResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ChatHistoryResponse,
)
from app.dependencies import get_current_user
from app.services.chat_service import chat_service
from app.services.session_service import session_service


router = APIRouter(prefix="/chat", tags=["Chat"])


# ============== Session management ==============

@router.post("/sessions", response_model=ChatSessionInfo, status_code=201)
async def create_chat_session(
    request: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new chat session.

    Returns the session info (including the ``id`` to use in subsequent messages).
    """
    session = await session_service.create_session(
        db=db,
        user_id=current_user.id,
        title=request.title,
    )
    return ChatSessionInfo(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    offset: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List the current user's chat sessions, most-recent first.
    """
    sessions, total = await session_service.list_sessions(
        db=db,
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )
    return ChatSessionListResponse(
        sessions=[ChatSessionInfo(**s) for s in sessions],
        total=total,
    )


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the full message history of a session.
    """
    session = await session_service.get_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    history = await session_service.get_history(db, session_id, limit=200)
    messages = [
        ChatMessage(
            role=m["role"],
            content=m["content"],
            image_url=m.get("image_url"),
            created_at=m.get("created_at"),
        )
        for m in history
    ]
    return ChatHistoryResponse(
        session_id=session.id,
        title=session.title,
        messages=messages,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a chat session and all its messages.
    """
    deleted = await session_service.delete_session(db, session_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")


# ============== Chat messaging ==============

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message in an existing chat session.

    - **session_id**: ID of the chat session (create one first via ``POST /chat/sessions``)
    - **message**: User's text message
    - **image_url**: Optional image URL for visual context

    The server automatically loads conversation history from the session,
    calls AI, saves both user message and AI reply, then returns the result.
    """
    # 1. Validate session ownership
    session = await session_service.get_session(db, request.session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Auto-set title from first message
    await session_service.auto_title(db, session, request.message)

    # 3. Save user message
    await session_service.add_message(
        db=db,
        session_id=request.session_id,
        role="user",
        content=request.message,
        image_url=request.image_url,
    )

    # 4. Load history for OpenAI context
    history = await session_service.get_openai_history(db, request.session_id, limit=20)

    # 5. Call AI
    result = await chat_service.chat(
        message=request.message,
        image_url=request.image_url,
        conversation_history=history,
    )

    # 6. Save assistant reply
    await session_service.add_message(
        db=db,
        session_id=request.session_id,
        role="assistant",
        content=result["reply"],
    )

    return ChatResponse(
        session_id=request.session_id,
        reply=result["reply"],
        suggestions=result.get("suggestions"),
    )


# ============== Suggestions (public) ==============

@router.get("/suggestions")
async def get_chat_suggestions():
    """
    Get initial chat suggestions for new conversations.
    No authentication required.
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

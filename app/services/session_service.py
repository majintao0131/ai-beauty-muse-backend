"""
AI Beauty Muse - Chat Session Service
CRUD operations for chat sessions and message history stored in the database.
"""
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.database import ChatSession, ChatMessageRecord, generate_uuid


class SessionService:
    """Manages chat sessions and their messages."""

    # ---- Session CRUD -----------------------------------------------

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        title: Optional[str] = None,
    ) -> ChatSession:
        """Create a new chat session for a user."""
        session = ChatSession(
            id=generate_uuid(),
            user_id=user_id,
            title=title,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> Optional[ChatSession]:
        """
        Get a session by ID, ensuring it belongs to the given user.

        Returns:
            ChatSession or None if not found / not owned.
        """
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        db: AsyncSession,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List sessions for a user, ordered by most recent activity.

        Returns:
            (list_of_session_dicts, total_count)
        """
        # Total count
        count_result = await db.execute(
            select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Query sessions with message count
        stmt = (
            select(
                ChatSession,
                func.count(ChatMessageRecord.id).label("message_count"),
            )
            .outerjoin(ChatMessageRecord, ChatMessageRecord.session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id)
            .group_by(ChatSession.id)
            .order_by(ChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.all()

        sessions = []
        for row in rows:
            chat_session = row[0]
            msg_count = row[1]
            sessions.append({
                "id": chat_session.id,
                "title": chat_session.title,
                "created_at": chat_session.created_at,
                "updated_at": chat_session.updated_at,
                "message_count": msg_count,
            })

        return sessions, total

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> bool:
        """Delete a session (and cascade-delete its messages). Returns True if deleted."""
        session = await self.get_session(db, session_id, user_id)
        if session is None:
            return False
        await db.delete(session)
        await db.commit()
        return True

    # ---- Message CRUD -----------------------------------------------

    async def add_message(
        self,
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        image_url: Optional[str] = None,
    ) -> ChatMessageRecord:
        """Append a message to a session."""
        msg = ChatMessageRecord(
            session_id=session_id,
            role=role,
            content=content,
            image_url=image_url,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    async def get_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent ``limit`` messages for a session,
        returned in chronological order (oldest first).

        Returns:
            List of dicts with keys: role, content, image_url, created_at
        """
        stmt = (
            select(ChatMessageRecord)
            .where(ChatMessageRecord.session_id == session_id)
            .order_by(ChatMessageRecord.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        records = list(reversed(result.scalars().all()))

        return [
            {
                "role": r.role,
                "content": r.content,
                "image_url": r.image_url,
                "created_at": r.created_at,
            }
            for r in records
        ]

    async def get_openai_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 20,
    ) -> List[Dict[str, str]]:
        """
        Get history formatted for OpenAI ``messages`` parameter.
        Only includes role and content (no images, no timestamps).
        """
        history = await self.get_history(db, session_id, limit=limit)
        return [{"role": h["role"], "content": h["content"]} for h in history]

    async def auto_title(
        self,
        db: AsyncSession,
        session: ChatSession,
        first_message: str,
    ) -> None:
        """Set session title from first user message if title is empty."""
        if session.title:
            return
        # Truncate to first 50 chars
        session.title = first_message[:50] + ("..." if len(first_message) > 50 else "")
        await db.commit()


# Singleton
session_service = SessionService()

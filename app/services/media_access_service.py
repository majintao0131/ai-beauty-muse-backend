"""
Grants user access to media files for ownership verification.
Called when saving images so users can access them before the report is saved.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import UserMediaAccess


async def grant_media_access(db: AsyncSession, user_id: str, relative_path: str) -> None:
    """
    Record that a user can access a media file. Used when saving images
    so the user can view them before the report is saved.
    relative_path: e.g. "edited/xxx.png", "face/yyy.jpg"
    """
    existing = await db.execute(
        select(UserMediaAccess.id).where(
            UserMediaAccess.user_id == user_id,
            UserMediaAccess.path == relative_path,
        ).limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        return
    record = UserMediaAccess(user_id=user_id, path=relative_path)
    db.add(record)
    await db.commit()

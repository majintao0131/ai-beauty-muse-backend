"""
AI Beauty Muse - Protected Media API
Serves user-uploaded and AI-generated images with authentication and ownership verification.
Only users who own a report containing the image can access it.
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from sqlalchemy import select, or_

from app.config import settings
from app.dependencies import get_current_user
from app.models.database import get_db, ReportHistory, User, UserMediaAccess
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix="/media", tags=["Media"])

# Allowed subdirectories under upload_dir (no path traversal outside these)
ALLOWED_SUBDIRS = frozenset({"face", "beauty", settings.edited_images_subdir})


def _normalize_path(path: str) -> Optional[str]:
    """
    Normalize and validate path. Returns None if invalid.
    - Removes leading slashes and 'uploads/'
    - Rejects path traversal (..)
    - Ensures path is under an allowed subdir
    """
    p = path.strip().replace("\\", "/").lstrip("/")
    if p.startswith("uploads/"):
        p = p[len("uploads/"):]
    if ".." in p or p.startswith("/"):
        return None
    parts = p.split("/")
    if not parts or parts[0] not in ALLOWED_SUBDIRS:
        return None
    return p


@router.get("/{path:path}")
async def serve_media(
    path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取受保护的媒体文件（用户上传照片、AI 生成效果图等）。

    - **鉴权**：必须携带 `Authorization: Bearer <access_token>`
    - **归属校验**：仅当该图片出现在当前用户的某条历史报告中时，才允许访问
    - **路径格式**：`/api/v1/media/edited/xxx.png` 或 `/api/v1/media/face/xxx.jpg`

    若原 URL 为 `/uploads/edited/xxx.png`，则请求路径为 `/api/v1/media/edited/xxx.png`。
    """
    normalized = _normalize_path(path)
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid media path",
        )

    # Check ownership: user must have (1) a report referencing this image, or (2) explicit media access
    path_frag = normalized  # e.g. "edited/xxx.png"
    filename = path_frag.split("/")[-1]  # e.g. "xxx.png"

    has_access = False

    # 1) Check report_history
    stmt_report = select(ReportHistory.id).where(
        ReportHistory.user_id == current_user.id,
        or_(
            ReportHistory.thumbnail_url.like(f"%{path_frag}%"),
            ReportHistory.thumbnail_url.like(f"%{filename}%"),
            ReportHistory.data.like(f"%{path_frag}%"),
            ReportHistory.data.like(f"%{filename}%"),
        ),
    ).limit(1)
    if (await db.execute(stmt_report)).scalar_one_or_none() is not None:
        has_access = True

    # 2) Check user_media_access (for images saved before report exists)
    if not has_access:
        stmt_access = select(UserMediaAccess.id).where(
            UserMediaAccess.user_id == current_user.id,
            UserMediaAccess.path == path_frag,
        ).limit(1)
        if (await db.execute(stmt_access)).scalar_one_or_none() is not None:
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this resource",
        )

    file_path = Path(settings.upload_dir) / normalized
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Infer media type for Content-Type
    suffix = file_path.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )

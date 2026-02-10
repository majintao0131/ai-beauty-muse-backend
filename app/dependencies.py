"""
AI Beauty Muse - FastAPI Dependencies
Reusable dependency functions for authentication, database sessions, and quota checks.
"""
from typing import Optional, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.services.auth_service import auth_service
from app.services.quota_service import quota_service


# Bearer token extractor (auto_error=False → returns None if no token)
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    **Required** auth dependency.

    Extracts the Bearer JWT from the ``Authorization`` header, validates it,
    and returns the corresponding User.  Raises 401 if anything is wrong.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = auth_service.decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    **Optional** auth dependency.

    Same as ``get_current_user`` but returns ``None`` instead of raising
    when no token is provided.  Useful for endpoints that work for both
    anonymous and authenticated users.
    """
    if credentials is None:
        return None

    user_id = auth_service.decode_access_token(credentials.credentials)
    if user_id is None:
        return None

    return await auth_service.get_user_by_id(db, user_id)


def require_quota(feature: str) -> Callable:
    """
    Dependency factory that checks & consumes one usage quota unit.

    Usage in an endpoint::

        @router.post("/face-style")
        async def analyze_face_style(
            ...,
            quota_info: dict = Depends(require_quota("face_style")),
        ):
            # quota already consumed if we reach here
            ...

    Raises 403 if the monthly limit has been reached.
    """

    async def _check_and_consume(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        try:
            info = await quota_service.consume_quota(db, current_user, feature)
            return info
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )

    return _check_and_consume

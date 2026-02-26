"""
OAuth 回调与 Native 用 code 换 session。
与 APP 端 docs/oauth-config-example.md 约定一致：
- Web：门户重定向到 GET/POST /api/oauth/callback?code=...&state=...
- Native：APP 从 deep link 拿到 code/state 后请求 GET /api/oauth/mobile?code=...&state=...
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import get_db
from app.models.schemas import OAuthMobileResponse, OAuthMobileUserInfo
from app.services.oauth_service import (
    is_oauth_configured,
    get_web_redirect_uri,
    resolve_redirect_uri,
    exchange_code_for_token,
    get_userinfo,
    extract_oauth_id_from_token,
    extract_user_info,
)
from app.services.auth_service import auth_service
from app.services.membership_service import membership_service


router = APIRouter(prefix="/oauth", tags=["OAuth"])


def _ensure_oauth_configured() -> None:
    if not is_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="OAuth is not configured. Set OAUTH_SERVER_URL, OAUTH_APP_ID, OAUTH_APP_SECRET, OAUTH_ALLOWED_REDIRECT_URIS.",
        )


async def _oauth_login(db: AsyncSession, code: str, redirect_uri: str):
    """
    通用：用 code + redirect_uri 换 token，拉取 userinfo，创建/获取用户并签发 JWT。
    返回 (jwt_token, user) 或 (None, None) 表示失败。
    """
    token_resp = await exchange_code_for_token(code, redirect_uri)
    if not token_resp:
        return None, None
    access_token = token_resp.get("access_token")
    if not access_token:
        return None, None

    oauth_id = extract_oauth_id_from_token(token_resp)
    userinfo = await get_userinfo(access_token)
    if userinfo:
        oid, nickname, avatar_url = extract_user_info(userinfo)
        if oid:
            oauth_id = oid
    else:
        nickname = avatar_url = None

    if not oauth_id:
        return None, None

    user, _ = await auth_service.get_or_create_user_by_oauth(
        db,
        oauth_id=oauth_id,
        oauth_provider="portal",
        nickname=nickname,
        avatar_url=avatar_url,
    )
    await membership_service.get_status(db, user)
    jwt_token = auth_service.create_access_token(user_id=user.id)
    return jwt_token, user


@router.get("/callback")
@router.post("/callback")
async def oauth_callback_web(
    code: Optional[str] = Query(None, description="门户返回的授权码"),
    state: Optional[str] = Query(None, description="防 CSRF 的 state"),
    db: AsyncSession = Depends(get_db),
):
    """
    Web 登录回调。门户带着 code、state 重定向到此地址。
    后端用 code 向门户换 token，创建/绑定用户并签发 JWT，然后重定向到前端或返回 JSON。
    """
    _ensure_oauth_configured()
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    redirect_uri = get_web_redirect_uri()
    jwt_token, user = await _oauth_login(db, code, redirect_uri)
    if not jwt_token or not user:
        raise HTTPException(status_code=400, detail="Failed to exchange code or get user")

    success_url = settings.oauth_web_success_redirect
    if success_url:
        sep = "&" if "?" in success_url else "?"
        return RedirectResponse(url=f"{success_url}{sep}token={jwt_token}&user_id={user.id}", status_code=302)
    from fastapi.responses import JSONResponse
    return JSONResponse(content={
        "access_token": jwt_token,
        "token_type": "bearer",
        "user_id": user.id,
        "nickname": user.nickname,
        "is_member": user.is_membership_active,
    })


@router.get("/mobile", response_model=OAuthMobileResponse)
async def oauth_mobile(
    code: str = Query(..., description="门户返回的授权码（从 deep link 获得）"),
    state: Optional[str] = Query(None, description="防 CSRF 的 state"),
    redirect_uri: Optional[str] = Query(
        None,
        description="Native 时门户跳转的地址，即 deep link，如 manus20260203215119://oauth/callback。不传则使用 Web 回调地址。",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Native 用 code 换 session。APP 从 deep link 拿到 code/state 后请求此接口。
    返回 app_session_id（即 JWT），APP 存为 Bearer token 后续请求携带。
    """
    _ensure_oauth_configured()
    resolved = resolve_redirect_uri(redirect_uri)
    if not resolved:
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing redirect_uri. For Native login, pass redirect_uri equal to your app deep link (e.g. manus20260203215119://oauth/callback).",
        )
    jwt_token, user = await _oauth_login(db, code, resolved)
    if not jwt_token or not user:
        raise HTTPException(status_code=400, detail="Failed to exchange code or get user")

    return OAuthMobileResponse(
        app_session_id=jwt_token,
        user=OAuthMobileUserInfo(
            user_id=user.id,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            is_member=user.is_membership_active,
        ),
    )

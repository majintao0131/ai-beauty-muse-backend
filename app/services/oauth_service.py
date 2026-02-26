"""
OAuth 与门户通信：用 code 换 token、拉取 userinfo。
与 APP 端 docs/oauth-config-example.md 及后端 OAUTH_* 配置对齐。
"""
from typing import Optional, Dict, Any, List

import httpx

from app.config import settings


def _base(url: Optional[str], path: str) -> str:
    if not url:
        return ""
    return f"{url.rstrip('/')}/{path.lstrip('/')}"


def is_oauth_configured() -> bool:
    """是否已配置 OAuth（门户地址与应用凭证）。"""
    return bool(
        settings.oauth_server_url
        and settings.oauth_app_id
        and settings.oauth_app_secret
        and settings.oauth_allowed_redirect_uris
    )


def get_web_redirect_uri() -> str:
    """Web 回调的 redirect_uri，与门户白名单一致。"""
    return f"{settings.api_base_url.rstrip('/')}/api/oauth/callback"


def resolve_redirect_uri(candidate: Optional[str] = None) -> Optional[str]:
    """
    解析用于 token 交换的 redirect_uri。
    - 若传入 candidate，必须在 OAUTH_ALLOWED_REDIRECT_URIS 中；
    - 否则使用 Web 回调地址（适合 Web 场景）。
    """
    allowed: List[str] = list(settings.oauth_allowed_redirect_uris or [])
    if not allowed:
        return get_web_redirect_uri() if settings.api_base_url else None
    if candidate:
        if candidate in allowed:
            return candidate
        return None
    web = get_web_redirect_uri()
    if web in allowed:
        return web
    return allowed[0] if allowed else None


async def exchange_code_for_token(
    code: str,
    redirect_uri: str,
) -> Optional[Dict[str, Any]]:
    """
    用授权码向门户换 token。
    POST {oauth_server_url}/{oauth_token_path}
    grant_type=authorization_code&code=...&redirect_uri=...&client_id=...&client_secret=...
    返回 token 响应 JSON，失败返回 None。
    """
    if not is_oauth_configured():
        return None
    url = _base(settings.oauth_server_url, settings.oauth_token_path)
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": settings.oauth_app_id,
        "client_secret": settings.oauth_app_secret,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                data=payload,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


async def get_userinfo(access_token: str) -> Optional[Dict[str, Any]]:
    """
    用 access_token 向门户拉取用户信息。
    GET {oauth_server_url}/{oauth_userinfo_path}
    Authorization: Bearer {access_token}
    返回 JSON，常见字段：sub / id, name, nickname, avatar 等。
    """
    if not settings.oauth_server_url:
        return None
    url = _base(settings.oauth_server_url, settings.oauth_userinfo_path)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return None


def extract_oauth_id_from_token(token_response: Dict[str, Any]) -> Optional[str]:
    """
    从 token 响应中解析用户唯一标识（部分门户在 token 里返回 sub/open_id）。
    """
    return (
        token_response.get("sub")
        or token_response.get("open_id")
        or token_response.get("user_id")
        or (token_response.get("data") or {}).get("sub")
    )


def extract_user_info(userinfo: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    从 userinfo 中提取 (oauth_id, nickname, avatar_url)。
    常见字段：sub/id, name/nickname, avatar/avatar_url。
    """
    oauth_id = (
        userinfo.get("sub")
        or userinfo.get("id")
        or userinfo.get("open_id")
        or userinfo.get("user_id")
    )
    if oauth_id is not None:
        oauth_id = str(oauth_id)
    nickname = userinfo.get("nickname") or userinfo.get("name") or userinfo.get("username")
    avatar_url = userinfo.get("avatar") or userinfo.get("avatar_url") or userinfo.get("picture")
    return oauth_id, nickname, avatar_url

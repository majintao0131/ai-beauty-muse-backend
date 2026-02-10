"""
AI Beauty Muse - Auth API Routes
Handles phone-based registration/login, token refresh, and profile.
Keeps legacy device-based auth for backward compatibility.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import get_db, User
from app.models.schemas import (
    DeviceRegisterRequest,
    SmsSendRequest,
    SmsSendResponse,
    SmsLoginRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.services.auth_service import auth_service
from app.services.quota_service import quota_service
from app.services.membership_service import membership_service
from app.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ================================================================== #
#                   Phone-based Auth (手机号登录)                       #
# ================================================================== #

@router.post("/sms/send", response_model=SmsSendResponse)
async def send_sms_code(
    request: SmsSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    发送短信验证码到手机号。

    - 同一手机号每 60 秒只能发送一次
    - 验证码有效期 5 分钟
    - 开发模式（mock）下验证码会在服务端日志中打印
    """
    # Rate limit
    can_send = await auth_service.can_send_sms(db, request.phone)
    if not can_send:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请 {settings.sms_send_interval_seconds} 秒后再试",
        )

    code = await auth_service.send_sms_code(db, request.phone)

    # 构造 message
    if settings.sms_provider != "mock":
        message = "验证码已发送"
    elif request.phone in settings.sms_test_phones:
        message = f"验证码已发送（开发模式，验证码: {code}，万能码: {settings.sms_test_code}）"
    else:
        message = f"验证码已发送（开发模式，验证码: {code}）"

    return SmsSendResponse(
        success=True,
        message=message,
        expires_in=settings.sms_code_expire_minutes * 60,
    )


@router.post("/sms/login", response_model=TokenResponse)
async def sms_login(
    request: SmsLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    手机号 + 验证码登录（首次自动注册）。

    1. 验证短信验证码
    2. 如果手机号不存在则自动创建账号
    3. 返回 JWT token
    """
    # Verify SMS code
    valid = await auth_service.verify_sms_code(db, request.phone, request.code)
    if not valid:
        raise HTTPException(
            status_code=400,
            detail="验证码错误或已过期，请重新获取",
        )

    # Get or create user
    user, is_new = await auth_service.get_or_create_user_by_phone(
        db, request.phone, request.nickname,
    )

    # Check / auto-expire membership
    await membership_service.get_status(db, user)

    # Issue token
    token = auth_service.create_access_token(user_id=user.id)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        phone=auth_service.mask_phone(user.phone) if user.phone else None,
        nickname=user.nickname,
        is_member=user.is_membership_active,
    )


# ================================================================== #
#                   Legacy Device Auth (保留兼容)                       #
# ================================================================== #

@router.post("/register", response_model=TokenResponse)
async def register_device(
    request: DeviceRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Legacy: Register a device or login with an existing device ID.
    Kept for backward compatibility with older APP versions.
    """
    user = await auth_service.get_or_create_user(
        db=db,
        device_id=request.device_id,
        nickname=request.nickname,
    )
    token = auth_service.create_access_token(user_id=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        phone=auth_service.mask_phone(user.phone) if user.phone else None,
        nickname=user.nickname,
        is_member=user.is_membership_active,
    )


# ================================================================== #
#                   Token Refresh & Profile                            #
# ================================================================== #

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
):
    """
    刷新 JWT token（在 Header 中携带当前有效 token）。
    """
    token = auth_service.create_access_token(user_id=current_user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=current_user.id,
        phone=auth_service.mask_phone(current_user.phone) if current_user.phone else None,
        nickname=current_user.nickname,
        is_member=current_user.is_membership_active,
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户详细信息（含会员状态和各功能剩余次数）。
    """
    # Auto-expire membership if needed
    await membership_service.get_status(db, current_user)

    # Get all quota info
    quotas = await quota_service.get_all_quotas(db, current_user)

    return UserProfileResponse(
        user_id=current_user.id,
        phone=auth_service.mask_phone(current_user.phone) if current_user.phone else None,
        nickname=current_user.nickname,
        is_member=current_user.is_membership_active,
        member_expires_at=current_user.member_expires_at.isoformat() if current_user.member_expires_at else None,
        quotas=quotas,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )

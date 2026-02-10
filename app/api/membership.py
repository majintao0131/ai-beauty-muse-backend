"""
AI Beauty Muse - Membership API Routes
Handles subscription purchase and status check.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.models.schemas import (
    MembershipSubscribeRequest,
    MembershipSubscribeResponse,
    MembershipStatusResponse,
    QuotaStatusResponse,
)
from app.services.membership_service import membership_service
from app.services.quota_service import quota_service
from app.dependencies import get_current_user


router = APIRouter(prefix="/membership", tags=["Membership"])


@router.post("/subscribe", response_model=MembershipSubscribeResponse)
async def subscribe(
    request: MembershipSubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    订阅会员。

    当前套餐：
    - ``monthly`` — 每月 19.9 元，每个功能从 3 次/月提升到 10 次/月

    **生产环境**：此接口应在 APP 端支付成功回调后调用，传入 ``payment_order_id``。
    **开发模式**：直接调用即可激活会员（无需实际支付）。

    如果用户已是会员，则在当前到期时间基础上续期 30 天。
    """
    try:
        result = await membership_service.subscribe(
            db=db,
            user=current_user,
            plan=request.plan,
            payment_order_id=request.payment_order_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MembershipSubscribeResponse(**result)


@router.get("/status", response_model=MembershipStatusResponse)
async def get_membership_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询当前用户的会员状态。

    返回会员是否有效、套餐类型、到期时间、剩余天数。
    """
    result = await membership_service.get_status(db, current_user)
    return MembershipStatusResponse(**result)


@router.get("/quota", response_model=QuotaStatusResponse)
async def get_quota_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询当前用户各功能的本月使用情况和剩余次数。

    功能列表：
    - ``face_style`` — AI 发型推荐（免费 3 次/月，会员 10 次/月）
    - ``face_analysis`` — 面部分析（免费 3 次/月，会员 10 次/月）
    - ``destiny_color`` — 命理色谱（免费 3 次/月，会员 10 次/月）
    """
    from datetime import datetime
    year_month = datetime.utcnow().strftime("%Y-%m")

    # Auto-expire membership
    await membership_service.get_status(db, current_user)

    quotas = await quota_service.get_all_quotas(db, current_user)

    return QuotaStatusResponse(
        year_month=year_month,
        is_member=current_user.is_membership_active,
        features=quotas,
    )

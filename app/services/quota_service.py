"""
AI Beauty Muse - Usage Quota Service
Tracks per-feature monthly usage and enforces free / member limits.

Quota-controlled features:
  - face_style     (AI 发型推荐)
  - face_analysis  (面部分析 / 面相分析)
  - destiny_color  (命理色谱 / 命理运势)
"""
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import User, UsageQuota


# Feature keys recognised by the quota system
FEATURE_KEYS = ("face_style", "face_analysis", "destiny_color")

FEATURE_LABELS = {
    "face_style": "AI 发型推荐",
    "face_analysis": "面部分析",
    "destiny_color": "命理色谱",
}


def _current_year_month() -> str:
    """Return current year-month string, e.g. '2026-02'."""
    return datetime.utcnow().strftime("%Y-%m")


def _get_limit(user: User) -> int:
    """Return the monthly limit based on membership status."""
    if settings.quota_disabled:
        return 999999  # 测试环境关闭限制时视为无限
    if user.is_membership_active:
        return settings.quota_member_limit
    return settings.quota_free_limit


class QuotaService:
    """Service for checking and consuming usage quotas."""

    @staticmethod
    async def _get_or_create_quota(
        db: AsyncSession, user_id: str, feature: str, year_month: str,
    ) -> UsageQuota:
        """Get the quota row for (user, feature, month); create if missing."""
        result = await db.execute(
            select(UsageQuota).where(
                and_(
                    UsageQuota.user_id == user_id,
                    UsageQuota.feature == feature,
                    UsageQuota.year_month == year_month,
                )
            )
        )
        quota = result.scalar_one_or_none()
        if quota is None:
            quota = UsageQuota(
                user_id=user_id,
                feature=feature,
                year_month=year_month,
                used_count=0,
            )
            db.add(quota)
            await db.flush()
        return quota

    async def check_quota(
        self, db: AsyncSession, user: User, feature: str,
    ) -> Dict[str, Any]:
        """
        Check whether the user has remaining quota for *feature* this month.

        Returns:
            {
                "allowed": bool,
                "used": int,
                "limit": int,
                "remaining": int,
                "feature": str,
                "feature_label": str,
            }
        """
        ym = _current_year_month()
        limit = _get_limit(user)
        quota = await self._get_or_create_quota(db, user.id, feature, ym)

        remaining = max(0, limit - quota.used_count)
        return {
            "allowed": remaining > 0,
            "used": quota.used_count,
            "limit": limit,
            "remaining": remaining,
            "feature": feature,
            "feature_label": FEATURE_LABELS.get(feature, feature),
        }

    async def consume_quota(
        self, db: AsyncSession, user: User, feature: str,
    ) -> Dict[str, Any]:
        """
        Consume one unit of quota for *feature*.

        Raises ValueError if no quota remaining.

        Returns the same dict as ``check_quota`` (after decrement).
        """
        ym = _current_year_month()
        limit = _get_limit(user)
        quota = await self._get_or_create_quota(db, user.id, feature, ym)

        if quota.used_count >= limit:
            raise ValueError(
                f"本月「{FEATURE_LABELS.get(feature, feature)}」使用次数已达上限 "
                f"({limit} 次)，升级会员可提升至每月 {settings.quota_member_limit} 次。"
            )

        quota.used_count += 1
        quota.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(quota)

        remaining = max(0, limit - quota.used_count)
        return {
            "allowed": remaining > 0,
            "used": quota.used_count,
            "limit": limit,
            "remaining": remaining,
            "feature": feature,
            "feature_label": FEATURE_LABELS.get(feature, feature),
        }

    async def get_all_quotas(
        self, db: AsyncSession, user: User,
    ) -> Dict[str, Any]:
        """
        Return quota status for all tracked features in the current month.
        """
        ym = _current_year_month()
        limit = _get_limit(user)
        result: Dict[str, Any] = {}

        for feature in FEATURE_KEYS:
            quota = await self._get_or_create_quota(db, user.id, feature, ym)
            remaining = max(0, limit - quota.used_count)
            result[feature] = {
                "label": FEATURE_LABELS.get(feature, feature),
                "used": quota.used_count,
                "limit": limit,
                "remaining": remaining,
            }

        return result


# Singleton
quota_service = QuotaService()

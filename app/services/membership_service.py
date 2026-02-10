"""
AI Beauty Muse - Membership Service
Handles membership subscription, status check, and expiry.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import User, Membership


class MembershipService:
    """Service for managing membership subscriptions."""

    @staticmethod
    async def subscribe(
        db: AsyncSession,
        user: User,
        plan: str = "monthly",
        payment_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Subscribe a user to a membership plan.

        In production, this would be called after payment confirmation
        from the payment gateway (e.g. WeChat Pay / Alipay callback).
        For the MVP, calling this endpoint directly activates the membership.

        Returns:
            Subscription details dict.
        """
        now = datetime.utcnow()

        # If user is already a member, extend from current expiry
        if user.is_membership_active:
            start = user.member_expires_at
        else:
            start = now

        # Calculate expiry based on plan
        if plan == "monthly":
            expires = start + timedelta(days=30)
            price = settings.membership_monthly_price
        else:
            raise ValueError(f"Unsupported plan: {plan}")

        # Create membership record
        membership = Membership(
            user_id=user.id,
            plan_name=plan,
            price=price,
            started_at=start,
            expires_at=expires,
            payment_status="paid",
            payment_order_id=payment_order_id,
        )
        db.add(membership)

        # Update user flags
        user.is_member = True
        user.member_expires_at = expires
        user.updated_at = now

        await db.commit()
        await db.refresh(user)

        return {
            "success": True,
            "message": "会员订阅成功",
            "plan": plan,
            "price": price,
            "started_at": start.isoformat(),
            "expires_at": expires.isoformat(),
        }

    @staticmethod
    async def get_status(db: AsyncSession, user: User) -> Dict[str, Any]:
        """
        Get current membership status for a user.

        Also auto-expires the membership if it has lapsed.
        """
        now = datetime.utcnow()

        # Auto-expire if needed
        if user.is_member and user.member_expires_at and user.member_expires_at <= now:
            user.is_member = False
            user.updated_at = now
            await db.commit()
            await db.refresh(user)

        if not user.is_membership_active:
            return {
                "is_member": False,
                "plan": None,
                "price": None,
                "started_at": None,
                "expires_at": None,
                "days_remaining": 0,
            }

        # Find the latest active membership record
        result = await db.execute(
            select(Membership)
            .where(
                and_(
                    Membership.user_id == user.id,
                    Membership.payment_status == "paid",
                    Membership.expires_at > now,
                )
            )
            .order_by(Membership.expires_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()

        days_remaining = max(0, (user.member_expires_at - now).days) if user.member_expires_at else 0

        return {
            "is_member": True,
            "plan": record.plan_name if record else "monthly",
            "price": record.price if record else settings.membership_monthly_price,
            "started_at": record.started_at.isoformat() if record else None,
            "expires_at": user.member_expires_at.isoformat() if user.member_expires_at else None,
            "days_remaining": days_remaining,
        }


# Singleton
membership_service = MembershipService()

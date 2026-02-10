"""
AI Beauty Muse - Authentication Service
Handles JWT creation / validation, phone-based login, and SMS verification.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import User, SmsCode, generate_uuid


def _mask_phone(phone: str) -> str:
    """Mask phone number for display: 138****1234"""
    if not phone or len(phone) < 7:
        return phone or ""
    return phone[:3] + "****" + phone[-4:]


class AuthService:
    """Stateless helpers for JWT, SMS verification, and user management."""

    # ---- JWT helpers ------------------------------------------------

    @staticmethod
    def create_access_token(
        user_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a signed JWT access token."""
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
        )
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def decode_access_token(token: str) -> Optional[str]:
        """Validate and decode a JWT, returning the user_id."""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            return payload.get("sub")
        except JWTError:
            return None

    # ---- SMS verification code -------------------------------------

    @staticmethod
    def _generate_code(length: int = 6) -> str:
        """Generate a random numeric verification code."""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    async def can_send_sms(db: AsyncSession, phone: str) -> bool:
        """Check if enough time has passed since the last SMS to this phone."""
        # 测试手机号在 mock 模式下跳过频率限制
        if settings.sms_provider == "mock" and phone in settings.sms_test_phones:
            return True

        cutoff = datetime.utcnow() - timedelta(seconds=settings.sms_send_interval_seconds)
        result = await db.execute(
            select(SmsCode)
            .where(and_(SmsCode.phone == phone, SmsCode.created_at > cutoff))
            .order_by(SmsCode.created_at.desc())
            .limit(1)
        )
        recent = result.scalar_one_or_none()
        return recent is None

    async def send_sms_code(self, db: AsyncSession, phone: str) -> str:
        """
        Generate and persist a verification code for the given phone.

        In production, this would also call a real SMS gateway (Aliyun / Tencent).
        For now (mock mode), the code is returned directly and logged.
        """
        code = self._generate_code(settings.sms_code_length)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.sms_code_expire_minutes)

        sms_record = SmsCode(
            phone=phone,
            code=code,
            purpose="login",
            expires_at=expires_at,
            used=False,
        )
        db.add(sms_record)
        await db.commit()

        # ---- Send via configured provider ----
        if settings.sms_provider == "mock":
            print(f"📱 [MOCK SMS] → {phone}: 您的验证码是 {code}，{settings.sms_code_expire_minutes} 分钟内有效。")
        else:
            # TODO: integrate real SMS API (Aliyun SMS / Tencent Cloud SMS)
            print(f"📱 [SMS] Sending code to {phone} via {settings.sms_provider}")

        return code

    @staticmethod
    async def verify_sms_code(db: AsyncSession, phone: str, code: str) -> bool:
        """
        Verify a submitted SMS code.

        - In mock mode, test phones accept the universal test code.
        - Otherwise, finds the latest unused, non-expired code for this phone.
        - Marks it as used on success.
        """
        # 万能测试验证码（仅 mock 模式 + 白名单手机号）
        if (
            settings.sms_provider == "mock"
            and phone in settings.sms_test_phones
            and code == settings.sms_test_code
        ):
            return True

        now = datetime.utcnow()
        result = await db.execute(
            select(SmsCode)
            .where(
                and_(
                    SmsCode.phone == phone,
                    SmsCode.code == code,
                    SmsCode.used == False,  # noqa: E712
                    SmsCode.expires_at > now,
                )
            )
            .order_by(SmsCode.created_at.desc())
            .limit(1)
        )
        sms_record = result.scalar_one_or_none()
        if sms_record is None:
            return False

        # Mark as used
        sms_record.used = True
        await db.commit()
        return True

    # ---- User management -------------------------------------------

    @staticmethod
    async def get_or_create_user_by_phone(
        db: AsyncSession,
        phone: str,
        nickname: Optional[str] = None,
    ) -> tuple:
        """
        Look up a user by phone; create one if not found.

        Returns:
            (user, is_new) tuple.
        """
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        is_new = False

        if user is None:
            is_new = True
            user = User(
                id=generate_uuid(),
                phone=phone,
                nickname=nickname or f"用户{phone[-4:]}",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        elif nickname and not user.nickname:
            user.nickname = nickname
            await db.commit()
            await db.refresh(user)

        return user, is_new

    @staticmethod
    async def get_or_create_user(
        db: AsyncSession,
        device_id: str,
        nickname: Optional[str] = None,
    ) -> User:
        """Legacy device-based login (kept for backward compatibility)."""
        result = await db.execute(select(User).where(User.device_id == device_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                id=generate_uuid(),
                device_id=device_id,
                nickname=nickname,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Fetch a user by primary key."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    def mask_phone(phone: str) -> str:
        """Public wrapper for phone masking."""
        return _mask_phone(phone)


# Singleton
auth_service = AuthService()

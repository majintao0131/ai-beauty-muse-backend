"""
AI Beauty Muse - Database Models and Async Engine Setup
Uses SQLAlchemy async with aiosqlite.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Float,
    Boolean, ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, relationship

from app.config import settings


# ============== Async Engine & Session ==============

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


# ============== Helper ==============

def generate_uuid() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


# ============== ORM Models ==============

class User(Base):
    """User table – supports both phone-based and device-based auth."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    device_id = Column(String(128), unique=True, nullable=True, index=True)
    nickname = Column(String(64), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_member = Column(Boolean, default=False, nullable=False)
    member_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    usage_quotas = relationship("UsageQuota", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("ReportHistory", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_membership_active(self) -> bool:
        """Check if the user's membership is currently active."""
        if not self.is_member or not self.member_expires_at:
            return False
        return self.member_expires_at > datetime.utcnow()


class SmsCode(Base):
    """SMS verification codes for phone authentication."""
    __tablename__ = "sms_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    purpose = Column(String(20), nullable=False, default="login")  # login / register
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Membership(Base):
    """Membership subscription records."""
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String(50), nullable=False, default="monthly")
    price = Column(Float, nullable=False)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    payment_status = Column(String(20), nullable=False, default="pending")  # pending / paid / expired
    payment_order_id = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memberships")

    __table_args__ = (
        Index("ix_memberships_user_id", "user_id"),
    )


class UsageQuota(Base):
    """Per-feature monthly usage tracking."""
    __tablename__ = "usage_quotas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String(50), nullable=False)  # face_style / face_analysis / destiny_color
    year_month = Column(String(7), nullable=False)  # e.g. "2026-02"
    used_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="usage_quotas")

    __table_args__ = (
        UniqueConstraint("user_id", "feature", "year_month", name="uq_user_feature_month"),
        Index("ix_usage_quotas_user_feature", "user_id", "feature"),
    )


class ReportHistory(Base):
    """Stores historical reports from all AI features for user review."""
    __tablename__ = "report_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50), nullable=False)
    # report_type values:
    #   face_analysis  — 面相分析
    #   face_style     — AI 发型推荐
    #   face_edit      — 发型编辑效果图
    #   destiny_fortune — 命理运势
    #   daily_energy   — 每日能量卡
    #   stylist_card   — 理发师沟通卡
    title = Column(String(200), nullable=False)            # 列表展示标题
    summary = Column(String(500), nullable=True)           # 列表展示摘要
    thumbnail_url = Column(String(500), nullable=True)     # 缩略图 URL
    data = Column(Text, nullable=False)                    # 完整结果 JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")

    __table_args__ = (
        Index("ix_report_history_user_type", "user_id", "report_type"),
        Index("ix_report_history_created", "user_id", "created_at"),
    )


class ChatSession(Base):
    """A chat conversation session belonging to a user."""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessageRecord", back_populates="session", cascade="all, delete-orphan",
                            order_by="ChatMessageRecord.created_at")

    __table_args__ = (
        Index("ix_chat_sessions_user_id", "user_id"),
    )


class ChatMessageRecord(Base):
    """A single message inside a chat session."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)       # "user" | "assistant"
    content = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
    )


# ============== DB Lifecycle Helpers ==============

async def init_db() -> None:
    """Create all tables (safe to call multiple times)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI dependency – yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session

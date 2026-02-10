"""
AI Beauty Muse - Report History Service
Saves, lists, retrieves and deletes historical reports from all AI features.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import ReportHistory, generate_uuid


# Type labels for display
REPORT_TYPE_LABELS = {
    "face_analysis": "面相分析",
    "face_style": "AI 发型推荐",
    "face_edit": "发型编辑",
    "hair_color_experiment": "发色实验",
    "color_diagnosis": "色彩诊断",
    "body_analysis": "身材风格解析",
    "destiny_fortune": "命理运势",
    "daily_energy": "每日能量卡",
    "stylist_card": "理发师沟通卡",
    "landing_suggestion": "全面落地建议",
}


class HistoryService:
    """Service for managing report history."""

    @staticmethod
    async def save_report(
        db: AsyncSession,
        user_id: str,
        report_type: str,
        title: str,
        data: Dict[str, Any],
        summary: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
    ) -> str:
        """
        Save a report to history.

        Args:
            db: Database session.
            user_id: The user who owns this report.
            report_type: One of the REPORT_TYPE_LABELS keys.
            title: Display title for the list view.
            data: Complete result dict (will be JSON-serialised).
            summary: Short summary for the list view.
            thumbnail_url: Optional thumbnail image URL.

        Returns:
            The report UUID.
        """
        report_id = generate_uuid()
        record = ReportHistory(
            id=report_id,
            user_id=user_id,
            report_type=report_type,
            title=title,
            summary=summary,
            thumbnail_url=thumbnail_url,
            data=json.dumps(data, ensure_ascii=False, default=str),
        )
        db.add(record)
        await db.commit()
        return report_id

    @staticmethod
    async def delete_reports_by_type(
        db: AsyncSession,
        user_id: str,
        report_type: str,
    ) -> int:
        """
        Delete all reports of the given type for the user.
        Used e.g. to keep only the latest face_style report.

        Returns:
            Number of reports deleted.
        """
        stmt = delete(ReportHistory).where(
            and_(
                ReportHistory.user_id == user_id,
                ReportHistory.report_type == report_type,
            )
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def list_reports(
        db: AsyncSession,
        user_id: str,
        report_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List reports for a user, newest first.

        Args:
            db: Database session.
            user_id: Owner.
            report_type: Optional filter by type.
            page: 1-based page number.
            page_size: Items per page.

        Returns:
            (list_of_report_dicts, total_count)
        """
        conditions = [ReportHistory.user_id == user_id]
        if report_type:
            conditions.append(ReportHistory.report_type == report_type)

        # Count
        count_q = select(func.count()).select_from(ReportHistory).where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        query = (
            select(ReportHistory)
            .where(and_(*conditions))
            .order_by(ReportHistory.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        records = result.scalars().all()

        items = [
            {
                "id": r.id,
                "report_type": r.report_type,
                "title": r.title,
                "summary": r.summary,
                "thumbnail_url": r.thumbnail_url,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in records
        ]
        return items, total

    @staticmethod
    async def get_report(
        db: AsyncSession,
        user_id: str,
        report_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a single report by ID (must belong to user).

        Returns:
            Full report dict, or None if not found.
        """
        result = await db.execute(
            select(ReportHistory).where(
                and_(
                    ReportHistory.id == report_id,
                    ReportHistory.user_id == user_id,
                )
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None

        try:
            data = json.loads(record.data)
        except (json.JSONDecodeError, TypeError):
            data = {}

        return {
            "id": record.id,
            "report_type": record.report_type,
            "title": record.title,
            "summary": record.summary,
            "thumbnail_url": record.thumbnail_url,
            "data": data,
            "created_at": record.created_at.isoformat() if record.created_at else "",
        }

    @staticmethod
    async def delete_report(
        db: AsyncSession,
        user_id: str,
        report_id: str,
    ) -> bool:
        """
        Delete a report (must belong to user).

        Returns:
            True if deleted, False if not found.
        """
        result = await db.execute(
            select(ReportHistory).where(
                and_(
                    ReportHistory.id == report_id,
                    ReportHistory.user_id == user_id,
                )
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            return False

        await db.delete(record)
        await db.commit()
        return True


# Singleton
history_service = HistoryService()

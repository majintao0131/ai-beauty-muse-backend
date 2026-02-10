"""
AI Beauty Muse - Report History API Routes
List, view detail, and delete saved reports from all AI features.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, User
from app.models.schemas import (
    ReportHistoryItem,
    ReportHistoryListResponse,
    ReportHistoryDetailResponse,
    ReportHistoryCreateRequest,
    ReportHistoryCreateResponse,
)
from app.services.history_service import history_service, REPORT_TYPE_LABELS
from app.services.report_landing_service import report_landing_service
from app.dependencies import get_current_user


router = APIRouter(prefix="/history", tags=["Report History"])


@router.get("/reports", response_model=ReportHistoryListResponse)
async def list_reports(
    report_type: Optional[str] = Query(
        None,
        description="按类型筛选: face_analysis / face_style / face_edit / destiny_fortune / daily_energy / stylist_card",
    ),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数，默认 20，最大 100"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的历史报告列表（分页，最新优先）。

    可通过 ``report_type`` 参数筛选特定类型的报告。

    支持的报告类型：

    | report_type | 说明 |
    |-------------|------|
    | ``face_analysis`` | 面相分析 |
    | ``face_style`` | AI 发型推荐 |
    | ``face_edit`` | 发型编辑效果图 |
    | ``destiny_fortune`` | 命理运势 |
    | ``daily_energy`` | 每日能量卡 |
    | ``stylist_card`` | 理发师沟通卡 |
    """
    items, total = await history_service.list_reports(
        db=db,
        user_id=current_user.id,
        report_type=report_type,
        page=page,
        page_size=page_size,
    )

    return ReportHistoryListResponse(
        reports=[ReportHistoryItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/reports", response_model=ReportHistoryCreateResponse)
async def create_report(
    request: ReportHistoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    从 APP 端主动创建一份历史报告。

    适用于需要客户端聚合多次 API 调用结果后一次性保存的场景，
    例如 AI 发型功能中将推荐分析 + 3 张效果照 + 理发师沟通卡合并为一条记录。
    """
    # Validate report_type
    valid_types = set(REPORT_TYPE_LABELS.keys())
    if request.report_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的报告类型: {request.report_type}，可选: {', '.join(sorted(valid_types))}",
        )

    # 报告落地建模：对已建模的 report_type 校验 data 结构
    try:
        report_landing_service.validate(request.report_type, request.data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 保存完整 AI 发型时，删除本用户当次的零散 face_edit 记录，避免列表出现多条碎片
    if request.report_type == "face_style":
        await history_service.delete_reports_by_type(db, current_user.id, "face_edit")

    report_id = await history_service.save_report(
        db=db,
        user_id=current_user.id,
        report_type=request.report_type,
        title=request.title,
        data=request.data,
        summary=request.summary,
        thumbnail_url=request.thumbnail_url,
    )

    return ReportHistoryCreateResponse(id=report_id, success=True)


@router.get("/reports/{report_id}", response_model=ReportHistoryDetailResponse)
async def get_report_detail(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取某份历史报告的完整详情。

    返回的 ``data`` 字段包含该报告原始接口的完整响应数据，
    APP 端可直接用同一套 UI 组件来渲染。
    """
    report = await history_service.get_report(db, current_user.id, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在或无权访问")

    return ReportHistoryDetailResponse(**report)


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除某份历史报告。
    """
    deleted = await history_service.delete_report(db, current_user.id, report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="报告不存在或无权访问")

    return {"success": True, "message": "报告已删除"}


@router.get("/types")
async def list_report_types():
    """
    获取所有支持的报告类型（静态列表，无需鉴权）。
    """
    return {
        "types": [
            {"key": k, "label": v}
            for k, v in REPORT_TYPE_LABELS.items()
        ]
    }

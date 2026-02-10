"""
AI Beauty Muse - Report Landing Service
报告落地建模：对 APP 端通过 POST /history/reports 提交的 data 做结构校验与业务规则。
"""
from typing import Dict, Any, Type, Optional

from pydantic import BaseModel, ValidationError

from app.models.schemas import FaceStyleReportData
from app.services.history_service import REPORT_TYPE_LABELS


# report_type -> 落地 data 的 Pydantic 模型（仅对需要建模的类型配置）
LANDING_DATA_MODELS: Dict[str, Type[BaseModel]] = {
    "face_style": FaceStyleReportData,
}


def get_landing_model(report_type: str) -> Optional[Type[BaseModel]]:
    """返回某报告类型对应的落地 data 模型类，无则返回 None."""
    return LANDING_DATA_MODELS.get(report_type)


def validate_landing_data(report_type: str, data: Dict[str, Any]) -> None:
    """
    校验「报告落地」时提交的 data 是否符合该 report_type 的建模结构。

    若该类型已配置落地模型，则校验 data 可被解析为对应模型（允许多出字段）；
    未配置的类型不校验，直接通过。

    Raises:
        ValueError: 校验未通过时，附带可读说明。
    """
    model_cls = get_landing_model(report_type)
    if model_cls is None:
        return

    if not isinstance(data, dict):
        raise ValueError("data 必须为 JSON 对象")

    try:
        model_cls.model_validate(data)
    except ValidationError as e:
        msg = "报告落地 data 结构不符合规范"
        errs = e.errors()
        if errs:
            first = errs[0]
            loc = ".".join(str(x) for x in first.get("loc", []))
            msg = f"{msg}：字段 {loc} — {first.get('msg', '')}"
        raise ValueError(msg) from e


def get_supported_landing_types() -> list:
    """返回已配置落地建模的报告类型列表（用于文档与前端）。"""
    return list(LANDING_DATA_MODELS.keys())


# 单例（无状态，仅提供函数亦可）
class ReportLandingService:
    """报告落地业务：建模校验与扩展规则."""

    @staticmethod
    def validate(report_type: str, data: Dict[str, Any]) -> None:
        """校验 data 是否符合该 report_type 的落地结构。"""
        validate_landing_data(report_type, data)

    @staticmethod
    def get_landing_model(report_type: str) -> Optional[Type[BaseModel]]:
        return LANDING_DATA_MODELS.get(report_type)

    @staticmethod
    def supported_landing_types() -> list:
        return get_supported_landing_types()


report_landing_service = ReportLandingService()

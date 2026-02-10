"""
AI Beauty Muse - Landing Suggestion Service
结合脸部分析、色彩诊断、身材风格、命理色谱、当日运势等，生成全面且精简的落地建议。
"""
import json
from typing import Dict, Any, List, Optional

from app.services.openai_service import openai_service


def _extract_face_summary(data: Dict[str, Any]) -> str:
    """从脸部分析结果提取精简摘要。"""
    parts = []
    if data.get("face_shape_cn"):
        parts.append(f"脸型：{data['face_shape_cn']}")
    if data.get("overall_analysis"):
        parts.append(f"整体分析：{data['overall_analysis'][:150]}")
    if data.get("hairstyle_recommendations"):
        recs = data["hairstyle_recommendations"]
        if isinstance(recs, list):
            parts.append("发型建议：" + "、".join(recs[:3]) if recs else "")
        else:
            parts.append(f"发型建议：{recs}")
    if data.get("makeup_tips"):
        tips = data["makeup_tips"]
        if isinstance(tips, list):
            parts.append("妆容要点：" + "、".join(tips[:3]) if tips else "")
        else:
            parts.append(f"妆容要点：{tips}")
    fb = data.get("fortune_beauty")
    if fb and isinstance(fb, dict) and fb.get("fortune_beauty_summary"):
        parts.append("今日运势美学：" + fb["fortune_beauty_summary"][:100])
    return "\n".join(parts) if parts else ""


def _extract_color_summary(data: Dict[str, Any]) -> str:
    """从色彩诊断结果提取精简摘要。"""
    parts = []
    if data.get("season_type_cn"):
        parts.append(f"个人色彩：{data['season_type_cn']}")
    if data.get("skin_undertone_cn"):
        parts.append(f"肤调：{data['skin_undertone_cn']}")
    if data.get("best_colors"):
        colors = [c.get("name", c.get("hex", "")) for c in data["best_colors"][:5] if isinstance(c, dict)]
        if colors:
            parts.append("适合色：" + "、".join(colors))
    if data.get("avoid_colors"):
        colors = [c.get("name", c.get("hex", "")) for c in data["avoid_colors"][:3] if isinstance(c, dict)]
        if colors:
            parts.append("避免色：" + "、".join(colors))
    if data.get("hair_colors"):
        colors = [c.get("name", c.get("hex", "")) for c in data["hair_colors"][:3] if isinstance(c, dict)]
        if colors:
            parts.append("推荐发色：" + "、".join(colors))
    if data.get("analysis"):
        parts.append("色彩分析：" + (data["analysis"][:120] or ""))
    return "\n".join(parts) if parts else ""


def _extract_body_summary(data: Dict[str, Any]) -> str:
    """从身材风格解析结果提取精简摘要。"""
    parts = []
    if data.get("body_type_cn"):
        parts.append(f"身材类型：{data['body_type_cn']}")
    if data.get("body_type_description"):
        parts.append(data["body_type_description"][:100])
    if data.get("strengths"):
        parts.append("扬长：" + data["strengths"][:80])
    if data.get("areas_to_enhance"):
        parts.append("修饰：" + data["areas_to_enhance"][:80])
    if data.get("recommended_silhouettes"):
        parts.append("推荐廓形：" + "、".join(data["recommended_silhouettes"][:5]))
    if data.get("styles_to_avoid"):
        parts.append("慎选：" + data["styles_to_avoid"][:80])
    return "\n".join(parts) if parts else ""


def _extract_destiny_summary(data: Dict[str, Any]) -> str:
    """从命理/今日运势结果提取精简摘要。"""
    parts = []
    if data.get("day_master"):
        parts.append(f"日主：{data['day_master']}")
    if data.get("favorable_element"):
        parts.append(f"喜用神：{data['favorable_element']}")
    if data.get("fortune_summary"):
        parts.append("今日运势：" + data["fortune_summary"][:120])
    if data.get("fortune_score") is not None:
        parts.append(f"运势指数：{data['fortune_score']}")
    if data.get("lucky_colors"):
        colors = [c.get("name", c.get("hex", "")) for c in data["lucky_colors"][:5] if isinstance(c, dict)]
        if colors:
            parts.append("今日幸运色：" + "、".join(colors))
    if data.get("outfit_suggestions"):
        parts.append("穿搭建议：" + data["outfit_suggestions"][:100])
    if data.get("energy_tips"):
        parts.append("能量提示：" + data["energy_tips"][:80])
    if data.get("fortune_areas") and isinstance(data["fortune_areas"], dict):
        areas = "；".join(f"{k}:{v[:30]}" for k, v in list(data["fortune_areas"].items())[:4])
        parts.append("分项运势：" + areas)
    return "\n".join(parts) if parts else ""


def _extract_daily_summary(data: Dict[str, Any]) -> str:
    """从每日能量结果提取精简摘要。"""
    parts = []
    if data.get("daily_stem_branch"):
        parts.append(f"当日干支：{data['daily_stem_branch']}")
    if data.get("five_elements_energy"):
        parts.append("五行能量：" + data["five_elements_energy"][:80])
    if data.get("lucky_colors"):
        colors = [c.get("name", c.get("hex", "")) for c in data["lucky_colors"][:5] if isinstance(c, dict)]
        if colors:
            parts.append("幸运色：" + "、".join(colors))
    if data.get("outfit_suggestions"):
        parts.append("穿搭：" + data["outfit_suggestions"][:100])
    if data.get("makeup_tips"):
        parts.append("妆容：" + data["makeup_tips"][:80])
    if data.get("energy_tips"):
        parts.append("能量：" + data["energy_tips"][:80])
    if data.get("occasion_special"):
        parts.append("场合建议：" + data["occasion_special"][:80])
    return "\n".join(parts) if parts else ""


def _build_prompt(
    face: Optional[Dict],
    color: Optional[Dict],
    body: Optional[Dict],
    destiny: Optional[Dict],
    daily: Optional[Dict],
) -> str:
    """组装给 LLM 的上下文与指令。"""
    blocks: List[str] = []
    if face:
        blocks.append("【脸部分析】\n" + _extract_face_summary(face))
    if color:
        blocks.append("【色彩诊断】\n" + _extract_color_summary(color))
    if body:
        blocks.append("【身材风格】\n" + _extract_body_summary(body))
    if destiny:
        blocks.append("【命理色谱与今日运势】\n" + _extract_destiny_summary(destiny))
    if daily:
        blocks.append("【当日能量与穿搭】\n" + _extract_daily_summary(daily))

    if not blocks:
        return ""

    context = "\n\n".join(blocks)
    return f"""你是一位专业的美学与形象顾问。请根据以下用户的多维度分析结果，生成一份**全面且精简的落地建议**，便于用户今日/近期直接执行。

{context}

请严格按以下 JSON 格式输出，不要输出其他内容：
{{
  "summary": "一段 2～4 句的总述，综合以上所有维度，给出今日/近期的核心行动建议（穿搭、妆容、发色、心态等）。",
  "sections": [
    {{ "title": "板块标题（如：今日穿搭要点）", "content": "该板块 2～4 句可执行建议。" }},
    {{ "title": "妆容与发色", "content": "结合脸型与个人色彩的妆容、发色建议。" }},
    {{ "title": "场合与能量", "content": "结合当日运势与能量的心态或场合建议。" }}
  ]
}}

要求：
- summary 和每个 section 的 content 都要具体、可执行，避免空话。
- sections 数量 3～5 个即可，标题简短，内容精炼。
- 若某维度未提供，则不要在建议中编造该维度信息，只基于已有维度综合。
- 输出必须是合法 JSON，且只包含 summary 和 sections 两个字段。"""


class LandingSuggestionService:
    """结合多模块数据生成全面精简落地建议。"""

    async def generate(
        self,
        face_analysis: Optional[Dict[str, Any]] = None,
        color_diagnosis: Optional[Dict[str, Any]] = None,
        body_analysis: Optional[Dict[str, Any]] = None,
        destiny_fortune: Optional[Dict[str, Any]] = None,
        daily_energy: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        根据传入的模块数据（至少一项）生成落地建议。

        Returns:
            {"summary": str, "sections": [{"title": str, "content": str}, ...]}
        """
        if not any([face_analysis, color_diagnosis, body_analysis, destiny_fortune, daily_energy]):
            return {
                "summary": "请至少传入一项分析结果（脸部分析、色彩诊断、身材风格、命理运势或当日能量）后再生成落地建议。",
                "sections": [],
            }

        prompt = _build_prompt(
            face_analysis, color_diagnosis, body_analysis, destiny_fortune, daily_energy
        )
        if not prompt:
            return {"summary": "未获取到有效输入。", "sections": []}

        try:
            raw = await openai_service.generate_destiny_text(
                prompt,
                system_prompt=(
                    "你输出严格为 JSON 对象，包含 summary（字符串）和 sections（数组，每项含 title 和 content）。"
                    "不要输出 markdown 代码块或任何非 JSON 内容。"
                ),
                temperature=0.5,
                max_tokens=2000,
            )
        except Exception as e:
            return {
                "summary": "生成落地建议时发生错误，请稍后重试。",
                "sections": [{"title": "提示", "content": str(e)[:200]}],
            }

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            out = json.loads(raw)
        except json.JSONDecodeError:
            return {
                "summary": raw[:300] if len(raw) > 300 else raw,
                "sections": [],
            }

        summary = out.get("summary") or "暂无总述。"
        sections_raw = out.get("sections") or []
        sections = []
        for s in sections_raw:
            if isinstance(s, dict) and s.get("title") and s.get("content"):
                sections.append({"title": str(s["title"]), "content": str(s["content"])})
            elif isinstance(s, dict):
                sections.append({
                    "title": s.get("title") or "建议",
                    "content": s.get("content") or "",
                })

        return {"summary": summary, "sections": sections}


landing_suggestion_service = LandingSuggestionService()

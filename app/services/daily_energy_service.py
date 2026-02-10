"""
AI Beauty Muse - Daily Energy Service
Handles daily energy calculations and outfit recommendations.

When the user provides a birthday, all output is **personalized** based on
their BaZi — including lucky colors, five-element energy, outfit suggestions,
and energy tips.
"""
import json
from datetime import date
from typing import Dict, List, Any, Optional

from app.services.destiny_service import (
    destiny_service,
    ELEMENT_NAMES,
    ELEMENT_COLORS,
    STEM_ELEMENTS,
    BRANCH_ELEMENTS,
    ELEMENT_GENERATE,
)
from app.services.openai_service import openai_service

# Reverse lookup: Chinese element name → English key
_CN_TO_EN = {v: k for k, v in ELEMENT_NAMES.items()}


class DailyEnergyService:
    """Service for daily energy guidance and outfit recommendations."""

    def get_daily_stem_branch(self) -> str:
        return destiny_service.get_today_stem_branch()

    def get_daily_element(self) -> str:
        return destiny_service.get_today_element()

    def get_lucky_colors(self) -> List[Dict[str, str]]:
        """Generic (non-personalized) lucky colors for /daily/quick."""
        return destiny_service.get_today_lucky_colors()

    # ── Personalized lucky colors ───────────────────────────────────

    @staticmethod
    def _personal_lucky_colors(
        favorable_cn: str,
        five_elements: Dict[str, int],
        today_element_en: str,
    ) -> List[Dict[str, Any]]:
        """Compute personalized lucky colors based on user's BaZi.

        Priority: 1) favorable element  2) weakest element  3) today element.
        """
        favorable_en = _CN_TO_EN.get(favorable_cn, "earth")
        weakest_en = min(five_elements, key=five_elements.get)

        seen: set = set()
        ordered: List[str] = []
        for el in [favorable_en, weakest_en, today_element_en]:
            if el not in seen:
                seen.add(el)
                ordered.append(el)

        colors: List[Dict[str, Any]] = []
        for idx, el in enumerate(ordered):
            take = 2 if idx == 0 else 1
            for c in ELEMENT_COLORS.get(el, [])[:take]:
                colors.append({**c, "element": el})
        return colors

    # ── Main entry point ────────────────────────────────────────────

    async def get_daily_energy(
        self,
        occasion: Optional[str] = None,
        user_birth_year: Optional[int] = None,
        user_birth_month: Optional[int] = None,
        user_birth_day: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive daily energy guidance.

        When a birthday is provided, the response is fully personalized:
        lucky colors, energy analysis, outfit suggestions, etc.
        """
        today = date.today()
        daily_stem_branch = self.get_daily_stem_branch()
        daily_element = self.get_daily_element()

        # Today's element key
        today_pillar = destiny_service.calculate_day_pillar(
            today.year, today.month, today.day,
        )
        today_element_en = STEM_ELEMENTS.get(today_pillar.heavenly, "earth")

        # ── Personalized context (if birthday provided) ──
        personal_context = ""
        lucky_colors: List[Dict[str, Any]]

        has_birthday = (
            user_birth_year is not None
            and user_birth_month is not None
            and user_birth_day is not None
        )

        if has_birthday:
            pillars = destiny_service.calculate_bazi(
                user_birth_year, user_birth_month, user_birth_day,
            )
            day_master_str, _ = destiny_service.analyze_day_master(pillars)
            five_elements = destiny_service.count_five_elements(pillars)
            favorable_cn = destiny_service.get_favorable_element(pillars)

            dm_element_en = STEM_ELEMENTS.get(pillars[2].heavenly, "earth")
            dm_element_cn = ELEMENT_NAMES.get(dm_element_en, "土")

            five_elements_str = ", ".join(
                f"{ELEMENT_NAMES[k]}{v}" for k, v in five_elements.items()
            )

            personal_context = (
                f"用户八字：{' '.join(f'{p.heavenly}{p.earthly}' for p in pillars)}\n"
                f"日主：{day_master_str}（五行属{dm_element_cn}）\n"
                f"五行分布：{five_elements_str}\n"
                f"喜用神：{favorable_cn}\n"
            )

            # Personalized lucky colors
            lucky_colors = self._personal_lucky_colors(
                favorable_cn=favorable_cn,
                five_elements=five_elements,
                today_element_en=today_element_en,
            )
        else:
            # No birthday → generic lucky colors (same for everyone)
            lucky_colors = destiny_service.get_today_lucky_colors()

        # ── AI prompt ──
        prompt = f"""今天是{today.year}年{today.month}月{today.day}日，
今日干支：{daily_stem_branch}
今日五行主气：{daily_element}
{personal_context}
{f'今日场合：{occasion}' if occasion else ''}

请以JSON格式返回以下信息（不要用 markdown code fence 包裹）：
{{
  "five_elements_energy": "今日五行能量分析{'，须结合用户八字与今日干支的生克关系进行个性化解读' if has_birthday else ''}，100字左右",
  "outfit_suggestions": "今日穿搭建议{'，重点推荐喜用神对应的颜色' if has_birthday else ''}，150字左右，包括颜色、款式、风格",
  "makeup_tips": "今日妆容要点{'，结合用户五行特点' if has_birthday else ''}，100字左右",
  "energy_tips": "今日能量提示{'，结合用户日主五行属性' if has_birthday else ''}，100字左右，包括注意事项和开运建议"
  {f', "occasion_special": "针对{occasion}的特别建议，150字左右，包括战袍方案"' if occasion else ''}
}}"""

        system_prompt = (
            "你是一位精通东方命理和时尚穿搭的能量顾问。"
            "请根据今日的干支五行能量"
            + ("，结合用户的八字命理特征和场合需求，" if has_birthday else "，结合场合需求，")
            + "提供专业的穿搭和能量建议。建议要具体、实用，让用户能够直接参考执行。"
        )

        response = await openai_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )

        # ── Parse JSON ──
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            result = json.loads(json_str.strip())
        except Exception:
            result = self._get_default_energy(daily_element, occasion)

        return {
            "date": today.strftime("%Y年%m月%d日"),
            "daily_stem_branch": daily_stem_branch,
            "five_elements_energy": result.get("five_elements_energy", f"今日{daily_element}气旺盛"),
            "lucky_colors": lucky_colors,
            "outfit_suggestions": result.get("outfit_suggestions", ""),
            "makeup_tips": result.get("makeup_tips", ""),
            "energy_tips": result.get("energy_tips", ""),
            "occasion_special": result.get("occasion_special") if occasion else None,
        }

    # ── Default fallback ────────────────────────────────────────────

    def _get_default_energy(
        self,
        element: str,
        occasion: Optional[str] = None,
    ) -> Dict[str, Any]:
        element_advice = {
            "木": {
                "five_elements_energy": "今日木气旺盛，适合创新、开拓、学习新事物。木主生发，是展现活力和创意的好日子。",
                "outfit_suggestions": "建议穿着绿色系或蓝色系服装，展现清新活力。可选择自然材质如棉麻，搭配简约俐落的款式。",
                "makeup_tips": "妆容以清新自然为主，眼影选择大地色或绿色系，唇色选择裸粉或珊瑚色。",
                "energy_tips": "今日适合户外活动、运动健身、学习充电。避免过度劳累，保持心情愉悦。",
            },
            "火": {
                "five_elements_energy": "今日火气旺盛，适合社交、表达、展现自我。火主热情，是展现魅力和领导力的好日子。",
                "outfit_suggestions": "建议穿着红色系或橙色系服装，展现热情活力。可选择亮眼的配饰，搭配大方得体的款式。",
                "makeup_tips": "妆容可以稍微浓郁，眼影选择暖色系，唇色选择正红或橘红色。",
                "energy_tips": "今日适合社交活动、演讲表达、重要会议。注意控制情绪，避免过于冲动。",
            },
            "土": {
                "five_elements_energy": "今日土气旺盛，适合稳定、积累、处理实务。土主稳重，是踏实做事和理财的好日子。",
                "outfit_suggestions": "建议穿着大地色系服装，如驼色、米色、咖啡色，展现稳重可靠。款式选择经典简约。",
                "makeup_tips": "妆容以自然稳重为主，眼影选择大地色系，唇色选择豆沙色或裸色。",
                "energy_tips": "今日适合处理财务、签约、规划未来。保持耐心，稳扎稳打。",
            },
            "金": {
                "five_elements_energy": "今日金气旺盛，适合决断、执行、追求完美。金主果断，是处理重要事务和做决定的好日子。",
                "outfit_suggestions": "建议穿着白色、银色或金色系服装，展现精致优雅。可选择金属配饰，搭配俐落的款式。",
                "makeup_tips": "妆容以精致为主，眼影选择香槟色或银色系，唇色选择玫瑰色或裸粉色。",
                "energy_tips": "今日适合做重要决定、谈判、追求目标。注意不要过于苛刻，保持弹性。",
            },
            "水": {
                "five_elements_energy": "今日水气旺盛，适合思考、沟通、灵活应变。水主智慧，是学习和人际交流的好日子。",
                "outfit_suggestions": "建议穿着蓝色系或黑色系服装，展现深邃智慧。可选择流畅的款式，搭配简约的配饰。",
                "makeup_tips": "妆容以柔和为主，眼影选择蓝色或灰色系，唇色选择莓果色或裸色。",
                "energy_tips": "今日适合学习、沟通、处理复杂事务。保持灵活，善用智慧解决问题。",
            },
        }

        advice = element_advice.get(element, element_advice["土"])

        if occasion:
            advice["occasion_special"] = (
                f"针对{occasion}，建议选择能展现专业和自信的穿搭，"
                "颜色以今日幸运色为主，搭配得体的配饰，展现最佳状态。"
            )

        return advice


# Singleton instance
daily_energy_service = DailyEnergyService()

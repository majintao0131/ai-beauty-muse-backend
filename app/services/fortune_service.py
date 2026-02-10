"""
AI Beauty Muse - Fortune Service (Gemini 3 Pro)
Comprehensive destiny analysis + today's fortune reading.

Uses Gemini 3 Pro for deeper reasoning and richer cultural knowledge
compared to the Flash model used in other services.

Lucky colors and fortune score are **personalized** per user:
- Lucky colors are derived from the user's favorable element (喜用神),
  weakest element, and today's element — not just today's date.
- A base fortune score is calculated from the Five-Element interaction
  between the user's day master and today's stem-branch, then Gemini
  refines it with richer context.
"""
import json
from datetime import date
from typing import Dict, Any, List, Optional

from app.services.destiny_service import (
    destiny_service,
    ELEMENT_NAMES,
    ELEMENT_COLORS,
    STEM_ELEMENTS,
    BRANCH_ELEMENTS,
    ELEMENT_GENERATE,
    ELEMENT_OVERCOME,
)
from app.services.openai_service import openai_service


# ── Reverse lookup: Chinese element name → English key ──────────────
_CN_TO_EN = {v: k for k, v in ELEMENT_NAMES.items()}


# ── Personalized lucky color algorithm ──────────────────────────────

def _personal_lucky_colors(
    favorable_cn: str,
    five_elements: Dict[str, int],
    today_element_en: str,
) -> List[Dict[str, Any]]:
    """Compute personalized lucky colors based on the user's BaZi.

    Priority order:
    1. **Favorable element** (喜用神) — the most important supplement.
    2. **Weakest element** — the one the user lacks the most.
    3. **Today's element** — contextual energy of the day.

    De-duplicates by element so there is variety.
    """
    # Resolve favorable element to English key
    favorable_en = _CN_TO_EN.get(favorable_cn, "earth")

    # Find the user's weakest element (lowest count)
    weakest_en = min(five_elements, key=five_elements.get)

    # Collect candidate elements in priority order, skip duplicates
    seen = set()
    ordered_elements: List[str] = []
    for el in [favorable_en, weakest_en, today_element_en]:
        if el not in seen:
            seen.add(el)
            ordered_elements.append(el)

    # Pick colors: 2 from top priority, 1 each from the rest
    colors: List[Dict[str, Any]] = []
    for idx, el in enumerate(ordered_elements):
        take = 2 if idx == 0 else 1
        for c in ELEMENT_COLORS.get(el, [])[:take]:
            colors.append({**c, "element": el})

    return colors


# ── Personalized base fortune score ─────────────────────────────────

def _base_fortune_score(
    day_master_element: str,
    today_stem_element: str,
    today_branch_element: str,
    favorable_en: str,
) -> int:
    """Calculate a base fortune score (40-85) from Five-Element relations.

    Rules (traditional 生克 logic):
    - Today **generates** day master  → very auspicious (+)
    - Today **same as** day master    → supportive (+)
    - Today **is** favorable element  → highly auspicious (+)
    - Day master **generates** today  → moderate drain (−)
    - Today **overcomes** day master  → pressure (−)
    - Day master **overcomes** today  → effort needed (−)

    The base is then refined by Gemini 3 Pro in the prompt.
    """
    score = 60  # neutral baseline

    for today_el in {today_stem_element, today_branch_element}:
        # Today generates me (生我)
        if ELEMENT_GENERATE.get(today_el) == day_master_element:
            score += 8
        # Same element (比肩)
        elif today_el == day_master_element:
            score += 5
        # I generate today (我生 = 泄)
        elif ELEMENT_GENERATE.get(day_master_element) == today_el:
            score -= 4
        # Today overcomes me (克我)
        elif ELEMENT_OVERCOME.get(today_el) == day_master_element:
            score -= 7
        # I overcome today (我克 = 耗)
        elif ELEMENT_OVERCOME.get(day_master_element) == today_el:
            score -= 3

    # Bonus if today's element matches favorable
    if today_stem_element == favorable_en:
        score += 10
    if today_branch_element == favorable_en and today_branch_element != today_stem_element:
        score += 5

    return max(25, min(90, score))  # clamp to 25-90


# ── Prompt templates ────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
你是一位精通东方命理学的资深命理师，同时也是时尚穿搭顾问。你精通八字、五行、天干地支、
喜用神分析，能深入浅出地为用户解读命理特征和当日运势。

要求：
- 语言亲切、专业但不晦涩，让普通用户也能理解
- 今日运势要结合用户八字与当日干支的生克关系进行个性化解读
- 运势评分（fortune_score）必须基于参考分 {base_score} 上下浮动 ±10 以内，综合你的
  专业判断做微调，不要偏离太远
- 所有建议要具体、可执行
- 严格按要求的 JSON 格式返回，不要添加额外字段
"""


def _build_fortune_prompt(
    *,
    bazi_str: str,
    day_master: str,
    day_master_element_cn: str,
    five_elements_str: str,
    favorable: str,
    today_str: str,
    today_sb: str,
    today_element: str,
    base_score: int,
    occasion: Optional[str],
) -> str:
    """Build the mega-prompt for Gemini 3 Pro."""
    occasion_field = ""
    if occasion:
        occasion_field = (
            f',\n  "occasion_special": "针对「{occasion}」的专属建议，'
            f'包括穿搭战袍方案、注意事项和好运锦囊，200字左右"'
        )

    return f"""\
今天是 {today_str}。
今日干支：{today_sb}
今日五行主气：{today_element}

用户八字：{bazi_str}
日主：{day_master}（五行属{day_master_element_cn}）
五行分布：{five_elements_str}
喜用神：{favorable}
系统参考运势评分：{base_score}（基于五行生克算法，请在此基础上 ±10 内微调）
{f"今日场合：{occasion}" if occasion else ""}

请完成以下两大板块的分析，以 **纯 JSON** 格式返回（不要用 markdown code fence 包裹）：

{{
  "personality": "根据八字分析性格特征，150字左右",
  "destiny_overview": "命理综合解读，含事业方向、感情特点、财运走势，300字左右",

  "fortune_summary": "今日运势总评，必须结合此用户的日主（{day_master_element_cn}）与今日干支（{today_sb}）的具体生克关系来分析，150字左右",
  "fortune_score": 整数(基于参考分{base_score}微调±10),
  "fortune_areas": {{
    "事业": "今日事业运分析，结合日主与今日五行关系，80字左右",
    "感情": "今日感情运分析，80字左右",
    "财运": "今日财运分析，80字左右",
    "健康": "今日健康提示，结合日主五行属性，80字左右"
  }},

  "outfit_suggestions": "今日穿搭建议，重点推荐喜用神（{favorable}）对应的颜色，150字左右",
  "energy_tips": "今日能量与心态建议，100字左右"{occasion_field}
}}"""


# ── Main entry point ────────────────────────────────────────────────

async def get_fortune(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: Optional[int] = None,
    occasion: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Comprehensive fortune analysis using BaZi + Gemini 3 Pro.

    Returns a dict ready to be mapped onto ``FortuneResponse``.
    """
    today = date.today()

    # ── BaZi calculation (pure Python) ──
    pillars = destiny_service.calculate_bazi(
        birth_year, birth_month, birth_day, birth_hour,
    )
    day_master_str, _ = destiny_service.analyze_day_master(pillars)
    five_elements = destiny_service.count_five_elements(pillars)
    favorable_cn = destiny_service.get_favorable_element(pillars)
    favorable_en = _CN_TO_EN.get(favorable_cn, "earth")

    # Day master's own element
    day_pillar = pillars[2]
    dm_element_en = STEM_ELEMENTS.get(day_pillar.heavenly, "earth")
    dm_element_cn = ELEMENT_NAMES.get(dm_element_en, "土")

    # ── Today's stem-branch ──
    today_pillar = destiny_service.calculate_day_pillar(
        today.year, today.month, today.day,
    )
    today_sb = f"{today_pillar.heavenly}{today_pillar.earthly}"
    today_stem_en = STEM_ELEMENTS.get(today_pillar.heavenly, "earth")
    today_branch_en = BRANCH_ELEMENTS.get(today_pillar.earthly, "earth")
    today_element_cn = ELEMENT_NAMES.get(today_stem_en, "土")

    # ── Personalized lucky colors ──
    lucky_colors = _personal_lucky_colors(
        favorable_cn=favorable_cn,
        five_elements=five_elements,
        today_element_en=today_stem_en,
    )

    # ── Personalized base fortune score ──
    base_score = _base_fortune_score(
        day_master_element=dm_element_en,
        today_stem_element=today_stem_en,
        today_branch_element=today_branch_en,
        favorable_en=favorable_en,
    )

    # ── Build prompt & call Gemini 3 Pro ──
    bazi_str = " ".join(f"{p.heavenly}{p.earthly}" for p in pillars)
    five_elements_str = ", ".join(
        f"{ELEMENT_NAMES[k]}{v}" for k, v in five_elements.items()
    )

    prompt = _build_fortune_prompt(
        bazi_str=bazi_str,
        day_master=day_master_str,
        day_master_element_cn=dm_element_cn,
        five_elements_str=five_elements_str,
        favorable=favorable_cn,
        today_str=today.strftime("%Y年%m月%d日"),
        today_sb=today_sb,
        today_element=today_element_cn,
        base_score=base_score,
        occasion=occasion,
    )

    system = _SYSTEM_PROMPT.format(base_score=base_score)

    raw = await openai_service.generate_destiny_text(
        prompt=prompt,
        system_prompt=system,
        temperature=0.7,
        max_tokens=4000,
    )

    # ── Parse JSON ──
    try:
        txt = raw.strip()
        if "```" in txt:
            txt = txt.split("```")[1]
            if txt.startswith("json"):
                txt = txt[4:]
            txt = txt.split("```")[0]
        result = json.loads(txt.strip())
    except Exception:
        result = {
            "personality": "命理分析暂不可用，请稍后再试。",
            "destiny_overview": "",
            "fortune_summary": "今日运势分析暂不可用。",
            "fortune_score": base_score,
            "fortune_areas": {
                "事业": "平稳", "感情": "平稳", "财运": "平稳", "健康": "注意休息",
            },
            "outfit_suggestions": "建议穿着舒适自然的服装。",
            "energy_tips": "保持正面心态，顺其自然。",
        }

    # ── Assemble response dict ──
    bazi_chart = [
        {"heavenly": p.heavenly, "earthly": p.earthly} for p in pillars
    ]

    return {
        "date": today.strftime("%Y年%m月%d日"),
        "bazi_chart": bazi_chart,
        "day_master": day_master_str,
        "five_elements": {ELEMENT_NAMES[k]: v for k, v in five_elements.items()},
        "favorable_element": favorable_cn,
        "personality": result.get("personality", ""),
        "destiny_overview": result.get("destiny_overview", ""),
        "daily_stem_branch": today_sb,
        "daily_element": today_element_cn,
        "fortune_summary": result.get("fortune_summary", ""),
        "fortune_score": int(result.get("fortune_score", base_score)),
        "fortune_areas": result.get("fortune_areas", {}),
        "lucky_colors": lucky_colors,
        "outfit_suggestions": result.get("outfit_suggestions", ""),
        "energy_tips": result.get("energy_tips", ""),
        "occasion_special": result.get("occasion_special") if occasion else None,
    }

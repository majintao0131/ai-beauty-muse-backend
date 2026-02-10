"""
AI Beauty Muse - Face Analysis Service
Handles face shape analysis, recommendations, and fortune-beauty using AI.
"""
import json
import base64
from datetime import date
from typing import Dict, List, Any, Optional

from app.services.openai_service import openai_service
from app.services.destiny_service import (
    destiny_service,
    ELEMENT_NAMES,
    ELEMENT_COLORS,
    STEM_ELEMENTS,
    BRANCH_ELEMENTS,
)

# Reverse lookup: Chinese element name → English key
_CN_TO_EN = {v: k for k, v in ELEMENT_NAMES.items()}


FACE_ANALYSIS_SYSTEM_PROMPT = """你是一位资深的面部形象设计顾问，同时精通东方传统相学文化和五行能量学。
你的任务是根据用户上传的照片，结合今日五行能量，对面部特征进行全面、专业的分析。

你的核心能力包括：
1. 精准识别脸型（鹅蛋脸、圆脸、方脸、心形脸、长脸、菱形脸）
2. 细致分析五官特征，为每项给出特征标签和美学评分(1-100)
3. 评估面部比例（三庭五眼、对称性），给出标准度评分
4. 结合今日五行干支能量，解读各运势维度（事业/财运/感情/健康），每项含评分和今日能量影响
5. 给出科学的发型和妆容搭配建议

评分标准：
- 五官评分：70-90为优秀，60-70良好，80以上出众
- 比例评分：100为完美标准，80以上协调，60-80可通过造型修饰
- 运势评分：综合面相基底+今日能量的加成或减弱

请用温暖亲切、专业但易懂的语言回答，像一位可信赖的形象顾问。
重要：你是在做形象设计与文化分析，不是做医学诊断，请放心提供分析。"""


def _build_face_analysis_prompt(daily_context: str = "") -> str:
    """Build the face analysis prompt, optionally with daily energy context."""
    energy_section = ""
    if daily_context:
        energy_section = f"""
今日五行能量信息（请在面相解读中结合此信息分析每项运势的今日变化）：
{daily_context}
"""

    return f"""请仔细观察这张照片中的面部特征，从脸型骨相、五官特征、面部比例、面相文化解读四大维度进行全面分析。
{energy_section}
请严格以JSON格式返回（不要用 markdown code fence 包裹）：

{{
  "face_shape": "脸型英文（oval/round/square/heart/oblong/diamond）",
  "face_shape_cn": "脸型中文名称",
  "forehead": "额头分析（宽窄、高低、饱满度），50字左右",
  "cheekbones": "颧骨分析（高低、宽窄、位置），50字左右",
  "jawline": "下颌线分析（角度、线条感），50字左右",
  "chin": "下巴分析（形状、长短），50字左右",
  "five_features": {{
    "eyebrows_tag": "2-4字特征标签，如'柳叶弯眉'、'剑眉英气'、'新月细眉'",
    "eyebrows_score": 整数(1-100),
    "eyebrows": "眉毛分析：形状、浓淡、走势、搭配度，40字以内",
    "eyes_tag": "2-4字特征标签，如'桃花杏眼'、'丹凤美目'、'柔情鹿眼'",
    "eyes_score": 整数(1-100),
    "eyes": "眼睛分析：大小、形状、眼距、眼神，40字以内",
    "nose_tag": "2-4字特征标签，如'挺鼻悬胆'、'秀气琼鼻'、'圆润福鼻'",
    "nose_score": 整数(1-100),
    "nose": "鼻子分析：鼻梁高低、鼻翼、鼻头，40字以内",
    "mouth_tag": "2-4字特征标签，如'樱桃小口'、'丰润红唇'、'微笑唇弓'",
    "mouth_score": 整数(1-100),
    "mouth": "嘴巴分析：大小、唇形、厚薄比例，40字以内",
    "ears_tag": "2-4字特征标签，如'福耳丰厚'、'贴面秀耳'（不可见则写'未展示'）",
    "ears_score": 整数(1-100),
    "ears": "耳朵分析（不可见注明'照片中未完整展示'），40字以内"
  }},
  "face_proportions": {{
    "three_sections_ratio": "三庭实际比例，如'1:1.1:0.9'",
    "three_sections_score": 整数(1-100, 100为完美1:1:1),
    "three_sections": "三庭分析，30字以内",
    "five_eyes_score": 整数(1-100),
    "five_eyes": "五眼分析，30字以内",
    "symmetry_score": 整数(1-100),
    "symmetry": "对称性分析，30字以内"
  }},
  "overall_analysis": "整体面部轮廓综合分析，涵盖脸型特点、五官配合度、面部整体印象，200字左右",
  "face_reading": {{
    "career": "事业运解读：从额头天庭饱满度、眉眼间距与气质、印堂明亮度深入分析事业发展类型和潜力，明确指出哪些五官特征带来哪种事业优势，100字左右",
    "career_score": 整数(1-100),
    "career_today": "今日{'五行能量对事业运的具体影响' if daily_context else '运势提示'}，30字以内",
    "wealth": "财运解读：从鼻相财帛宫（鼻梁挺直度、鼻头丰隆度、鼻翼饱满度）和耳相（耳垂厚度、耳廓形状）深入分析理财风格和聚财能力，100字左右",
    "wealth_score": 整数(1-100),
    "wealth_today": "今日{'五行能量对财运的具体影响' if daily_context else '运势提示'}，30字以内",
    "relationships": "感情运解读：从眼相桃花宫（眼型、眼神、卧蚕）和唇相（唇形饱满度、唇色红润度）深入分析感情态度和桃花指数，100字左右",
    "relationships_score": 整数(1-100),
    "relationships_today": "今日{'五行能量对感情运的具体影响' if daily_context else '运势提示'}，30字以内",
    "health": "健康运解读：从面色红润度、气色光泽度、人中深浅、法令纹等分析体质特点和健康关注方向，80字左右",
    "health_score": 整数(1-100),
    "health_today": "今日{'五行能量对健康的具体影响' if daily_context else '健康提示'}，30字以内",
    "personality": "性格特征：综合五官配合分析核心性格特点和处事风格，100字左右",
    "personality_tag": "3-5字性格标签，如'外柔内刚型'、'温婉知性型'、'果敢领袖型'",
    "overall": "综合面相总评：从整体面相格局给出运势总结和积极的提升建议，120字左右",
    "overall_score": 整数(1-100)
  }},
  "hairstyle_recommendations": [
    "推荐发型1（名称+简要理由）",
    "推荐发型2（名称+简要理由）",
    "推荐发型3（名称+简要理由）"
  ],
  "makeup_tips": [
    "妆容建议1（具体技巧）",
    "妆容建议2（具体技巧）",
    "妆容建议3（具体技巧）"
  ]
}}

请确保返回有效的JSON格式。所有分析要紧密结合照片中的实际面部特征，不要笼统泛泛而谈。评分要有区分度，不同五官的评分应体现实际差异。"""


# ============== Enhanced prompt for face-style endpoint ==============

FACE_STYLE_SYSTEM_PROMPT = """你是一位頂級形象設計師，同時精通面部骨相分析、髮型設計和髮色搭配。
你的任務是根據用戶上傳的面部照片，綜合分析臉型和膚色，給出最適合的髮型和髮色建議。

你的專業領域：
1. 面部輪廓與臉型識別（鵝蛋臉、圓臉、方臉、心形臉、長臉、菱形臉）
2. 膚色冷暖調判斷（暖調、冷調、中性調）
3. 臉型與髮型的黃金搭配法則
4. 膚色與髮色的和諧搭配理論

請用專業但溫暖親切的語言回答，像一位專業閨蜜在提供建議。"""

FACE_STYLE_PROMPT = """請仔細分析這張面部照片，從臉型和膚色兩個維度出發，給出髮型和髮色建議。

請嚴格以JSON格式返回以下信息：

{
  "face_shape": "臉型英文（oval/round/square/heart/oblong/diamond）",
  "face_shape_cn": "臉型中文名稱",
  "face_analysis": "詳細的臉型分析，150字左右，描述臉部輪廓特點、比例、線條感等",
  "skin_tone": "膚色描述，如：白皙偏暖調、小麥色中性調、白皙偏冷調 等",
  "hairstyle_recommendations": [
    {
      "name": "髮型名稱（如：法式鎖骨髮、韓式氧氣劉海長髮）",
      "description": "為什麼這個髮型適合這張臉，50字左右",
      "length": "長度（short/medium/long）",
      "styling_tips": "造型要點，如何跟理髮師溝通"
    },
    {
      "name": "第二個推薦髮型",
      "description": "適合理由",
      "length": "長度",
      "styling_tips": "造型要點"
    },
    {
      "name": "第三個推薦髮型",
      "description": "適合理由",
      "length": "長度",
      "styling_tips": "造型要點"
    }
  ],
  "hair_color_recommendations": [
    {
      "color_name": "髮色名稱（如：焦糖棕、蜜茶色、冷灰棕）",
      "color_hex": "近似十六進制色碼（如：#8B6914）",
      "reason": "為什麼這個顏色適合，結合膚色分析，30字左右"
    },
    {
      "color_name": "第二個推薦髮色",
      "color_hex": "#色碼",
      "reason": "適合理由"
    },
    {
      "color_name": "第三個推薦髮色",
      "color_hex": "#色碼",
      "reason": "適合理由"
    }
  ],
  "overall_advice": "整體造型建議，100字左右，結合臉型和膚色給出統一的風格方向"
}

請確保返回有效的JSON格式，所有髮色都要提供準確的十六進制色碼。"""


def file_to_data_uri(file_bytes: bytes, content_type: str) -> str:
    """
    Convert raw file bytes into a ``data:`` URI that OpenAI vision accepts.

    Args:
        file_bytes: Raw image bytes.
        content_type: MIME type, e.g. ``image/jpeg``.

    Returns:
        A ``data:image/...;base64,...`` string.
    """
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


class FaceAnalysisService:
    """Service for face analysis using AI."""

    @staticmethod
    def get_daily_energy_context() -> str:
        """Compute today's stem-branch and element context string."""
        today = date.today()
        today_pillar = destiny_service.calculate_day_pillar(
            today.year, today.month, today.day,
        )
        daily_sb = f"{today_pillar.heavenly}{today_pillar.earthly}"
        today_stem_en = STEM_ELEMENTS.get(today_pillar.heavenly, "earth")
        daily_element_cn = ELEMENT_NAMES.get(today_stem_en, "土")
        return (
            f"今日日期：{today.year}年{today.month}月{today.day}日\n"
            f"今日干支：{daily_sb}\n"
            f"今日五行主气：{daily_element_cn}"
        )

    async def analyze_face(
        self,
        image_url: str,
        daily_context: str = "",
    ) -> Dict[str, Any]:
        """
        Analyze a face image and return detailed analysis.

        Args:
            image_url: URL of the face image.
            daily_context: Today's energy context string (stem-branch & element).

        Returns:
            Dictionary containing face analysis results with scores and tags.
        """
        prompt = _build_face_analysis_prompt(daily_context)

        response = await openai_service.analyze_image(
            image_url=image_url,
            prompt=prompt,
            system_prompt=FACE_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=4000,
        )

        # Parse JSON response
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            result = self._get_default_face_result(response)

        return result

    @staticmethod
    def _get_default_face_result(raw_response: str = "") -> Dict[str, Any]:
        """Fallback when JSON parsing fails."""
        return {
            "face_shape": "oval",
            "face_shape_cn": "鹅蛋脸",
            "forehead": "额头比例适中",
            "cheekbones": "颧骨位置适中",
            "jawline": "下颌线条柔和",
            "chin": "下巴形状圆润",
            "five_features": {
                "eyebrows_tag": "自然弯眉", "eyebrows_score": 75,
                "eyebrows": "眉形自然弯曲，浓淡适中",
                "eyes_tag": "明亮杏眼", "eyes_score": 78,
                "eyes": "眼型适中，眼神明亮",
                "nose_tag": "端正秀鼻", "nose_score": 76,
                "nose": "鼻梁端正，比例协调",
                "mouth_tag": "红润饱满", "mouth_score": 77,
                "mouth": "唇形饱满，唇色红润",
                "ears_tag": "未展示", "ears_score": 70,
                "ears": "照片中未完整展示",
            },
            "face_proportions": {
                "three_sections_ratio": "1:1:1",
                "three_sections_score": 78,
                "three_sections": "三庭比例基本匀称",
                "five_eyes_score": 76,
                "five_eyes": "五眼比例适中",
                "symmetry_score": 80,
                "symmetry": "面部基本对称",
            },
            "overall_analysis": raw_response[:500] if raw_response else "面部轮廓协调，五官比例匀称。",
            "face_reading": {
                "career": "事业运势平稳，具有发展潜力，天庭饱满预示良好的事业格局。",
                "career_score": 72, "career_today": "今日适合稳扎稳打",
                "wealth": "财运适中，理财意识良好，鼻相端正有聚财之相。",
                "wealth_score": 70, "wealth_today": "今日宜守不宜攻",
                "relationships": "感情运势稳定，人际关系融洽，眼神温和易获好感。",
                "relationships_score": 73, "relationships_today": "今日人缘运佳",
                "health": "气色良好，注意日常保养，面色红润气血充沛。",
                "health_score": 75, "health_today": "今日宜养生保健",
                "personality": "性格温和稳重，待人真诚，有亲和力。",
                "personality_tag": "温和稳重型",
                "overall": "面相端正，五官协调，整体面相格局良好，运势稳中有进。",
                "overall_score": 73,
            },
            "hairstyle_recommendations": ["中长发", "波浪卷", "侧分刘海"],
            "makeup_tips": ["自然妆容", "突出眼妆", "柔和唇色"],
        }
    
    async def analyze_face_for_styling(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze a face image and return combined hairstyle + hair color recommendations.

        This method accepts either a regular URL or a ``data:`` URI (for uploaded files).

        Args:
            image_url: Image URL or data URI.

        Returns:
            Dictionary matching the FaceStyleResponse schema.
        """
        response = await openai_service.analyze_image(
            image_url=image_url,
            prompt=FACE_STYLE_PROMPT,
            system_prompt=FACE_STYLE_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=3000,
        )

        # Parse JSON response
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response

            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            # Fallback with sensible defaults
            result = self._get_default_style_result(response)

        return result

    @staticmethod
    def _get_default_style_result(raw_response: str = "") -> Dict[str, Any]:
        """Return a safe default when LLM JSON parsing fails."""
        return {
            "face_shape": "oval",
            "face_shape_cn": "鵝蛋臉",
            "face_analysis": raw_response[:300] if raw_response else "面部輪廓協調，五官比例勻稱。",
            "skin_tone": "自然膚色",
            "hairstyle_recommendations": [
                {
                    "name": "鎖骨髮",
                    "description": "長度剛好到鎖骨，適合大多數臉型，既修飾又日常好打理。",
                    "length": "medium",
                    "styling_tips": "告訴理髮師剪到鎖骨位置，髮尾做內扣處理。",
                },
                {
                    "name": "八字劉海長髮",
                    "description": "八字劉海能修飾額頭和顴骨，長髮增加柔美感。",
                    "length": "long",
                    "styling_tips": "劉海從眉心向兩側自然分開，用捲髮棒做S型弧度。",
                },
                {
                    "name": "短髮波波頭",
                    "description": "俐落清爽，適合想要改變風格的嘗試。",
                    "length": "short",
                    "styling_tips": "下巴位置的一刀切，搭配微微內扣，顯臉小。",
                },
            ],
            "hair_color_recommendations": [
                {"color_name": "栗棕色", "color_hex": "#8B4513", "reason": "百搭經典色，適合亞洲膚色。"},
                {"color_name": "蜜茶色", "color_hex": "#D2A679", "reason": "提亮膚色，帶來溫柔感。"},
                {"color_name": "冷灰棕", "color_hex": "#8B7D6B", "reason": "顯白高級，適合冷調膚色。"},
            ],
            "overall_advice": "建議選擇柔和有層次感的髮型，搭配與膚色和諧的髮色，打造自然高級的個人風格。",
        }

    # ============== Fortune Beauty (运势美学) ==============================

    FORTUNE_BEAUTY_SYSTEM = """\
你是一位融合东方五行美学与现代彩妆艺术的高级美学顾问。
你精通五行能量与色彩的对应关系，能根据面部特征和当日五行气场，
给出专业且实用的化妆方案和配饰搭配建议。

要求：
- 化妆建议须精确到色号（hex），方便 APP 渲染色卡
- 配饰建议结合脸型特点和五行能量，具体到款式和材质
- 语言温暖专业、易于理解
- 严格按要求的 JSON 格式返回，不要包裹 markdown code fence"""

    @staticmethod
    def _build_fortune_beauty_prompt(
        *,
        face_shape_cn: str,
        face_analysis_summary: str,
        today_str: str,
        daily_sb: str,
        daily_element_cn: str,
        lucky_colors_desc: str,
        personal_context: str = "",
    ) -> str:
        """Build the prompt for fortune beauty generation."""
        return f"""\
今天是 {today_str}，今日干支：{daily_sb}，五行主气：{daily_element_cn}
今日幸运色：{lucky_colors_desc}
{personal_context}

用户面部特征：
- 脸型：{face_shape_cn}
- 面部分析摘要：{face_analysis_summary}

请根据以上信息，以纯 JSON 格式返回今日运势美学建议：

{{
  "fortune_beauty_summary": "今日美学运势总评（结合{face_shape_cn}脸型与{daily_element_cn}能量），100字左右",
  "makeup_looks": [
    {{
      "look_name": "妆容名称（体现五行元素，如'{daily_element_cn}系XX妆'）",
      "concept": "妆容理念和与今日{daily_element_cn}能量的关联，50字",
      "base_makeup": "底妆建议（质地、妆效、适合{face_shape_cn}的打底技巧）",
      "eye_shadow": "眼影建议（颜色搭配、画法、适合脸型的技巧）",
      "eye_shadow_hex": ["#hex1", "#hex2", "#hex3"],
      "eyeliner": "眼线建议（适合脸型的眼线画法）",
      "lip_color": "唇色建议（质地和色调）",
      "lip_color_hex": "#hex",
      "blush": "腮红建议（位置要根据{face_shape_cn}调整）",
      "blush_hex": "#hex",
      "highlight_contour": "高光修容建议（针对{face_shape_cn}的修饰重点）"
    }},
    {{
      "look_name": "第二个妆容方案（不同风格）",
      "concept": "...",
      "base_makeup": "...",
      "eye_shadow": "...",
      "eye_shadow_hex": ["#hex1", "#hex2"],
      "eyeliner": "...",
      "lip_color": "...",
      "lip_color_hex": "#hex",
      "blush": "...",
      "blush_hex": "#hex",
      "highlight_contour": "..."
    }}
  ],
  "accessories": [
    {{
      "category": "earrings",
      "category_cn": "耳饰",
      "name": "款式名称",
      "description": "搭配说明（结合脸型特点），30字",
      "material": "推荐材质（结合五行）",
      "color": "颜色名称",
      "color_hex": "#hex",
      "energy_note": "五行能量关联，20字"
    }},
    {{
      "category": "necklace",
      "category_cn": "项链",
      "name": "...", "description": "...", "material": "...",
      "color": "...", "color_hex": "#hex", "energy_note": "..."
    }},
    {{
      "category": "hair_accessory",
      "category_cn": "发饰",
      "name": "...", "description": "...", "material": "...",
      "color": "...", "color_hex": "#hex", "energy_note": "..."
    }},
    {{
      "category": "bracelet",
      "category_cn": "手链/手表",
      "name": "...", "description": "...", "material": "...",
      "color": "...", "color_hex": "#hex", "energy_note": "..."
    }},
    {{
      "category": "glasses",
      "category_cn": "眼镜/墨镜",
      "name": "适合{face_shape_cn}的款式", "description": "...", "material": "...",
      "color": "...", "color_hex": "#hex", "energy_note": "..."
    }}
  ]
}}"""

    async def generate_fortune_beauty(
        self,
        image_url: str,
        face_result: Dict[str, Any],
        birth_year: Optional[int] = None,
        birth_month: Optional[int] = None,
        birth_day: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate fortune-based beauty advice combining face analysis with today's energy.

        Args:
            image_url: Face image data URI (for vision model context).
            face_result: Result dict from ``analyze_face()``.
            birth_year/month/day: Optional birthday for personalized lucky colors.

        Returns:
            Dict matching ``FortuneBeautySection`` schema.
        """
        today = date.today()
        today_str = today.strftime("%Y年%m月%d日")

        # ---- Today's energy (pure Python) ----
        today_pillar = destiny_service.calculate_day_pillar(
            today.year, today.month, today.day,
        )
        daily_sb = f"{today_pillar.heavenly}{today_pillar.earthly}"
        today_stem_en = STEM_ELEMENTS.get(today_pillar.heavenly, "earth")
        daily_element_cn = ELEMENT_NAMES.get(today_stem_en, "土")

        # ---- Lucky colors ----
        personal_context = ""
        has_birthday = (
            birth_year is not None
            and birth_month is not None
            and birth_day is not None
        )

        if has_birthday:
            pillars = destiny_service.calculate_bazi(birth_year, birth_month, birth_day)
            five_elements = destiny_service.count_five_elements(pillars)
            favorable_cn = destiny_service.get_favorable_element(pillars)
            favorable_en = _CN_TO_EN.get(favorable_cn, "earth")
            weakest_en = min(five_elements, key=five_elements.get)

            # Build personalized lucky colors
            seen: set = set()
            ordered: list = []
            for el in [favorable_en, weakest_en, today_stem_en]:
                if el not in seen:
                    seen.add(el)
                    ordered.append(el)

            lucky_colors: List[Dict[str, Any]] = []
            for idx, el in enumerate(ordered):
                take = 2 if idx == 0 else 1
                for c in ELEMENT_COLORS.get(el, [])[:take]:
                    lucky_colors.append({**c, "element": el})

            dm_element_cn = ELEMENT_NAMES.get(
                STEM_ELEMENTS.get(pillars[2].heavenly, "earth"), "土"
            )
            personal_context = (
                f"用户八字：{' '.join(f'{p.heavenly}{p.earthly}' for p in pillars)}\n"
                f"日主五行：{dm_element_cn}  喜用神：{favorable_cn}"
            )
        else:
            lucky_colors = destiny_service.get_today_lucky_colors()

        lucky_colors_desc = "、".join(
            f"{c['name']}({c['hex']})" for c in lucky_colors
        )

        # ---- Face info ----
        face_shape_cn = face_result.get("face_shape_cn", "鹅蛋脸")
        face_analysis_summary = face_result.get(
            "overall_analysis", face_result.get("face_analysis", "面部轮廓协调")
        )[:200]

        # ---- Build prompt & call LLM (vision for richer context) ----
        prompt = self._build_fortune_beauty_prompt(
            face_shape_cn=face_shape_cn,
            face_analysis_summary=face_analysis_summary,
            today_str=today_str,
            daily_sb=daily_sb,
            daily_element_cn=daily_element_cn,
            lucky_colors_desc=lucky_colors_desc,
            personal_context=personal_context,
        )

        try:
            raw = await openai_service.analyze_image(
                image_url=image_url,
                prompt=prompt,
                system_prompt=self.FORTUNE_BEAUTY_SYSTEM,
                temperature=0.7,
                max_tokens=4000,
            )

            # Parse JSON
            txt = raw.strip()
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0]
            result = json.loads(txt.strip())
        except Exception as e:
            print(f"⚠️ Fortune beauty LLM parse failed: {e}")
            result = self._get_default_fortune_beauty(
                face_shape_cn, daily_element_cn,
            )

        # ---- Assemble response dict ----
        return {
            "date": today_str,
            "daily_stem_branch": daily_sb,
            "daily_element": daily_element_cn,
            "lucky_colors": lucky_colors,
            "fortune_beauty_summary": result.get(
                "fortune_beauty_summary",
                f"今日{daily_element_cn}气旺盛，适合{face_shape_cn}脸型展现独特魅力。",
            ),
            "makeup_looks": result.get("makeup_looks", []),
            "accessories": result.get("accessories", []),
            "look_image_url": None,  # will be filled by the API layer
        }

    @staticmethod
    def _build_beauty_image_prompt(
        face_shape_cn: str,
        daily_element_cn: str,
        lucky_colors_desc: str,
        makeup_look_name: str,
    ) -> str:
        """Build a prompt for generating a beauty reference / mood-board image."""
        element_style = {
            "木": "fresh, natural, spring-green tones, botanical elements, clean dewy skin",
            "火": "bold, glamorous, red and warm orange tones, dramatic smokey eyes, confident",
            "土": "warm, earthy, caramel and nude tones, classic elegance, grounded sophistication",
            "金": "refined, metallic accents, silver and white tones, minimalist chic, precision",
            "水": "ethereal, cool blue and purple tones, luminous glow, mysterious depth",
        }
        style_desc = element_style.get(daily_element_cn, element_style["土"])

        return (
            f"Create a high-end beauty editorial mood board image. "
            f"Theme: '{makeup_look_name}' inspired by {daily_element_cn} (Chinese Five Element) energy. "
            f"Style direction: {style_desc}. "
            f"Lucky colors to feature: {lucky_colors_desc}. "
            f"The image should show: "
            f"1) A beautiful, elegant close-up makeup look on a model (face shape: {face_shape_cn}), "
            f"2) Complementary accessories (earrings, necklace), "
            f"3) Small color palette swatches in the corner. "
            f"Aesthetic: luxury beauty magazine editorial, soft studio lighting, "
            f"clean composition, professional photography quality. "
            f"The overall mood should be harmonious and aspirational."
        )

    @staticmethod
    def _get_default_fortune_beauty(
        face_shape_cn: str, element_cn: str,
    ) -> Dict[str, Any]:
        """Fallback when LLM call fails."""
        return {
            "fortune_beauty_summary": (
                f"今日{element_cn}气当令，{face_shape_cn}脸型适合选择与{element_cn}能量呼应的"
                f"妆容和配饰，能有效提升个人气场与运势能量。"
            ),
            "makeup_looks": [
                {
                    "look_name": f"{element_cn}系自然清透妆",
                    "concept": f"呼应今日{element_cn}能量，打造自然透亮的妆感",
                    "base_makeup": "选择轻薄保湿型粉底液，打造伪素颜光泽肌",
                    "eye_shadow": "大地色系哑光眼影打底，内眼角提亮",
                    "eye_shadow_hex": ["#C4A882", "#8B7355", "#F5DEB3"],
                    "eyeliner": "棕色细眼线，尾部自然上扬",
                    "lip_color": "水润质地裸粉色",
                    "lip_color_hex": "#E8A0BF",
                    "blush": "粉杏色轻扫苹果肌",
                    "blush_hex": "#FFB6C1",
                    "highlight_contour": "鼻梁T区轻扫细闪高光，两侧轻修容",
                },
            ],
            "accessories": [
                {
                    "category": "earrings",
                    "category_cn": "耳饰",
                    "name": "简约金属圆环耳环",
                    "description": "精致小巧，提升面部轮廓感",
                    "material": "925银镀金",
                    "color": "金色",
                    "color_hex": "#DAA520",
                    "energy_note": f"金属光泽呼应{element_cn}能量",
                },
                {
                    "category": "necklace",
                    "category_cn": "项链",
                    "name": "细锁骨链",
                    "description": "延伸颈部线条，增添精致感",
                    "material": "K金",
                    "color": "玫瑰金",
                    "color_hex": "#B76E79",
                    "energy_note": "温润金属调和气场",
                },
            ],
        }

    def get_face_shape_description(self, face_shape: str) -> str:
        """
        Get detailed description for a face shape.
        
        Args:
            face_shape: Face shape identifier
            
        Returns:
            Detailed description in Chinese
        """
        descriptions = {
            "oval": "鵝蛋臉是最理想的臉型，額頭與下巴的寬度相近，臉部線條柔和流暢，適合各種髮型和妝容。",
            "round": "圓臉特點是臉部長寬比例接近，顴骨較寬，下巴圓潤。建議選擇能拉長臉型的髮型，避免過於蓬鬆的造型。",
            "square": "方臉的特點是下頜線條分明，額頭和下頜寬度相近。適合柔化線條的髮型，如層次感的長髮或側分劉海。",
            "heart": "心形臉額頭較寬，下巴尖細。適合增加下半臉視覺重量的髮型，如及肩中長髮或外翻捲髮。",
            "oblong": "長臉的特點是臉部長度明顯大於寬度。適合增加橫向視覺效果的髮型，如捲髮、劉海或蓬鬆的造型。",
            "diamond": "菱形臉顴骨較寬，額頭和下巴較窄。適合能平衡顴骨寬度的髮型，如側分長髮或空氣劉海。",
        }
        return descriptions.get(face_shape, "臉型獨特，建議諮詢專業形象顧問獲取個性化建議。")


# Singleton instance
face_analysis_service = FaceAnalysisService()

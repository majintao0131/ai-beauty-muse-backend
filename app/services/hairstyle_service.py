"""
AI Beauty Muse - Hairstyle Service
Handles AI hairstyle generation, hair color, and stylist card generation.
"""
import json
from typing import Dict, List, Any, Optional, Tuple

from app.services.openai_service import openai_service


# ------------------------------------------------------------------ #
#                        髮型參數映射                                  #
# ------------------------------------------------------------------ #

HAIR_LENGTH_MAP = {
    "short": "短髮（耳上到下巴）",
    "medium": "中長髮（肩膀到鎖骨）",
    "long": "長髮（胸部以下）",
}

HAIR_CURL_MAP = {
    "straight": "直髮",
    "wavy": "微捲/波浪捲",
    "curly": "捲髮/螺旋捲",
}

HAIR_BANGS_MAP = {
    "none": "無劉海/露額",
    "full": "齊劉海",
    "side": "斜劉海/側分",
    "curtain": "八字劉海/窗簾劉海",
}


# ------------------------------------------------------------------ #
#        色值 → 國際標準染髮色號 映射（文檔 §2.2 規範）                   #
# ------------------------------------------------------------------ #

# 色調判定表（根據 warmth = (R - B) / 255）
_TONE_TABLE: List[Tuple[float, str, str]] = [
    # (threshold_lower, tone_code, tone_name)
    (0.25,  "/34", "金銅 (Gold-Copper)"),
    (0.12,  "/3",  "金 (Gold)"),
    (0.05,  "/73", "焦糖暖棕 (Caramel)"),
    (-0.05, "/0",  "自然 (Natural)"),
    (-0.12, "/12", "灰紫 (Ash-Violet)"),
]
_TONE_FALLBACK = ("/1", "灰藍 (Ash)")


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Parse #RRGGBB to (R, G, B) ints."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (128, 100, 80)  # safe fallback
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_to_level(hex_color: str) -> int:
    """根據亮度計算染髮色度 (1-10)。"""
    r, g, b = hex_to_rgb(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return max(1, min(10, round(luminance * 9) + 1))


def hex_to_tone(hex_color: str) -> Tuple[str, str]:
    """根據暖度 (R-B)/255 判定色調代碼和名稱。"""
    r, _, b = hex_to_rgb(hex_color)
    warmth = (r - b) / 255.0
    for threshold, code, name in _TONE_TABLE:
        if warmth > threshold:
            return code, name
    return _TONE_FALLBACK


def get_color_formula(hex_color: str, color_name: str, skin_tone: str = "") -> Dict[str, Any]:
    """
    完整的色值 → 專業色號映射。

    Returns a dict matching the ColorFormula schema.
    """
    level = hex_to_level(hex_color)
    tone_code, tone_name = hex_to_tone(hex_color)
    formula_code = f"{level}{tone_code}"

    # 品牌映射（文檔 §2.2）
    if level <= 7:
        brand_main = f"Wella Koleston Perfect {formula_code}"
        brand_alt = f"L'Oréal Majirel {formula_code.replace('/', '.')}"
        bleach_required = False
        bleach_level = 0
    else:
        brand_main = f"Wella Illumina Color {formula_code}"
        brand_alt = f"L'Oréal Inoa {formula_code.replace('/', '.')}"
        bleach_required = True
        bleach_level = 1

    # 染色停留時間
    processing_time = "35-40分鐘" if not bleach_required else "脫色30分鐘 + 上色35-40分鐘"

    # 色彩能量描述
    energy_note = (
        f"此髮色採用{color_name}色系，{tone_name}色調，"
        f"Level {level} 級別。"
    )
    if skin_tone:
        energy_note += f"搭配{skin_tone}，能夠營造自然和諧的整體效果。"
    energy_note += "在自然光下呈現溫暖光澤。"

    return {
        "formula_code": formula_code,
        "formula_name": f"{color_name}（{tone_name} Level {level}）",
        "brand_reference": brand_main,
        "brand_alt": brand_alt,
        "bleach_required": bleach_required,
        "bleach_level": bleach_level,
        "processing_time": processing_time,
        "energy_note": energy_note,
    }


# ------------------------------------------------------------------ #
#              AI Prompt: 修剪指導 + 造型指南 + 局部細節                 #
# ------------------------------------------------------------------ #

_STYLIST_CARD_SYSTEM_PROMPT = """你是一位資深美髮技術總監，同時精通面部骨相與髮型設計的關係。
你的任務是根據用戶已選定的髮型方案和臉型分析，生成一份面向專業理髮師的技術溝通卡。

你的核心能力：
1. 根據臉型骨相分析，確定最佳外輪廓線和視覺重心位置
2. 使用國際通用的專業修剪術語（滑剪 Sliding Cut、層次剪 Layered Cut、點剪 Point Cut、紋理剪 Texturizing 等）
3. 給出精確的局部處理建議（劉海、鬢角、髮尾、層次等）
4. 推薦適合的造型工具和產品

請確保所有建議與用戶之前收到的 AI 髮型推薦完全一致，不要給出矛盾的建議。"""


def _build_stylist_card_prompt(
    hairstyle_name: str,
    hairstyle_description: str,
    hairstyle_length: str,
    styling_tips: str,
    color_name: str,
    face_shape: str,
    face_shape_cn: str,
    face_analysis: str,
    skin_tone: str,
) -> str:
    length_cn = HAIR_LENGTH_MAP.get(hairstyle_length, hairstyle_length)
    return f"""用戶已選定以下髮型方案，請生成專業理髮師溝通卡內容。

【選定方案】
- 髮型名稱：{hairstyle_name}
- 髮型描述：{hairstyle_description}
- 長度分類：{length_cn}
- 造型技巧（來自AI推薦）：{styling_tips}
- 選定髮色：{color_name}

【用戶臉型信息】
- 臉型：{face_shape_cn}（{face_shape}）
- 臉型分析：{face_analysis or '未提供'}
- 膚色：{skin_tone or '未提供'}

請嚴格以JSON格式返回以下信息：

{{
  "cutting_guide": {{
    "outline": "根據{face_shape_cn}骨相分析，此方案的外輪廓設計說明（如何修飾臉型），80字左右",
    "technique": "核心修剪技法說明，包含至少2種專業術語（如滑剪、層次剪、點剪、紋理剪等），並說明使用位置和目的，100字左右",
    "weight_balance": "視覺重心定位說明，描述重心相對於臉部特徵（如下頜線、顴骨）的位置，以及這樣做的修飾效果，60字左右",
    "key_points": [
      "關鍵修剪要點1（針對特定區域的處理要求）",
      "關鍵修剪要點2",
      "關鍵修剪要點3",
      "'{hairstyle_description}'（保留原始AI推薦描述作為要點之一）"
    ]
  }},
  "styling_guide": {{
    "daily_routine": "基於'{styling_tips}'擴展的日常打理步驟說明，100字左右",
    "products": ["護色洗髮水", "修護精華油", "（再推薦2-3個適合此髮型的產品）"],
    "tools": ["（推薦2-3個造型工具，含具體規格如卷髮棒直徑mm）"],
    "maintenance_cycle": "補染和修剪的週期建議，50字左右"
  }},
  "detail_notes": [
    {{
      "area": "區域名稱（如髮尾、鬢角、劉海、頭頂層次等）",
      "note": "該區域的具體處理要求和美學目標"
    }},
    {{
      "area": "第二個重點區域",
      "note": "處理要求"
    }},
    {{
      "area": "第三個重點區域",
      "note": "處理要求"
    }}
  ]
}}

要求：
1. 所有建議必須與用戶之前收到的AI髮型推薦（上方造型技巧和描述）保持完全一致
2. 使用專業但理髮師能理解的術語
3. cutting_guide.key_points 至少包含3個要點
4. detail_notes 至少包含2個局部區域
5. 請確保返回有效的JSON格式"""


class HairstyleService:
    """Service for AI hairstyle generation and recommendations."""
    
    async def generate_hairstyle(
        self,
        image_url: str,
        length: str,
        curl: str,
        bangs: str,
        additional_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a hairstyle recommendation based on face image and preferences.
        
        Args:
            image_url: URL of the face image
            length: Desired hair length
            curl: Desired curl type
            bangs: Desired bangs style
            additional_notes: Additional styling notes
            
        Returns:
            Dictionary containing hairstyle generation results
        """
        length_cn = HAIR_LENGTH_MAP.get(length, "中長髮")
        curl_cn = HAIR_CURL_MAP.get(curl, "直髮")
        bangs_cn = HAIR_BANGS_MAP.get(bangs, "無劉海")
        
        # 分析面部並生成髮型建議
        analysis_prompt = f"""請分析這張面部照片，並根據以下髮型偏好生成專業的髮型建議：

髮型偏好：
- 長度：{length_cn}
- 捲度：{curl_cn}
- 劉海：{bangs_cn}
{f'- 額外要求：{additional_notes}' if additional_notes else ''}

請以JSON格式返回以下信息：
{{
  "hairstyle_name": "髮型名稱（如：法式波波頭、韓式空氣劉海長髮等）",
  "hairstyle_description": "髮型詳細描述，150字左右，包括長度、層次、捲度、劉海等細節",
  "styling_tips": ["造型技巧1", "造型技巧2", "造型技巧3"],
  "maintenance_tips": ["護理建議1", "護理建議2", "護理建議3"],
  "suitable_face_shapes": ["適合的臉型1", "適合的臉型2"],
  "face_analysis": "根據照片分析此髮型與臉型的匹配度"
}}

請確保返回有效的JSON格式。"""

        system_prompt = """你是一位專業的髮型設計師，精通各種髮型設計和臉型分析。
請根據用戶的面部特徵和髮型偏好，提供專業、實用的髮型建議。
建議要具體、可操作，讓用戶可以直接拿給理髮師參考。"""

        response = await openai_service.analyze_image(
            image_url=image_url,
            prompt=analysis_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
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
        except:
            result = self._get_default_hairstyle(length, curl, bangs)
        
        # 生成髮型效果圖的提示詞
        image_prompt = self._create_image_prompt(
            result.get("hairstyle_description", ""),
            length_cn,
            curl_cn,
            bangs_cn,
        )
        
        # 嘗試生成髮型效果圖
        try:
            generated_image_url = await openai_service.generate_image(
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                style="natural",
            )
        except Exception as e:
            # 如果圖片生成失敗，返回佔位圖
            generated_image_url = "https://via.placeholder.com/1024x1024.png?text=Hairstyle+Preview"
        
        return {
            "generated_image_url": generated_image_url,
            "hairstyle_name": result.get("hairstyle_name", f"{length_cn}{curl_cn}"),
            "hairstyle_description": result.get("hairstyle_description", ""),
            "styling_tips": result.get("styling_tips", ["使用捲髮棒打造捲度", "使用定型噴霧固定", "吹風機吹出蓬鬆感"]),
            "maintenance_tips": result.get("maintenance_tips", ["每週使用髮膜護理", "避免過度使用熱工具", "定期修剪髮尾"]),
            "suitable_face_shapes": result.get("suitable_face_shapes", ["鵝蛋臉", "圓臉"]),
        }
    
    def _create_image_prompt(
        self,
        description: str,
        length: str,
        curl: str,
        bangs: str,
    ) -> str:
        """
        Create a prompt for generating hairstyle image.
        
        Args:
            description: Hairstyle description
            length: Hair length in Chinese
            curl: Curl type in Chinese
            bangs: Bangs style in Chinese
            
        Returns:
            Image generation prompt
        """
        return f"""Professional hairstyle portrait photo of an Asian woman with {length}, {curl}, {bangs}.
{description}
High-quality salon photography, natural lighting, clean background, showing the hairstyle from a flattering angle.
Professional hair styling, glossy and healthy-looking hair, modern and trendy hairstyle."""
    
    def _get_default_hairstyle(
        self,
        length: str,
        curl: str,
        bangs: str,
    ) -> Dict[str, Any]:
        """
        Get default hairstyle recommendation.
        
        Args:
            length: Hair length
            curl: Curl type
            bangs: Bangs style
            
        Returns:
            Default hairstyle dictionary
        """
        length_cn = HAIR_LENGTH_MAP.get(length, "中長髮")
        curl_cn = HAIR_CURL_MAP.get(curl, "直髮")
        bangs_cn = HAIR_BANGS_MAP.get(bangs, "無劉海")
        
        return {
            "hairstyle_name": f"{length_cn}{curl_cn}",
            "hairstyle_description": f"這是一款{length_cn}造型，搭配{curl_cn}和{bangs_cn}，整體風格自然時尚。髮尾帶有輕微層次，增加動感和蓬鬆感。",
            "styling_tips": [
                "使用捲髮棒或直板夾打造想要的捲度",
                "使用定型噴霧或髮蠟固定造型",
                "吹風機配合圓梳吹出蓬鬆感",
            ],
            "maintenance_tips": [
                "每週使用一次髮膜深層護理",
                "避免過度使用熱工具，使用前噴護熱噴霧",
                "每6-8週修剪一次髮尾，保持髮型形狀",
            ],
            "suitable_face_shapes": ["鵝蛋臉", "圓臉", "心形臉"],
        }
    
    async def generate_hair_color(
        self,
        image_url: str,
        color_name: str,
        color_hex: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate hair color preview and recommendations.
        
        Args:
            image_url: URL of the face image
            color_name: Desired hair color name
            color_hex: Specific hex color code
            
        Returns:
            Dictionary containing hair color results
        """
        # 分析髮色適合度
        analysis_prompt = f"""請分析這張照片中人物的膚色，判斷「{color_name}」這個髮色是否適合。

請以JSON格式返回以下信息：
{{
  "color_analysis": "髮色適合度分析，150字左右，包括與膚色的搭配、整體效果等",
  "complementary_makeup": ["搭配妝容建議1", "搭配妝容建議2", "搭配妝容建議3"],
  "maintenance_tips": ["髮色護理建議1", "髮色護理建議2", "髮色護理建議3"]
}}

請確保返回有效的JSON格式。"""

        system_prompt = """你是一位專業的髮色顧問，精通髮色與膚色的搭配。
請根據用戶的膚色特徵，分析所選髮色的適合度，並提供專業建議。"""

        response = await openai_service.analyze_image(
            image_url=image_url,
            prompt=analysis_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
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
        except:
            result = {
                "color_analysis": f"{color_name}是一個時尚的髮色選擇，建議諮詢專業髮型師了解更多細節。",
                "complementary_makeup": ["自然裸妝", "大地色眼影", "裸色唇膏"],
                "maintenance_tips": ["使用護色洗髮水", "避免頻繁洗頭", "定期補染"],
            }
        
        # 生成髮色效果圖
        image_prompt = f"""Professional hair color portrait photo of an Asian woman with {color_name} hair color.
Beautiful, glossy, healthy-looking dyed hair. High-quality salon photography, natural lighting, 
showing the hair color from multiple angles. Modern and trendy hair coloring."""
        
        try:
            generated_image_url = await openai_service.generate_image(
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                style="natural",
            )
        except:
            generated_image_url = "https://via.placeholder.com/1024x1024.png?text=Hair+Color+Preview"
        
        return {
            "generated_image_url": generated_image_url,
            "color_name": color_name,
            "color_analysis": result.get("color_analysis", ""),
            "complementary_makeup": result.get("complementary_makeup", []),
            "maintenance_tips": result.get("maintenance_tips", []),
        }
    
    async def generate_stylist_card(
        self,
        hairstyle_name: str,
        hairstyle_description: str,
        hairstyle_length: str,
        styling_tips: str,
        color_name: str,
        color_hex: str,
        face_shape: str,
        face_shape_cn: str,
        face_analysis: str = "",
        skin_tone: str = "",
        effect_image_url: str = "",
    ) -> Dict[str, Any]:
        """
        Generate a professional stylist communication card.

        Combines:
        - **Deterministic** colour-formula mapping (hex → professional formula)
        - **AI-generated** cutting guide, styling guide, and detail notes

        All AI-generated content is prompted with the *same* data the user
        previously received from the face-style / face-edit endpoints, so the
        card stays 100 % consistent with the effect photo.

        Returns:
            Dictionary matching the StylistCardResponse schema.
        """

        # -------- 1. Deterministic: colour formula --------
        color_formula = get_color_formula(color_hex, color_name, skin_tone)

        # -------- 2. AI: cutting guide + styling guide + detail notes --------
        prompt = _build_stylist_card_prompt(
            hairstyle_name=hairstyle_name,
            hairstyle_description=hairstyle_description,
            hairstyle_length=hairstyle_length,
            styling_tips=styling_tips,
            color_name=color_name,
            face_shape=face_shape,
            face_shape_cn=face_shape_cn,
            face_analysis=face_analysis,
            skin_tone=skin_tone,
        )

        response = await openai_service.generate_text(
            prompt=prompt,
            system_prompt=_STYLIST_CARD_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=3000,
        )

        # Parse JSON
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            ai_result = json.loads(json_str.strip())
        except (json.JSONDecodeError, IndexError):
            ai_result = self._get_default_stylist_card(
                hairstyle_name, hairstyle_description, styling_tips, face_shape_cn,
            )

        # -------- 3. Assemble final response --------
        cutting_raw = ai_result.get("cutting_guide", {})
        cutting_guide = {
            "outline": cutting_raw.get("outline", f"基於{face_shape_cn}骨相設計的外輪廓方案。"),
            "technique": cutting_raw.get("technique", "採用層次剪 (Layered Cut) 結合紋理剪 (Texturizing) 處理。"),
            "weight_balance": cutting_raw.get("weight_balance", "視覺重心位於下頜線附近。"),
            "key_points": cutting_raw.get("key_points", [hairstyle_description]),
        }

        styling_raw = ai_result.get("styling_guide", {})
        styling_guide = {
            "daily_routine": styling_raw.get("daily_routine", styling_tips),
            "products": styling_raw.get("products", ["護色洗髮水", "修護精華油", "彈力捲髮素"]),
            "tools": styling_raw.get("tools", ["32mm陶瓷卷髮棒", "防熱噴霧", "鬃毛圓梳"]),
            "maintenance_cycle": styling_raw.get(
                "maintenance_cycle", "建議每6-8週補染髮根，定期使用護色產品。"
            ),
        }

        detail_notes = ai_result.get("detail_notes", [
            {"area": "髮尾", "note": "保持自然垂墜感"},
            {"area": "鬢角", "note": "自然貼合臉部輪廓"},
        ])

        return {
            "card_image_url": None,  # 長圖合成暫不實現
            "cutting_guide": cutting_guide,
            "color_formula": color_formula,
            "styling_guide": styling_guide,
            "detail_notes": detail_notes,
        }

    @staticmethod
    def _get_default_stylist_card(
        hairstyle_name: str,
        hairstyle_description: str,
        styling_tips: str,
        face_shape_cn: str,
    ) -> Dict[str, Any]:
        """Fallback when AI JSON parsing fails."""
        return {
            "cutting_guide": {
                "outline": f"根據{face_shape_cn}骨相分析，此方案採用{hairstyle_name}的外輪廓設計，保持面部輪廓的自然流暢感。",
                "technique": "採用「滑剪 (Sliding Cut)」處理髮尾，結合「層次剪 (Layered Cut)」增加整體蓬鬆度。注意內層次與外輪廓的銜接自然過渡。",
                "weight_balance": f"視覺重心位於下頜線附近，以達到調整{face_shape_cn}比例的最佳效果。",
                "key_points": [
                    "鬢角處保持適當厚度",
                    "髮尾保持自然弧度",
                    hairstyle_description,
                ],
            },
            "styling_guide": {
                "daily_routine": styling_tips,
                "products": ["護色洗髮水", "修護精華油", "彈力捲髮素", "防熱噴霧"],
                "tools": ["32mm陶瓷卷髮棒", "防熱噴霧", "鬃毛圓梳"],
                "maintenance_cycle": "建議每6-8週補染髮根以維持最佳色澤，每4-6週修剪髮尾。",
            },
            "detail_notes": [
                {"area": "髮尾", "note": "保持自然垂墜感和弧度"},
                {"area": "鬢角", "note": "自然貼合臉部輪廓，與整體髮型和諧過渡"},
            ],
        }


# Singleton instance
hairstyle_service = HairstyleService()

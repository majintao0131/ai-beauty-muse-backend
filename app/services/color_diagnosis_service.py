"""
AI Beauty Muse - Color Diagnosis Service
Handles personal color analysis and recommendations using AI.
"""
import json
from typing import Dict, List, Any

from app.services.openai_service import openai_service


COLOR_DIAGNOSIS_SYSTEM_PROMPT = """你是一位專業的個人色彩顧問，精通四季色彩理論和膚色分析。
你的任務是分析用戶的膚色、髮色和瞳孔顏色，判定其個人色彩季型，並提供專業的色彩搭配建議。

四季色彩類型：
- 春季型（Spring）：膚色暖調偏黃，適合明亮溫暖的顏色
- 夏季型（Summer）：膚色冷調偏粉，適合柔和冷調的顏色
- 秋季型（Autumn）：膚色暖調偏深，適合濃郁溫暖的顏色
- 冬季型（Winter）：膚色冷調清晰，適合鮮明冷調的顏色

分析時請注意：
1. 觀察膚色的冷暖調
2. 觀察膚色的明暗度
3. 觀察膚色的清濁度
4. 結合髮色和瞳孔顏色綜合判斷"""

COLOR_DIAGNOSIS_PROMPT = """請分析這張照片中人物的膚色，判定其個人色彩季型，並以JSON格式返回以下信息：

{
  "season_type": "季型英文（spring/summer/autumn/winter）",
  "season_type_cn": "季型中文名稱（如：暖調春季型）",
  "skin_undertone": "膚色底調英文（warm/cool/neutral）",
  "skin_undertone_cn": "膚色底調中文（暖調/冷調/中性調）",
  "best_colors": [
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"}
  ],
  "avoid_colors": [
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"}
  ],
  "neutral_colors": [
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"},
    {"name": "顏色名稱", "hex": "#十六進制色碼"}
  ],
  "makeup_colors": {
    "lip": [{"name": "唇色名稱", "hex": "#色碼"}, {"name": "唇色名稱", "hex": "#色碼"}],
    "eyeshadow": [{"name": "眼影色名稱", "hex": "#色碼"}, {"name": "眼影色名稱", "hex": "#色碼"}],
    "blush": [{"name": "腮紅色名稱", "hex": "#色碼"}, {"name": "腮紅色名稱", "hex": "#色碼"}]
  },
  "hair_colors": [
    {"name": "髮色名稱", "hex": "#色碼"},
    {"name": "髮色名稱", "hex": "#色碼"},
    {"name": "髮色名稱", "hex": "#色碼"}
  ],
  "analysis": "詳細的色彩分析說明，200字左右，包括為什麼判定為這個季型，以及穿搭建議"
}

請確保返回有效的JSON格式，所有顏色都要提供準確的十六進制色碼。"""


# 預設的季型色彩方案
SEASON_COLOR_PALETTES = {
    "spring": {
        "best_colors": [
            {"name": "珊瑚橙", "hex": "#FF7F50"},
            {"name": "桃粉", "hex": "#FFB6C1"},
            {"name": "嫩綠", "hex": "#98FB98"},
            {"name": "杏色", "hex": "#FFDAB9"},
            {"name": "淺金", "hex": "#FFD700"},
            {"name": "象牙白", "hex": "#FFFFF0"},
        ],
        "avoid_colors": [
            {"name": "黑色", "hex": "#000000"},
            {"name": "深紫", "hex": "#4B0082"},
            {"name": "冷灰", "hex": "#708090"},
        ],
        "neutral_colors": [
            {"name": "駝色", "hex": "#C19A6B"},
            {"name": "米白", "hex": "#F5F5DC"},
            {"name": "暖灰", "hex": "#A9A9A9"},
        ],
    },
    "summer": {
        "best_colors": [
            {"name": "薰衣草紫", "hex": "#E6E6FA"},
            {"name": "玫瑰粉", "hex": "#FFB6C1"},
            {"name": "天藍", "hex": "#87CEEB"},
            {"name": "薄荷綠", "hex": "#98FF98"},
            {"name": "淺灰藍", "hex": "#B0C4DE"},
            {"name": "珍珠白", "hex": "#F0EAD6"},
        ],
        "avoid_colors": [
            {"name": "橙色", "hex": "#FFA500"},
            {"name": "芥末黃", "hex": "#FFDB58"},
            {"name": "鐵鏽紅", "hex": "#B7410E"},
        ],
        "neutral_colors": [
            {"name": "藍灰", "hex": "#6699CC"},
            {"name": "玫瑰灰", "hex": "#C4AEAD"},
            {"name": "淺藕色", "hex": "#E8D0D0"},
        ],
    },
    "autumn": {
        "best_colors": [
            {"name": "南瓜橙", "hex": "#FF7518"},
            {"name": "橄欖綠", "hex": "#808000"},
            {"name": "酒紅", "hex": "#722F37"},
            {"name": "焦糖", "hex": "#FFD59A"},
            {"name": "咖啡", "hex": "#6F4E37"},
            {"name": "芥末黃", "hex": "#FFDB58"},
        ],
        "avoid_colors": [
            {"name": "粉紅", "hex": "#FFC0CB"},
            {"name": "純白", "hex": "#FFFFFF"},
            {"name": "冰藍", "hex": "#99FFFF"},
        ],
        "neutral_colors": [
            {"name": "卡其", "hex": "#C3B091"},
            {"name": "深駝", "hex": "#8B7355"},
            {"name": "橄欖灰", "hex": "#6B6B47"},
        ],
    },
    "winter": {
        "best_colors": [
            {"name": "正紅", "hex": "#FF0000"},
            {"name": "寶藍", "hex": "#0000FF"},
            {"name": "翡翠綠", "hex": "#50C878"},
            {"name": "紫羅蘭", "hex": "#8B00FF"},
            {"name": "純白", "hex": "#FFFFFF"},
            {"name": "純黑", "hex": "#000000"},
        ],
        "avoid_colors": [
            {"name": "橙色", "hex": "#FFA500"},
            {"name": "米色", "hex": "#F5F5DC"},
            {"name": "暖棕", "hex": "#8B4513"},
        ],
        "neutral_colors": [
            {"name": "冷灰", "hex": "#808080"},
            {"name": "海軍藍", "hex": "#000080"},
            {"name": "炭灰", "hex": "#36454F"},
        ],
    },
}


class ColorDiagnosisService:
    """Service for personal color diagnosis using AI."""
    
    async def diagnose_color(self, image_url: str) -> Dict[str, Any]:
        """
        Diagnose personal color type from an image.
        
        Args:
            image_url: URL of the face/skin image
            
        Returns:
            Dictionary containing color diagnosis results
        """
        response = await openai_service.analyze_image(
            image_url=image_url,
            prompt=COLOR_DIAGNOSIS_PROMPT,
            system_prompt=COLOR_DIAGNOSIS_SYSTEM_PROMPT,
            temperature=0.7,
        )
        
        # Parse JSON response
        try:
            # 嘗試提取 JSON 部分
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            result = json.loads(json_str.strip())
        except json.JSONDecodeError:
            # 如果解析失敗，返回默認結構（春季型）
            result = self._get_default_result("spring", response)
        
        return result
    
    def _get_default_result(self, season: str, analysis: str = "") -> Dict[str, Any]:
        """
        Get default result for a season type.
        
        Args:
            season: Season type
            analysis: Analysis text
            
        Returns:
            Default result dictionary
        """
        palette = SEASON_COLOR_PALETTES.get(season, SEASON_COLOR_PALETTES["spring"])
        season_names = {
            "spring": ("spring", "暖調春季型", "warm", "暖調"),
            "summer": ("summer", "冷調夏季型", "cool", "冷調"),
            "autumn": ("autumn", "暖調秋季型", "warm", "暖調"),
            "winter": ("winter", "冷調冬季型", "cool", "冷調"),
        }
        
        season_info = season_names.get(season, season_names["spring"])
        
        return {
            "season_type": season_info[0],
            "season_type_cn": season_info[1],
            "skin_undertone": season_info[2],
            "skin_undertone_cn": season_info[3],
            "best_colors": palette["best_colors"],
            "avoid_colors": palette["avoid_colors"],
            "neutral_colors": palette["neutral_colors"],
            "makeup_colors": {
                "lip": [{"name": "珊瑚", "hex": "#FF7F50"}, {"name": "玫瑰", "hex": "#FF007F"}],
                "eyeshadow": [{"name": "大地色", "hex": "#8B4513"}, {"name": "香檳", "hex": "#F7E7CE"}],
                "blush": [{"name": "蜜桃", "hex": "#FFCBA4"}, {"name": "珊瑚", "hex": "#FF7F50"}],
            },
            "hair_colors": [
                {"name": "栗棕", "hex": "#8B4513"},
                {"name": "焦糖", "hex": "#FFD59A"},
                {"name": "深巧克力", "hex": "#3D2314"},
            ],
            "analysis": analysis if analysis else f"您的膚色屬於{season_info[1]}，適合{season_info[3]}的顏色。",
        }
    
    def get_season_description(self, season_type: str) -> str:
        """
        Get detailed description for a season type.
        
        Args:
            season_type: Season type identifier
            
        Returns:
            Detailed description in Chinese
        """
        descriptions = {
            "spring": "春季型的特點是膚色明亮、透明感強，帶有溫暖的黃調。適合明亮、清新、溫暖的顏色，如珊瑚色、桃粉色、嫩綠色等。避免過於沉重或冷調的顏色。",
            "summer": "夏季型的特點是膚色柔和、帶有粉調，屬於冷調膚色。適合柔和、淡雅、冷調的顏色，如薰衣草紫、玫瑰粉、天藍色等。避免過於鮮豔或暖調的顏色。",
            "autumn": "秋季型的特點是膚色深沉、帶有金黃調，屬於暖調膚色。適合濃郁、大地色系的顏色，如南瓜橙、橄欖綠、酒紅色等。避免過於明亮或冷調的顏色。",
            "winter": "冬季型的特點是膚色清晰、對比度高，屬於冷調膚色。適合鮮明、純正、高對比的顏色，如正紅、寶藍、純白、純黑等。避免柔和或暖調的顏色。",
        }
        return descriptions.get(season_type, "請上傳照片進行色彩診斷。")


# Singleton instance
color_diagnosis_service = ColorDiagnosisService()

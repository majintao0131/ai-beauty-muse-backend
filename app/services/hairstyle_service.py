"""
AI Beauty Muse - Hairstyle Service
Handles AI hairstyle generation and recommendations.
"""
import json
from typing import Dict, List, Any, Optional

from app.services.openai_service import openai_service


# 髮型參數映射
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
        original_image_url: str,
        target_image_url: str,
        hairstyle_description: str,
        additional_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a communication card for the hairstylist.
        
        Args:
            original_image_url: Original photo URL
            target_image_url: Target hairstyle image URL
            hairstyle_description: Description of desired hairstyle
            additional_notes: Additional notes for stylist
            
        Returns:
            Dictionary containing stylist card information
        """
        prompt = f"""請根據以下信息，生成一份專業的理髮師溝通卡：

目標髮型描述：{hairstyle_description}
{f'額外要求：{additional_notes}' if additional_notes else ''}

請以JSON格式返回以下信息：
{{
  "summary": "給理髮師的簡要說明，50字左右",
  "key_points": ["重點1", "重點2", "重點3", "重點4"],
  "technical_terms": ["專業術語1", "專業術語2", "專業術語3"]
}}

請使用理髮師能理解的專業術語，確保溝通準確。"""

        system_prompt = """你是一位專業的髮型設計師，精通髮型設計的專業術語。
請幫助用戶生成一份專業的理髮師溝通卡，讓用戶能夠準確地向理髮師表達自己想要的髮型。"""

        response = await openai_service.generate_text(
            prompt=prompt,
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
                "summary": f"希望做{hairstyle_description}的造型",
                "key_points": ["保持自然感", "注意層次感", "劉海要輕盈", "髮尾要有動感"],
                "technical_terms": ["層次剪", "打薄", "紋理感"],
            }
        
        return {
            "card_image_url": target_image_url,  # 使用目標髮型圖作為卡片圖
            "summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "technical_terms": result.get("technical_terms", []),
        }


# Singleton instance
hairstyle_service = HairstyleService()

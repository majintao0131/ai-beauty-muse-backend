"""
AI Beauty Muse - Face Analysis Service
Handles face shape analysis and recommendations using AI.
"""
import json
from typing import Dict, List, Any

from app.services.openai_service import openai_service


FACE_ANALYSIS_SYSTEM_PROMPT = """你是一位專業的面相分析師和形象顧問，精通面部骨相學和東方面相學。
你的任務是分析用戶上傳的面部照片，提供專業的面部輪廓分析和形象建議。

分析時請注意：
1. 識別臉型（鵝蛋臉、圓臉、方臉、心形臉、長臉、菱形臉）
2. 分析額頭、顴骨、下頜線、下巴的特點
3. 結合東方面相學給出面相解讀
4. 提供適合的髮型和妝容建議

請用專業但易懂的語言回答，避免過於學術化的表達。"""

FACE_ANALYSIS_PROMPT = """請分析這張面部照片，並以JSON格式返回以下信息：

{
  "face_shape": "臉型英文（oval/round/square/heart/oblong/diamond）",
  "face_shape_cn": "臉型中文名稱",
  "forehead": "額頭分析（寬窄、高低、形狀特點）",
  "cheekbones": "顴骨分析（高低、寬窄、位置）",
  "jawline": "下頜線分析（角度、線條感）",
  "chin": "下巴分析（形狀、長短）",
  "overall_analysis": "整體面部輪廓分析，200字左右",
  "hairstyle_recommendations": ["推薦髮型1", "推薦髮型2", "推薦髮型3"],
  "makeup_tips": ["妝容建議1", "妝容建議2", "妝容建議3"],
  "face_reading": "面相解讀（事業、財運、感情等方面的簡要分析）"
}

請確保返回有效的JSON格式。"""


class FaceAnalysisService:
    """Service for face analysis using AI."""
    
    async def analyze_face(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze a face image and return detailed analysis.
        
        Args:
            image_url: URL of the face image
            
        Returns:
            Dictionary containing face analysis results
        """
        response = await openai_service.analyze_image(
            image_url=image_url,
            prompt=FACE_ANALYSIS_PROMPT,
            system_prompt=FACE_ANALYSIS_SYSTEM_PROMPT,
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
            # 如果解析失敗，返回默認結構
            result = {
                "face_shape": "oval",
                "face_shape_cn": "鵝蛋臉",
                "forehead": "額頭比例適中",
                "cheekbones": "顴骨位置適中",
                "jawline": "下頜線條柔和",
                "chin": "下巴形狀圓潤",
                "overall_analysis": response[:500] if len(response) > 500 else response,
                "hairstyle_recommendations": ["中長髮", "波浪捲", "側分劉海"],
                "makeup_tips": ["自然妝容", "突出眼妝", "柔和唇色"],
                "face_reading": "面相端正，五官協調",
            }
        
        return result
    
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

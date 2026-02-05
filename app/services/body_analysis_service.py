"""
AI Beauty Muse - Body Analysis Service
Handles body type analysis and styling recommendations.
"""
from typing import Dict, List, Any, Tuple

from app.services.openai_service import openai_service


class BodyAnalysisService:
    """Service for body type analysis and styling recommendations."""
    
    def calculate_body_type(
        self,
        height: int,
        bust: int,
        waist: int,
        hip: int,
    ) -> Tuple[str, str]:
        """
        Calculate body type based on measurements.
        
        Args:
            height: Height in cm
            bust: Bust measurement in cm
            waist: Waist measurement in cm
            hip: Hip measurement in cm
            
        Returns:
            Tuple of (body_type, body_type_cn)
        """
        # 計算比例
        bust_waist_diff = bust - waist
        hip_waist_diff = hip - waist
        bust_hip_diff = abs(bust - hip)
        
        # H型：胸腰臀差異不大，整體較直
        if bust_waist_diff < 20 and hip_waist_diff < 20 and bust_hip_diff < 10:
            return "H", "H型（直筒型）"
        
        # X型：胸臀豐滿，腰細
        if bust_waist_diff >= 25 and hip_waist_diff >= 25 and bust_hip_diff < 10:
            return "X", "X型（沙漏型）"
        
        # O型：腰部較粗，胸臀相對較小
        if waist >= bust - 5 and waist >= hip - 5:
            return "O", "O型（蘋果型）"
        
        # A型：臀部比胸部寬
        if hip > bust + 10:
            return "A", "A型（梨型）"
        
        # V型：肩寬胸大，臀部較窄
        if bust > hip + 10:
            return "V", "V型（倒三角型）"
        
        # 默認為 H 型
        return "H", "H型（直筒型）"
    
    def get_body_type_description(self, body_type: str) -> str:
        """
        Get description for a body type.
        
        Args:
            body_type: Body type identifier
            
        Returns:
            Description in Chinese
        """
        descriptions = {
            "H": "H型身材的特點是肩、腰、臀寬度相近，整體線條較為直線。這種身材的優勢是看起來修長挺拔，適合營造曲線感的穿搭。",
            "X": "X型身材是最經典的沙漏型身材，胸臀豐滿、腰部纖細。這種身材的優勢是曲線明顯，適合展現身材曲線的穿搭。",
            "O": "O型身材的特點是腰腹部較為豐滿，四肢相對纖細。穿搭重點是修飾腰腹，突出四肢優勢。",
            "A": "A型身材的特點是臀部和大腿較為豐滿，上半身相對纖細。穿搭重點是平衡上下身比例，突出上半身。",
            "V": "V型身材的特點是肩寬、胸部豐滿，臀部和腿部相對纖細。穿搭重點是平衡上下身，增加下半身視覺重量。",
        }
        return descriptions.get(body_type, "請輸入身材數據進行分析。")
    
    async def analyze_body(
        self,
        height: int,
        bust: int,
        waist: int,
        hip: int,
    ) -> Dict[str, Any]:
        """
        Analyze body type and provide styling recommendations.
        
        Args:
            height: Height in cm
            bust: Bust measurement in cm
            waist: Waist measurement in cm
            hip: Hip measurement in cm
            
        Returns:
            Dictionary containing body analysis results
        """
        # 計算身材類型
        body_type, body_type_cn = self.calculate_body_type(height, bust, waist, hip)
        
        # 使用 AI 生成詳細建議
        prompt = f"""根據以下身材數據，提供專業的穿搭建議：

身高：{height}cm
胸圍：{bust}cm
腰圍：{waist}cm
臀圍：{hip}cm
身材類型：{body_type_cn}

請以JSON格式返回以下信息：
{{
  "proportions": "身材比例分析，100字左右",
  "strengths": "身材優勢，需要突出的部位",
  "areas_to_enhance": "需要修飾的部位和方法",
  "recommended_silhouettes": ["推薦廓形1", "推薦廓形2", "推薦廓形3", "推薦廓形4"],
  "styles_to_avoid": "應避免的款式，100字左右",
  "accessories": "配飾建議，包括包包、鞋子、首飾等"
}}

請確保返回有效的JSON格式。"""

        system_prompt = """你是一位專業的形象顧問，精通身材分析和穿搭搭配。
請根據用戶的身材數據，提供專業、實用的穿搭建議。
建議要具體、可操作，避免過於籠統的表達。"""

        response = await openai_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        
        # Parse JSON response
        try:
            import json
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            ai_result = json.loads(json_str.strip())
        except:
            ai_result = self._get_default_recommendations(body_type)
        
        return {
            "body_type": body_type,
            "body_type_cn": body_type_cn,
            "body_type_description": self.get_body_type_description(body_type),
            "proportions": ai_result.get("proportions", "身材比例協調"),
            "strengths": ai_result.get("strengths", "整體線條流暢"),
            "areas_to_enhance": ai_result.get("areas_to_enhance", "可通過穿搭優化比例"),
            "recommended_silhouettes": ai_result.get("recommended_silhouettes", ["A字裙", "高腰褲", "V領上衣"]),
            "styles_to_avoid": ai_result.get("styles_to_avoid", "避免過於緊身或過於寬鬆的款式"),
            "accessories": ai_result.get("accessories", "選擇與身材比例協調的配飾"),
        }
    
    def _get_default_recommendations(self, body_type: str) -> Dict[str, Any]:
        """
        Get default recommendations for a body type.
        
        Args:
            body_type: Body type identifier
            
        Returns:
            Default recommendations dictionary
        """
        recommendations = {
            "H": {
                "proportions": "您的身材比例勻稱，肩、腰、臀寬度相近，整體線條流暢。",
                "strengths": "身材修長挺拔，適合展現簡約俐落的風格。",
                "areas_to_enhance": "可通過腰帶、收腰設計等營造腰線，增加曲線感。",
                "recommended_silhouettes": ["收腰連衣裙", "高腰闊腿褲", "腰帶搭配", "A字裙"],
                "styles_to_avoid": "避免過於寬鬆的直筒裙和無腰線設計的連衣裙。",
                "accessories": "選擇能強調腰線的腰帶，中等大小的包包，簡約的首飾。",
            },
            "X": {
                "proportions": "您擁有經典的沙漏型身材，胸臀豐滿、腰部纖細，曲線優美。",
                "strengths": "身材曲線明顯，是最理想的身材比例之一。",
                "areas_to_enhance": "適當展現曲線，避免過於寬鬆掩蓋身材優勢。",
                "recommended_silhouettes": ["修身連衣裙", "包臀裙", "高腰褲", "V領上衣"],
                "styles_to_avoid": "避免過於寬鬆的款式，會掩蓋身材優勢。",
                "accessories": "選擇精緻的首飾，中等大小的包包，高跟鞋更能展現曲線。",
            },
            "O": {
                "proportions": "您的腰腹部較為豐滿，四肢相對纖細，整體圓潤可愛。",
                "strengths": "四肢纖細是您的優勢，適合露出手臂和小腿。",
                "areas_to_enhance": "選擇能修飾腰腹的款式，如A字裙、帝國腰線設計。",
                "recommended_silhouettes": ["A字裙", "帝國腰連衣裙", "直筒褲", "V領上衣"],
                "styles_to_avoid": "避免緊身上衣、低腰褲和過於貼身的連衣裙。",
                "accessories": "選擇長項鏈拉長視覺，中大號包包，避免腰間配飾。",
            },
            "A": {
                "proportions": "您的臀部和大腿較為豐滿，上半身相對纖細，整體穩重。",
                "strengths": "上半身纖細是您的優勢，適合突出肩部和胸部。",
                "areas_to_enhance": "增加上半身視覺重量，選擇能平衡比例的款式。",
                "recommended_silhouettes": ["船領上衣", "泡泡袖", "A字裙", "直筒褲"],
                "styles_to_avoid": "避免緊身褲、包臀裙和過於貼身的下裝。",
                "accessories": "選擇醒目的耳環和項鏈，小號包包，避免臀部配飾。",
            },
            "V": {
                "proportions": "您的肩寬、胸部豐滿，臀部和腿部相對纖細，上身有力量感。",
                "strengths": "上半身線條有力量感，適合展現自信風格。",
                "areas_to_enhance": "增加下半身視覺重量，選擇能平衡比例的款式。",
                "recommended_silhouettes": ["V領上衣", "A字裙", "闊腿褲", "百褶裙"],
                "styles_to_avoid": "避免墊肩、泡泡袖和過於強調肩部的設計。",
                "accessories": "選擇長項鏈，中大號包包斜挎，腰帶強調腰線。",
            },
        }
        return recommendations.get(body_type, recommendations["H"])


# Singleton instance
body_analysis_service = BodyAnalysisService()

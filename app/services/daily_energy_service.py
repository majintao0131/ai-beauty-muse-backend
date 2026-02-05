"""
AI Beauty Muse - Daily Energy Service
Handles daily energy calculations and outfit recommendations.
"""
from datetime import date, datetime
from typing import Dict, List, Any, Optional

from app.services.destiny_service import destiny_service, ELEMENT_NAMES, ELEMENT_COLORS
from app.services.openai_service import openai_service


class DailyEnergyService:
    """Service for daily energy guidance and outfit recommendations."""
    
    def get_daily_stem_branch(self) -> str:
        """
        Get today's heavenly stem and earthly branch.
        
        Returns:
            Today's stem and branch as string
        """
        return destiny_service.get_today_stem_branch()
    
    def get_daily_element(self) -> str:
        """
        Get today's dominant element.
        
        Returns:
            Today's element name in Chinese
        """
        return destiny_service.get_today_element()
    
    def get_lucky_colors(self) -> List[Dict[str, str]]:
        """
        Get today's lucky colors.
        
        Returns:
            List of lucky colors with name and hex
        """
        return destiny_service.get_today_lucky_colors()
    
    async def get_daily_energy(
        self,
        occasion: Optional[str] = None,
        user_birth_year: Optional[int] = None,
        user_birth_month: Optional[int] = None,
        user_birth_day: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive daily energy guidance.
        
        Args:
            occasion: Special occasion for the day
            user_birth_year: User's birth year for personalization
            user_birth_month: User's birth month
            user_birth_day: User's birth day
            
        Returns:
            Dictionary containing daily energy guidance
        """
        today = date.today()
        daily_stem_branch = self.get_daily_stem_branch()
        daily_element = self.get_daily_element()
        lucky_colors = self.get_lucky_colors()
        
        # 如果有用戶生辰，計算個人化建議
        personal_context = ""
        if user_birth_year and user_birth_month and user_birth_day:
            pillars = destiny_service.calculate_bazi(
                user_birth_year, user_birth_month, user_birth_day
            )
            favorable = destiny_service.get_favorable_element(pillars)
            personal_context = f"用戶喜用神為{favorable}，"
        
        # 使用 AI 生成詳細建議
        prompt = f"""今天是{today.year}年{today.month}月{today.day}日，
今日干支：{daily_stem_branch}
今日五行主氣：{daily_element}
{personal_context}
{f'今日場合：{occasion}' if occasion else ''}

請以JSON格式返回以下信息：
{{
  "five_elements_energy": "今日五行能量分析，100字左右",
  "outfit_suggestions": "今日穿搭建議，150字左右，包括顏色、款式、風格",
  "makeup_tips": "今日妝容要點，100字左右",
  "energy_tips": "今日能量提示，100字左右，包括注意事項和開運建議"
  {f', "occasion_special": "針對{occasion}的特別建議，150字左右，包括戰袍方案"' if occasion else ''}
}}

請確保返回有效的JSON格式。"""

        system_prompt = """你是一位精通東方命理和時尚穿搭的能量顧問。
請根據今日的干支五行能量，結合用戶的場合需求，提供專業的穿搭和能量建議。
建議要具體、實用，讓用戶能夠直接參考執行。"""

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
            
            result = json.loads(json_str.strip())
        except:
            result = self._get_default_energy(daily_element, occasion)
        
        return {
            "date": today.strftime("%Y年%m月%d日"),
            "daily_stem_branch": daily_stem_branch,
            "five_elements_energy": result.get("five_elements_energy", f"今日{daily_element}氣旺盛"),
            "lucky_colors": lucky_colors,
            "outfit_suggestions": result.get("outfit_suggestions", ""),
            "makeup_tips": result.get("makeup_tips", ""),
            "energy_tips": result.get("energy_tips", ""),
            "occasion_special": result.get("occasion_special") if occasion else None,
        }
    
    def _get_default_energy(
        self,
        element: str,
        occasion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get default energy guidance.
        
        Args:
            element: Today's dominant element
            occasion: Special occasion
            
        Returns:
            Default energy dictionary
        """
        element_advice = {
            "木": {
                "five_elements_energy": "今日木氣旺盛，適合創新、開拓、學習新事物。木主生發，是展現活力和創意的好日子。",
                "outfit_suggestions": "建議穿著綠色系或藍色系服裝，展現清新活力。可選擇自然材質如棉麻，搭配簡約俐落的款式。",
                "makeup_tips": "妝容以清新自然為主，眼影選擇大地色或綠色系，唇色選擇裸粉或珊瑚色。",
                "energy_tips": "今日適合戶外活動、運動健身、學習充電。避免過度勞累，保持心情愉悅。",
            },
            "火": {
                "five_elements_energy": "今日火氣旺盛，適合社交、表達、展現自我。火主熱情，是展現魅力和領導力的好日子。",
                "outfit_suggestions": "建議穿著紅色系或橙色系服裝，展現熱情活力。可選擇亮眼的配飾，搭配大方得體的款式。",
                "makeup_tips": "妝容可以稍微濃郁，眼影選擇暖色系，唇色選擇正紅或橘紅色。",
                "energy_tips": "今日適合社交活動、演講表達、重要會議。注意控制情緒，避免過於衝動。",
            },
            "土": {
                "five_elements_energy": "今日土氣旺盛，適合穩定、積累、處理實務。土主穩重，是踏實做事和理財的好日子。",
                "outfit_suggestions": "建議穿著大地色系服裝，如駝色、米色、咖啡色，展現穩重可靠。款式選擇經典簡約。",
                "makeup_tips": "妝容以自然穩重為主，眼影選擇大地色系，唇色選擇豆沙色或裸色。",
                "energy_tips": "今日適合處理財務、簽約、規劃未來。保持耐心，穩紮穩打。",
            },
            "金": {
                "five_elements_energy": "今日金氣旺盛，適合決斷、執行、追求完美。金主果斷，是處理重要事務和做決定的好日子。",
                "outfit_suggestions": "建議穿著白色、銀色或金色系服裝，展現精緻優雅。可選擇金屬配飾，搭配俐落的款式。",
                "makeup_tips": "妝容以精緻為主，眼影選擇香檳色或銀色系，唇色選擇玫瑰色或裸粉色。",
                "energy_tips": "今日適合做重要決定、談判、追求目標。注意不要過於苛刻，保持彈性。",
            },
            "水": {
                "five_elements_energy": "今日水氣旺盛，適合思考、溝通、靈活應變。水主智慧，是學習和人際交流的好日子。",
                "outfit_suggestions": "建議穿著藍色系或黑色系服裝，展現深邃智慧。可選擇流暢的款式，搭配簡約的配飾。",
                "makeup_tips": "妝容以柔和為主，眼影選擇藍色或灰色系，唇色選擇莓果色或裸色。",
                "energy_tips": "今日適合學習、溝通、處理複雜事務。保持靈活，善用智慧解決問題。",
            },
        }
        
        advice = element_advice.get(element, element_advice["土"])
        
        if occasion:
            advice["occasion_special"] = f"針對{occasion}，建議選擇能展現專業和自信的穿搭，顏色以今日幸運色為主，搭配得體的配飾，展現最佳狀態。"
        
        return advice


# Singleton instance
daily_energy_service = DailyEnergyService()

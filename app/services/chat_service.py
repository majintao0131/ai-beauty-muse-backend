"""
AI Beauty Muse - Chat Service
Handles AI-powered beauty and styling chat assistant.

History is now loaded from the database by the API layer and passed in;
this service remains a pure AI-calling layer with no direct DB access.
"""
from typing import Dict, List, Any, Optional

from app.services.openai_service import openai_service


CHAT_SYSTEM_PROMPT = """你是 AI Beauty Muse 的智能美學助手「繆斯」，專精於以下領域：

1. **髮型設計**：各種髮型推薦、臉型與髮型搭配、髮色選擇、造型技巧
2. **妝容建議**：日常妝容、場合妝容、膚色與妝容搭配、化妝技巧
3. **穿搭搭配**：身材與穿搭、場合穿搭、色彩搭配、風格定位
4. **個人色彩**：四季色彩理論、膚色診斷、最佳用色建議
5. **命理能量**：五行色彩、每日能量、開運穿搭

你的特點：
- 專業但親切，用易懂的語言解釋專業知識
- 給出具體、可執行的建議，而非籠統的說法
- 結合東方美學和現代時尚，提供獨特視角
- 如果用戶上傳照片，會仔細分析並給出個性化建議

請用繁體中文回答，語氣溫暖親切，像一位專業又貼心的閨蜜。"""


class ChatService:
    """Service for AI-powered beauty chat assistant."""

    async def chat(
        self,
        message: str,
        image_url: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat message and return AI response.

        Args:
            message: User's current message.
            image_url: Optional image URL for visual context.
            conversation_history: Previous messages loaded from the DB
                (list of dicts with ``role`` and ``content``).

        Returns:
            Dictionary containing ``reply`` and ``suggestions``.
        """
        reply = await openai_service.chat_with_context(
            message=message,
            conversation_history=conversation_history,
            image_url=image_url,
            system_prompt=CHAT_SYSTEM_PROMPT,
        )

        suggestions = self._generate_suggestions(message, reply)

        return {
            "reply": reply,
            "suggestions": suggestions,
        }

    def _generate_suggestions(
        self,
        user_message: str,
        ai_reply: str,
    ) -> List[str]:
        """
        Generate follow-up suggestions based on the conversation.

        Args:
            user_message: User's message
            ai_reply: AI's reply

        Returns:
            List of follow-up suggestions (max 3)
        """
        suggestions = []

        # 髮型相關
        if any(word in user_message or word in ai_reply for word in ["髮型", "頭髮", "劉海", "捲髮", "直髮"]):
            suggestions.extend([
                "這個髮型需要怎麼打理？",
                "有沒有其他類似的髮型推薦？",
                "這個髮型適合什麼臉型？",
            ])

        # 妝容相關
        if any(word in user_message or word in ai_reply for word in ["妝容", "化妝", "眼影", "唇色", "腮紅"]):
            suggestions.extend([
                "有沒有推薦的產品？",
                "這個妝容適合什麼場合？",
                "怎麼讓妝容更持久？",
            ])

        # 穿搭相關
        if any(word in user_message or word in ai_reply for word in ["穿搭", "衣服", "搭配", "風格", "款式"]):
            suggestions.extend([
                "有沒有具體的單品推薦？",
                "這個風格適合什麼場合？",
                "怎麼用配飾提升整體造型？",
            ])

        # 色彩相關
        if any(word in user_message or word in ai_reply for word in ["顏色", "色彩", "膚色", "冷調", "暖調"]):
            suggestions.extend([
                "我適合什麼顏色的髮色？",
                "有沒有百搭的顏色推薦？",
                "怎麼判斷自己的膚色調？",
            ])

        # 默認建議
        if not suggestions:
            suggestions = [
                "幫我分析一下我的臉型",
                "今天穿什麼顏色比較好？",
                "有沒有適合我的髮型推薦？",
            ]

        return suggestions[:3]


# Singleton instance
chat_service = ChatService()

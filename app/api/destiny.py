"""
AI Beauty Muse - Destiny API Routes
Handles BaZi analysis, destiny-based color recommendations,
and comprehensive fortune reading (Gemini 3 Pro).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, require_quota
from app.models.database import get_db, User
from app.services.history_service import history_service
from app.models.schemas import (
    DestinyAnalysisRequest,
    DestinyAnalysisResponse,
    FortuneRequest,
    FortuneResponse,
    BaziPillar,
    ColorInfo,
)
from app.services.destiny_service import destiny_service, ELEMENT_NAMES
from app.services.openai_service import openai_service
from app.services.fortune_service import get_fortune


router = APIRouter(prefix="/destiny", tags=["Destiny"])


@router.post("/analyze", response_model=DestinyAnalysisResponse)
async def analyze_destiny(request: DestinyAnalysisRequest):
    """
    Analyze BaZi (八字) and provide destiny-based recommendations.
    
    - **birth_year**: Birth year (1900-2100)
    - **birth_month**: Birth month (1-12)
    - **birth_day**: Birth day (1-31)
    - **birth_hour**: Optional birth hour (0-23)
    
    Returns:
    - BaZi four pillars chart
    - Day master analysis
    - Five elements distribution
    - Favorable element (喜用神)
    - Color recommendations based on destiny
    - Hairstyle suggestions
    """
    try:
        # 計算八字
        pillars = destiny_service.calculate_bazi(
            year=request.birth_year,
            month=request.birth_month,
            day=request.birth_day,
            hour=request.birth_hour,
        )
        
        # 分析日主
        day_master, day_master_analysis = destiny_service.analyze_day_master(pillars)
        
        # 計算五行分布
        five_elements = destiny_service.count_five_elements(pillars)
        
        # 獲取喜用神
        favorable_element = destiny_service.get_favorable_element(pillars)
        
        # 獲取顏色建議
        enhance_colors, balance_colors, avoid_colors = destiny_service.get_color_recommendations(pillars)
        
        # 使用 AI 生成髮型建議
        prompt = f"""根據以下八字命理信息，提供髮型建議：

八字：{' '.join([f'{p.heavenly}{p.earthly}' for p in pillars])}
日主：{day_master}
五行分布：{', '.join([f'{ELEMENT_NAMES[k]}{v}' for k, v in five_elements.items()])}
喜用神：{favorable_element}

請提供150字左右的髮型建議，包括適合的髮型風格、長度、顏色等，要結合命理特點給出建議。"""

        hairstyle_suggestions = await openai_service.generate_text(
            prompt=prompt,
            system_prompt="你是一位精通命理和髮型設計的顧問，請根據用戶的八字命理特點，提供專業的髮型建議。",
            temperature=0.7,
            max_tokens=500,
        )
        
        # 生成整體分析
        overall_prompt = f"""根據以下八字命理信息，提供整體分析：

八字：{' '.join([f'{p.heavenly}{p.earthly}' for p in pillars])}
日主：{day_master}
五行分布：{', '.join([f'{ELEMENT_NAMES[k]}{v}' for k, v in five_elements.items()])}
喜用神：{favorable_element}

請提供200字左右的整體命理分析，包括性格特點、適合的風格定位、穿搭方向等。"""

        overall_analysis = await openai_service.generate_text(
            prompt=overall_prompt,
            system_prompt="你是一位專業的命理師，請根據用戶的八字，提供專業但易懂的命理分析，重點關注與形象、穿搭相關的建議。",
            temperature=0.7,
            max_tokens=500,
        )
        
        # 轉換為響應格式
        bazi_chart = [
            BaziPillar(heavenly=p.heavenly, earthly=p.earthly)
            for p in pillars
        ]
        
        return DestinyAnalysisResponse(
            bazi_chart=bazi_chart,
            day_master=day_master,
            five_elements={ELEMENT_NAMES[k]: v for k, v in five_elements.items()},
            favorable_element=favorable_element,
            enhance_colors=[ColorInfo(**c) for c in enhance_colors],
            balance_colors=[ColorInfo(**c) for c in balance_colors],
            avoid_colors=[ColorInfo(**c) for c in avoid_colors],
            hairstyle_suggestions=hairstyle_suggestions,
            overall_analysis=overall_analysis,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Destiny analysis failed: {str(e)}")


@router.post("/fortune", response_model=FortuneResponse)
async def analyze_fortune(
    request: FortuneRequest,
    _quota: dict = Depends(require_quota("destiny_color")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Comprehensive fortune analysis — **命理分析 + 今日运势** (Gemini 3 Pro).

    Takes a birthday (and optional birth hour / today's occasion) and returns:

    **命理分析（终身）**:
    - BaZi four-pillar chart
    - Personality traits
    - Destiny overview (career, love, wealth directions)
    - Favorable element (喜用神)

    **今日运势（当天）**:
    - Fortune score (1-100)
    - Fortune breakdown by area (事业 / 感情 / 财运 / 健康)
    - Lucky colors + outfit suggestions
    - Energy & mindset tips
    - Optional occasion-specific advice

    Powered by **Gemini 3 Pro** for deeper reasoning.
    """
    try:
        result = await get_fortune(
            birth_year=request.birth_year,
            birth_month=request.birth_month,
            birth_day=request.birth_day,
            birth_hour=request.birth_hour,
            occasion=request.occasion,
        )

        response = FortuneResponse(
            date=result["date"],
            bazi_chart=[BaziPillar(**p) for p in result["bazi_chart"]],
            day_master=result["day_master"],
            five_elements=result["five_elements"],
            favorable_element=result["favorable_element"],
            personality=result["personality"],
            destiny_overview=result["destiny_overview"],
            daily_stem_branch=result["daily_stem_branch"],
            daily_element=result["daily_element"],
            fortune_summary=result["fortune_summary"],
            fortune_score=result["fortune_score"],
            fortune_areas=result["fortune_areas"],
            lucky_colors=[ColorInfo(**c) for c in result["lucky_colors"]],
            outfit_suggestions=result["outfit_suggestions"],
            energy_tips=result["energy_tips"],
            occasion_special=result.get("occasion_special"),
        )

        # ---- Auto-save to history ----
        try:
            await history_service.save_report(
                db=db,
                user_id=current_user.id,
                report_type="destiny_fortune",
                title=f"命理运势 — {response.day_master}",
                data=response.model_dump(mode="json"),
                summary=response.fortune_summary[:100] if response.fortune_summary else None,
            )
        except Exception:
            pass

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fortune analysis failed: {str(e)}")

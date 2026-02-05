"""
AI Beauty Muse - Daily Energy API Routes
Handles daily energy guidance and outfit recommendations.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    DailyEnergyRequest,
    DailyEnergyResponse,
    ColorInfo,
)
from app.services.daily_energy_service import daily_energy_service


router = APIRouter(prefix="/daily", tags=["Daily Energy"])


@router.post("/energy", response_model=DailyEnergyResponse)
async def get_daily_energy(request: DailyEnergyRequest):
    """
    Get daily energy guidance and outfit recommendations.
    
    - **occasion**: Optional special occasion (e.g., "面試", "約會", "重要會議")
    - **user_birth_year**: Optional birth year for personalization
    - **user_birth_month**: Optional birth month
    - **user_birth_day**: Optional birth day
    
    Returns:
    - Today's date and stem-branch
    - Five elements energy analysis
    - Lucky colors for today
    - Outfit suggestions
    - Makeup tips
    - Energy tips
    - Special occasion advice (if applicable)
    """
    try:
        result = await daily_energy_service.get_daily_energy(
            occasion=request.occasion,
            user_birth_year=request.user_birth_year,
            user_birth_month=request.user_birth_month,
            user_birth_day=request.user_birth_day,
        )
        
        # Convert lucky colors to ColorInfo objects
        lucky_colors = [ColorInfo(**c) for c in result.get("lucky_colors", [])]
        
        return DailyEnergyResponse(
            date=result.get("date", ""),
            daily_stem_branch=result.get("daily_stem_branch", ""),
            five_elements_energy=result.get("five_elements_energy", ""),
            lucky_colors=lucky_colors,
            outfit_suggestions=result.get("outfit_suggestions", ""),
            makeup_tips=result.get("makeup_tips", ""),
            energy_tips=result.get("energy_tips", ""),
            occasion_special=result.get("occasion_special"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Daily energy calculation failed: {str(e)}")


@router.get("/quick")
async def get_quick_daily_info():
    """
    Get quick daily information without personalization.
    
    Returns basic daily energy info:
    - Today's stem-branch
    - Today's element
    - Lucky colors
    """
    try:
        stem_branch = daily_energy_service.get_daily_stem_branch()
        element = daily_energy_service.get_daily_element()
        lucky_colors = daily_energy_service.get_lucky_colors()
        
        return {
            "daily_stem_branch": stem_branch,
            "daily_element": element,
            "lucky_colors": [ColorInfo(**c) for c in lucky_colors],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick daily info failed: {str(e)}")

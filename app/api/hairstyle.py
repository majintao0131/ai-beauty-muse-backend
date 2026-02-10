"""
AI Beauty Muse - Hairstyle API Routes
Handles hairstyle generation, hair color, and stylist card endpoints.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_optional_user
from app.models.database import get_db, User
from app.services.history_service import history_service
from app.models.schemas import (
    HairstyleGenerationRequest,
    HairstyleGenerationResponse,
    HairColorRequest,
    HairColorResponse,
    StylistCardRequest,
    StylistCardResponse,
    CuttingGuide,
    ColorFormula,
    StylingGuide,
    DetailNote,
)
from app.services.hairstyle_service import hairstyle_service


router = APIRouter(prefix="/hairstyle", tags=["Hairstyle"])


@router.post("/generate", response_model=HairstyleGenerationResponse)
async def generate_hairstyle(request: HairstyleGenerationRequest):
    """
    Generate AI hairstyle recommendation based on face image and preferences.
    
    - **image_url**: URL of the face image
    - **length**: Desired hair length (short/medium/long)
    - **curl**: Desired curl type (straight/wavy/curly)
    - **bangs**: Desired bangs style (none/full/side/curtain)
    - **additional_notes**: Optional additional styling notes
    
    Returns:
    - Generated hairstyle preview image
    - Hairstyle name and description
    - Styling and maintenance tips
    - Suitable face shapes
    """
    try:
        result = await hairstyle_service.generate_hairstyle(
            image_url=request.image_url,
            length=request.length.value,
            curl=request.curl.value,
            bangs=request.bangs.value,
            additional_notes=request.additional_notes,
        )
        
        return HairstyleGenerationResponse(
            generated_image_url=result.get("generated_image_url", ""),
            hairstyle_name=result.get("hairstyle_name", ""),
            hairstyle_description=result.get("hairstyle_description", ""),
            styling_tips=result.get("styling_tips", []),
            maintenance_tips=result.get("maintenance_tips", []),
            suitable_face_shapes=result.get("suitable_face_shapes", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hairstyle generation failed: {str(e)}")


@router.post("/color", response_model=HairColorResponse)
async def experiment_hair_color(request: HairColorRequest):
    """
    Generate hair color preview and recommendations.
    
    - **image_url**: URL of the face image
    - **color_name**: Desired hair color name (e.g., "栗棕色", "蜜糖金")
    - **color_hex**: Optional specific hex color code
    
    Returns:
    - Generated hair color preview image
    - Color suitability analysis
    - Complementary makeup suggestions
    - Color maintenance tips
    """
    try:
        result = await hairstyle_service.generate_hair_color(
            image_url=request.image_url,
            color_name=request.color_name,
            color_hex=request.color_hex,
        )
        
        return HairColorResponse(
            generated_image_url=result.get("generated_image_url", ""),
            color_name=result.get("color_name", ""),
            color_analysis=result.get("color_analysis", ""),
            complementary_makeup=result.get("complementary_makeup", []),
            maintenance_tips=result.get("maintenance_tips", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hair color generation failed: {str(e)}")


@router.post("/stylist-card", response_model=StylistCardResponse)
async def generate_stylist_card(
    request: StylistCardRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a professional stylist communication card (理髮師溝通卡).

    This endpoint should be called **after** the user selects a hairstyle scheme
    from the face-style analysis results.  All input fields come from the prior
    ``/analysis/face-style`` and ``/analysis/face-edit`` responses so that the
    stylist card is **100 % consistent** with the AI-generated effect photo.

    **Returns**:
    - ``cutting_guide`` — professional cutting instructions based on bone-structure analysis
    - ``color_formula`` — international standard hair-color formula (e.g. Wella 6/34)
    - ``styling_guide`` — daily routine, products, tools, maintenance cycle
    - ``detail_notes`` — area-specific notes (bangs, ends, sideburns, layers …)
    - ``card_image_url`` — reserved for future composite-card image
    """
    try:
        result = await hairstyle_service.generate_stylist_card(
            hairstyle_name=request.hairstyle_name,
            hairstyle_description=request.hairstyle_description,
            hairstyle_length=request.hairstyle_length,
            styling_tips=request.styling_tips,
            color_name=request.color_name,
            color_hex=request.color_hex,
            face_shape=request.face_shape,
            face_shape_cn=request.face_shape_cn,
            face_analysis=request.face_analysis or "",
            skin_tone=request.skin_tone or "",
            effect_image_url=request.effect_image_url,
        )

        # Build nested response models
        cutting_raw = result.get("cutting_guide", {})
        color_raw = result.get("color_formula", {})
        styling_raw = result.get("styling_guide", {})
        notes_raw = result.get("detail_notes", [])

        response = StylistCardResponse(
            card_image_url=result.get("card_image_url"),
            cutting_guide=CuttingGuide(
                outline=cutting_raw.get("outline", ""),
                technique=cutting_raw.get("technique", ""),
                weight_balance=cutting_raw.get("weight_balance", ""),
                key_points=cutting_raw.get("key_points", []),
            ),
            color_formula=ColorFormula(
                formula_code=color_raw.get("formula_code", ""),
                formula_name=color_raw.get("formula_name", ""),
                brand_reference=color_raw.get("brand_reference", ""),
                brand_alt=color_raw.get("brand_alt", ""),
                bleach_required=color_raw.get("bleach_required", False),
                bleach_level=color_raw.get("bleach_level", 0),
                processing_time=color_raw.get("processing_time", ""),
                energy_note=color_raw.get("energy_note", ""),
            ),
            styling_guide=StylingGuide(
                daily_routine=styling_raw.get("daily_routine", ""),
                products=styling_raw.get("products", []),
                tools=styling_raw.get("tools", []),
                maintenance_cycle=styling_raw.get("maintenance_cycle", ""),
            ),
            detail_notes=[
                DetailNote(area=n.get("area", ""), note=n.get("note", ""))
                for n in notes_raw
            ],
        )

        # ---- Auto-save to history ----
        if current_user:
            try:
                await history_service.save_report(
                    db=db,
                    user_id=current_user.id,
                    report_type="stylist_card",
                    title=f"沟通卡 — {request.hairstyle_name}",
                    data=response.model_dump(mode="json"),
                    summary=f"{request.hairstyle_name} + {request.color_name}",
                    thumbnail_url=request.effect_image_url,
                )
            except Exception:
                pass

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stylist card generation failed: {str(e)}")

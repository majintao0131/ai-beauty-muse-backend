"""
AI Beauty Muse - Hairstyle API Routes
Handles hairstyle generation, hair color, and stylist card endpoints.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    HairstyleGenerationRequest,
    HairstyleGenerationResponse,
    HairColorRequest,
    HairColorResponse,
    StylistCardRequest,
    StylistCardResponse,
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
async def generate_stylist_card(request: StylistCardRequest):
    """
    Generate a communication card for the hairstylist.
    
    - **original_image_url**: URL of the original photo
    - **target_image_url**: URL of the target hairstyle image
    - **hairstyle_description**: Description of desired hairstyle
    - **additional_notes**: Optional additional notes for stylist
    
    Returns:
    - Card image URL
    - Summary for the stylist
    - Key points to communicate
    - Technical terms to use
    """
    try:
        result = await hairstyle_service.generate_stylist_card(
            original_image_url=request.original_image_url,
            target_image_url=request.target_image_url,
            hairstyle_description=request.hairstyle_description,
            additional_notes=request.additional_notes,
        )
        
        return StylistCardResponse(
            card_image_url=result.get("card_image_url", ""),
            summary=result.get("summary", ""),
            key_points=result.get("key_points", []),
            technical_terms=result.get("technical_terms", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stylist card generation failed: {str(e)}")

"""
AI Beauty Muse - Analysis API Routes
Handles face analysis, color diagnosis, and body analysis endpoints.
"""
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    FaceAnalysisRequest,
    FaceAnalysisResponse,
    ColorDiagnosisRequest,
    ColorDiagnosisResponse,
    BodyAnalysisRequest,
    BodyAnalysisResponse,
    ColorInfo,
)
from app.services.face_analysis_service import face_analysis_service
from app.services.color_diagnosis_service import color_diagnosis_service
from app.services.body_analysis_service import body_analysis_service


router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/face", response_model=FaceAnalysisResponse)
async def analyze_face(request: FaceAnalysisRequest):
    """
    Analyze face shape and provide recommendations.
    
    - **image_url**: URL of the face image to analyze
    
    Returns detailed face analysis including:
    - Face shape classification
    - Facial feature analysis
    - Hairstyle recommendations
    - Makeup tips
    - Face reading interpretation
    """
    try:
        result = await face_analysis_service.analyze_face(request.image_url)
        
        return FaceAnalysisResponse(
            face_shape=result.get("face_shape", "oval"),
            face_shape_cn=result.get("face_shape_cn", "鵝蛋臉"),
            forehead=result.get("forehead", ""),
            cheekbones=result.get("cheekbones", ""),
            jawline=result.get("jawline", ""),
            chin=result.get("chin", ""),
            overall_analysis=result.get("overall_analysis", ""),
            hairstyle_recommendations=result.get("hairstyle_recommendations", []),
            makeup_tips=result.get("makeup_tips", []),
            face_reading=result.get("face_reading"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face analysis failed: {str(e)}")


@router.post("/color", response_model=ColorDiagnosisResponse)
async def diagnose_color(request: ColorDiagnosisRequest):
    """
    Diagnose personal color type and provide color recommendations.
    
    - **image_url**: URL of the face/skin image to analyze
    
    Returns comprehensive color diagnosis including:
    - Personal color season type
    - Skin undertone analysis
    - Best colors to wear
    - Colors to avoid
    - Makeup color recommendations
    - Hair color recommendations
    """
    try:
        result = await color_diagnosis_service.diagnose_color(request.image_url)
        
        # Convert color dictionaries to ColorInfo objects
        best_colors = [ColorInfo(**c) for c in result.get("best_colors", [])]
        avoid_colors = [ColorInfo(**c) for c in result.get("avoid_colors", [])]
        neutral_colors = [ColorInfo(**c) for c in result.get("neutral_colors", [])]
        hair_colors = [ColorInfo(**c) for c in result.get("hair_colors", [])]
        
        # Convert makeup colors
        makeup_colors = {}
        for key, colors in result.get("makeup_colors", {}).items():
            makeup_colors[key] = [ColorInfo(**c) for c in colors]
        
        return ColorDiagnosisResponse(
            season_type=result.get("season_type", "spring"),
            season_type_cn=result.get("season_type_cn", "暖調春季型"),
            skin_undertone=result.get("skin_undertone", "warm"),
            skin_undertone_cn=result.get("skin_undertone_cn", "暖調"),
            best_colors=best_colors,
            avoid_colors=avoid_colors,
            neutral_colors=neutral_colors,
            makeup_colors=makeup_colors,
            hair_colors=hair_colors,
            analysis=result.get("analysis", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Color diagnosis failed: {str(e)}")


@router.post("/body", response_model=BodyAnalysisResponse)
async def analyze_body(request: BodyAnalysisRequest):
    """
    Analyze body type and provide styling recommendations.
    
    - **height**: Height in cm (100-250)
    - **bust**: Bust measurement in cm (50-150)
    - **waist**: Waist measurement in cm (40-150)
    - **hip**: Hip measurement in cm (50-150)
    
    Returns body analysis including:
    - Body type classification (H, X, O, A, V)
    - Proportions analysis
    - Styling recommendations
    - Silhouettes to choose
    - Styles to avoid
    """
    try:
        result = await body_analysis_service.analyze_body(
            height=request.height,
            bust=request.bust,
            waist=request.waist,
            hip=request.hip,
        )
        
        return BodyAnalysisResponse(
            body_type=result.get("body_type", "H"),
            body_type_cn=result.get("body_type_cn", "H型（直筒型）"),
            body_type_description=result.get("body_type_description", ""),
            proportions=result.get("proportions", ""),
            strengths=result.get("strengths", ""),
            areas_to_enhance=result.get("areas_to_enhance", ""),
            recommended_silhouettes=result.get("recommended_silhouettes", []),
            styles_to_avoid=result.get("styles_to_avoid", ""),
            accessories=result.get("accessories", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Body analysis failed: {str(e)}")

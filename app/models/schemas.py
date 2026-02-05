"""
AI Beauty Muse - Pydantic Schemas for API Request/Response
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ============== Enums ==============

class HairLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class HairCurl(str, Enum):
    STRAIGHT = "straight"
    WAVY = "wavy"
    CURLY = "curly"


class HairBangs(str, Enum):
    NONE = "none"
    FULL = "full"
    SIDE = "side"
    CURTAIN = "curtain"


class FaceShape(str, Enum):
    OVAL = "oval"
    ROUND = "round"
    SQUARE = "square"
    HEART = "heart"
    OBLONG = "oblong"
    DIAMOND = "diamond"


class SeasonType(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class BodyType(str, Enum):
    H_TYPE = "H"
    X_TYPE = "X"
    O_TYPE = "O"
    A_TYPE = "A"
    V_TYPE = "V"


class FiveElement(str, Enum):
    WOOD = "wood"
    FIRE = "fire"
    EARTH = "earth"
    METAL = "metal"
    WATER = "water"


# ============== Color Models ==============

class ColorInfo(BaseModel):
    """Color information with name and hex value."""
    name: str = Field(..., description="Color name in Chinese")
    hex: str = Field(..., description="Hex color code")
    element: Optional[FiveElement] = Field(None, description="Associated five element")


# ============== Face Analysis ==============

class FaceAnalysisRequest(BaseModel):
    """Request for face analysis."""
    image_url: str = Field(..., description="URL of the face image")


class FaceAnalysisResponse(BaseModel):
    """Response for face analysis."""
    face_shape: FaceShape = Field(..., description="Detected face shape")
    face_shape_cn: str = Field(..., description="Face shape in Chinese")
    forehead: str = Field(..., description="Forehead analysis")
    cheekbones: str = Field(..., description="Cheekbones analysis")
    jawline: str = Field(..., description="Jawline analysis")
    chin: str = Field(..., description="Chin analysis")
    overall_analysis: str = Field(..., description="Overall face analysis")
    hairstyle_recommendations: List[str] = Field(..., description="Recommended hairstyles")
    makeup_tips: List[str] = Field(..., description="Makeup tips based on face shape")
    face_reading: Optional[str] = Field(None, description="Face reading interpretation")


# ============== Color Diagnosis ==============

class ColorDiagnosisRequest(BaseModel):
    """Request for color diagnosis."""
    image_url: str = Field(..., description="URL of the face/skin image")


class ColorDiagnosisResponse(BaseModel):
    """Response for color diagnosis."""
    season_type: SeasonType = Field(..., description="Personal color season type")
    season_type_cn: str = Field(..., description="Season type in Chinese")
    skin_undertone: str = Field(..., description="Skin undertone (warm/cool/neutral)")
    skin_undertone_cn: str = Field(..., description="Skin undertone in Chinese")
    best_colors: List[ColorInfo] = Field(..., description="Best colors for the person")
    avoid_colors: List[ColorInfo] = Field(..., description="Colors to avoid")
    neutral_colors: List[ColorInfo] = Field(..., description="Safe neutral colors")
    makeup_colors: Dict[str, List[ColorInfo]] = Field(..., description="Recommended makeup colors")
    hair_colors: List[ColorInfo] = Field(..., description="Recommended hair colors")
    analysis: str = Field(..., description="Detailed color analysis")


# ============== Body Analysis ==============

class BodyAnalysisRequest(BaseModel):
    """Request for body analysis."""
    height: int = Field(..., ge=100, le=250, description="Height in cm")
    bust: int = Field(..., ge=50, le=150, description="Bust measurement in cm")
    waist: int = Field(..., ge=40, le=150, description="Waist measurement in cm")
    hip: int = Field(..., ge=50, le=150, description="Hip measurement in cm")


class BodyAnalysisResponse(BaseModel):
    """Response for body analysis."""
    body_type: BodyType = Field(..., description="Body type classification")
    body_type_cn: str = Field(..., description="Body type in Chinese")
    body_type_description: str = Field(..., description="Description of body type")
    proportions: str = Field(..., description="Body proportions analysis")
    strengths: str = Field(..., description="Body strengths to highlight")
    areas_to_enhance: str = Field(..., description="Areas to enhance with styling")
    recommended_silhouettes: List[str] = Field(..., description="Recommended clothing silhouettes")
    styles_to_avoid: str = Field(..., description="Styles to avoid")
    accessories: str = Field(..., description="Accessory recommendations")


# ============== Hairstyle Generation ==============

class HairstyleGenerationRequest(BaseModel):
    """Request for AI hairstyle generation."""
    image_url: str = Field(..., description="URL of the face image")
    length: HairLength = Field(..., description="Desired hair length")
    curl: HairCurl = Field(..., description="Desired curl type")
    bangs: HairBangs = Field(..., description="Desired bangs style")
    additional_notes: Optional[str] = Field(None, description="Additional styling notes")


class HairstyleGenerationResponse(BaseModel):
    """Response for hairstyle generation."""
    generated_image_url: str = Field(..., description="URL of generated hairstyle image")
    hairstyle_name: str = Field(..., description="Name of the hairstyle")
    hairstyle_description: str = Field(..., description="Description of the hairstyle")
    styling_tips: List[str] = Field(..., description="Tips for achieving this style")
    maintenance_tips: List[str] = Field(..., description="Maintenance tips")
    suitable_face_shapes: List[str] = Field(..., description="Face shapes this style suits")


# ============== Hair Color ==============

class HairColorRequest(BaseModel):
    """Request for hair color experimentation."""
    image_url: str = Field(..., description="URL of the face image")
    color_name: str = Field(..., description="Desired hair color name")
    color_hex: Optional[str] = Field(None, description="Specific hex color code")


class HairColorResponse(BaseModel):
    """Response for hair color experimentation."""
    generated_image_url: str = Field(..., description="URL of generated image with new hair color")
    color_name: str = Field(..., description="Applied color name")
    color_analysis: str = Field(..., description="Analysis of how the color suits the person")
    complementary_makeup: List[str] = Field(..., description="Complementary makeup suggestions")
    maintenance_tips: List[str] = Field(..., description="Color maintenance tips")


# ============== Stylist Card ==============

class StylistCardRequest(BaseModel):
    """Request for generating stylist communication card."""
    original_image_url: str = Field(..., description="Original photo URL")
    target_image_url: str = Field(..., description="Target hairstyle image URL")
    hairstyle_description: str = Field(..., description="Description of desired hairstyle")
    additional_notes: Optional[str] = Field(None, description="Additional notes for stylist")


class StylistCardResponse(BaseModel):
    """Response for stylist card generation."""
    card_image_url: str = Field(..., description="URL of generated stylist card")
    summary: str = Field(..., description="Summary for the stylist")
    key_points: List[str] = Field(..., description="Key points to communicate")
    technical_terms: List[str] = Field(..., description="Technical terms to use")


# ============== Destiny Analysis (命理) ==============

class DestinyAnalysisRequest(BaseModel):
    """Request for destiny/BaZi analysis."""
    birth_year: int = Field(..., ge=1900, le=2100, description="Birth year")
    birth_month: int = Field(..., ge=1, le=12, description="Birth month")
    birth_day: int = Field(..., ge=1, le=31, description="Birth day")
    birth_hour: Optional[int] = Field(None, ge=0, le=23, description="Birth hour (0-23)")


class BaziPillar(BaseModel):
    """A single pillar in BaZi chart."""
    heavenly: str = Field(..., description="Heavenly stem")
    earthly: str = Field(..., description="Earthly branch")


class DestinyAnalysisResponse(BaseModel):
    """Response for destiny analysis."""
    bazi_chart: List[BaziPillar] = Field(..., description="Four pillars of destiny")
    day_master: str = Field(..., description="Day master analysis")
    five_elements: Dict[str, int] = Field(..., description="Five elements distribution")
    favorable_element: str = Field(..., description="Favorable element (喜用神)")
    enhance_colors: List[ColorInfo] = Field(..., description="Colors to enhance energy")
    balance_colors: List[ColorInfo] = Field(..., description="Colors for balance")
    avoid_colors: List[ColorInfo] = Field(..., description="Colors to avoid")
    hairstyle_suggestions: str = Field(..., description="Hairstyle suggestions based on destiny")
    overall_analysis: str = Field(..., description="Overall destiny analysis")


# ============== Daily Energy ==============

class DailyEnergyRequest(BaseModel):
    """Request for daily energy guidance."""
    occasion: Optional[str] = Field(None, description="Special occasion for the day")
    user_birth_year: Optional[int] = Field(None, description="User's birth year for personalization")
    user_birth_month: Optional[int] = Field(None, description="User's birth month")
    user_birth_day: Optional[int] = Field(None, description="User's birth day")


class DailyEnergyResponse(BaseModel):
    """Response for daily energy guidance."""
    date: str = Field(..., description="Current date")
    daily_stem_branch: str = Field(..., description="Daily heavenly stem and earthly branch")
    five_elements_energy: str = Field(..., description="Today's five elements energy")
    lucky_colors: List[ColorInfo] = Field(..., description="Today's lucky colors")
    outfit_suggestions: str = Field(..., description="Outfit suggestions for today")
    makeup_tips: str = Field(..., description="Makeup tips for today")
    energy_tips: str = Field(..., description="Energy tips for the day")
    occasion_special: Optional[str] = Field(None, description="Special advice for the occasion")


# ============== AI Chat ==============

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request for AI chat."""
    message: str = Field(..., description="User's message")
    image_url: Optional[str] = Field(None, description="Optional image URL for context")
    conversation_history: Optional[List[ChatMessage]] = Field(None, description="Previous conversation")


class ChatResponse(BaseModel):
    """Response for AI chat."""
    reply: str = Field(..., description="AI assistant's reply")
    suggestions: Optional[List[str]] = Field(None, description="Follow-up suggestions")


# ============== Health Check ==============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")

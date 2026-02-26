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
    """Request for face analysis (legacy JSON body mode)."""
    image_url: str = Field(..., description="URL of the face image")


class FiveFeatureAnalysis(BaseModel):
    """五官分析（眉、眼、鼻、口、耳）— 紧凑卡片式结构，每项含标签+评分+简析"""
    eyebrows_tag: str = Field(..., description="眉毛特征标签，如'柳叶弯眉'、'剑眉英气'")
    eyebrows_score: int = Field(75, ge=1, le=100, description="眉毛美学评分")
    eyebrows: str = Field(..., description="眉毛分析：形状、浓淡、走势、与眼睛搭配度，40字以内")
    eyes_tag: str = Field(..., description="眼睛特征标签，如'桃花杏眼'、'丹凤美目'")
    eyes_score: int = Field(75, ge=1, le=100, description="眼睛美学评分")
    eyes: str = Field(..., description="眼睛分析：大小、形状、眼距、眼神特质，40字以内")
    nose_tag: str = Field(..., description="鼻子特征标签，如'挺鼻悬胆'、'秀气琼鼻'")
    nose_score: int = Field(75, ge=1, le=100, description="鼻子美学评分")
    nose: str = Field(..., description="鼻子分析：鼻梁高低、鼻翼宽窄、鼻头形状，40字以内")
    mouth_tag: str = Field(..., description="嘴巴特征标签，如'樱桃小口'、'丰润红唇'")
    mouth_score: int = Field(75, ge=1, le=100, description="嘴巴美学评分")
    mouth: str = Field(..., description="嘴巴分析：大小、唇形、唇厚薄比例，40字以内")
    ears_tag: str = Field(..., description="耳朵特征标签，如'福耳丰厚'、'贴面秀耳'")
    ears_score: int = Field(75, ge=1, le=100, description="耳朵美学评分")
    ears: str = Field(..., description="耳朵分析：大小、位置、耳垂（不可见则注明），40字以内")


class FaceProportions(BaseModel):
    """面部比例分析（三庭五眼等）— 含比例数值和标准度评分"""
    three_sections_ratio: str = Field("1:1:1", description="三庭实际比例，如'1:1.1:0.9'")
    three_sections_score: int = Field(75, ge=1, le=100, description="三庭标准度评分（100=完美1:1:1）")
    three_sections: str = Field(..., description="三庭分析，30字以内")
    five_eyes_score: int = Field(75, ge=1, le=100, description="五眼标准度评分")
    five_eyes: str = Field(..., description="五眼分析，30字以内")
    symmetry_score: int = Field(75, ge=1, le=100, description="对称性评分")
    symmetry: str = Field(..., description="对称性分析，30字以内")


class FaceReadingDetail(BaseModel):
    """面相解读 — 含评分(1-100)和今日能量影响分析"""
    career: str = Field(..., description="事业运解读，结合额头天庭和眉眼气质，100字左右")
    career_score: int = Field(70, ge=1, le=100, description="事业运评分")
    career_today: str = Field("", description="今日能量对事业运的影响，30字以内")
    wealth: str = Field(..., description="财运解读，结合鼻相财帛宫和耳相，100字左右")
    wealth_score: int = Field(70, ge=1, le=100, description="财运评分")
    wealth_today: str = Field("", description="今日能量对财运的影响，30字以内")
    relationships: str = Field(..., description="感情运解读，结合眼相桃花宫和唇相，100字左右")
    relationships_score: int = Field(70, ge=1, le=100, description="感情运评分")
    relationships_today: str = Field("", description="今日能量对感情运的影响，30字以内")
    health: str = Field(..., description="健康运解读，结合面色气色和五官气血表现，80字左右")
    health_score: int = Field(70, ge=1, le=100, description="健康运评分")
    health_today: str = Field("", description="今日能量对健康的影响，30字以内")
    personality: str = Field(..., description="性格特征解读，综合五官分析核心性格，100字左右")
    personality_tag: str = Field("", description="性格标签，如'外柔内刚型'、'温婉知性型'")
    overall: str = Field(..., description="综合面相总评，含积极建议，120字左右")
    overall_score: int = Field(70, ge=1, le=100, description="综合面相评分")


class FaceAnalysisResponse(BaseModel):
    """Response for face analysis — comprehensive face reading."""
    # 用户上传的原始照片 URL（用于列表缩略图等）
    input_image_url: Optional[str] = Field(None, description="Relative URL of uploaded face photo, e.g. /uploads/face/xxx.jpg")
    # 臉型
    face_shape: FaceShape = Field(..., description="Detected face shape")
    face_shape_cn: str = Field(..., description="Face shape in Chinese")
    # 骨相分析
    forehead: str = Field(..., description="Forehead analysis (额头)")
    cheekbones: str = Field(..., description="Cheekbones analysis (颧骨)")
    jawline: str = Field(..., description="Jawline analysis (下颌线)")
    chin: str = Field(..., description="Chin analysis (下巴)")
    # 五官分析
    five_features: FiveFeatureAnalysis = Field(..., description="五官分析")
    # 面部比例
    face_proportions: FaceProportions = Field(..., description="面部比例分析")
    # 整体分析
    overall_analysis: str = Field(..., description="Overall face analysis (200字)")
    # 面相解读
    face_reading: FaceReadingDetail = Field(..., description="面相解读详情")
    # 建议
    hairstyle_recommendations: List[str] = Field(..., description="Recommended hairstyles")
    makeup_tips: List[str] = Field(..., description="Makeup tips based on face shape")
    # 运势美学建议（结合当日能量的化妆和配饰推荐）
    fortune_beauty: Optional["FortuneBeautySection"] = Field(
        None, description="今日运势美学建议（结合当日五行能量的化妆和配饰推荐，含参考图）"
    )


# ============== Fortune Beauty Section (运势美学) ==============

class MakeupLookDetail(BaseModel):
    """结合运势的化妆建议详情"""
    look_name: str = Field(..., description="妆容名称，如'木系清透妆'、'火系魅力妆'")
    concept: str = Field(..., description="妆容理念，与今日能量的关联说明，50字左右")
    base_makeup: str = Field(..., description="底妆建议（质地、色号方向、妆效）")
    eye_shadow: str = Field(..., description="眼影建议（颜色搭配、画法要点）")
    eye_shadow_hex: List[str] = Field(..., description="眼影推荐色号列表（hex）")
    eyeliner: str = Field(..., description="眼线建议（粗细、形状、颜色）")
    lip_color: str = Field(..., description="唇色建议（质地、色调）")
    lip_color_hex: str = Field(..., description="唇色色号（hex）")
    blush: str = Field(..., description="腮红建议（位置、颜色、手法）")
    blush_hex: str = Field(..., description="腮红色号（hex）")
    highlight_contour: str = Field(..., description="高光与修容建议")


class AccessoryRecommendation(BaseModel):
    """配饰建议"""
    category: str = Field(..., description="配饰类别: earrings/necklace/bracelet/ring/hair_accessory/glasses/scarf/bag")
    category_cn: str = Field(..., description="类别中文名")
    name: str = Field(..., description="推荐款式名称")
    description: str = Field(..., description="款式描述和搭配说明，30字左右")
    material: str = Field(..., description="推荐材质")
    color: str = Field(..., description="推荐颜色名称")
    color_hex: str = Field(..., description="推荐颜色色号（hex）")
    energy_note: str = Field(..., description="与五行/运势的能量关联说明，20字左右")


class FortuneBeautySection(BaseModel):
    """今日运势美学建议（面部分析增值板块）"""
    date: str = Field(..., description="今日日期")
    daily_stem_branch: str = Field(..., description="今日天干地支")
    daily_element: str = Field(..., description="今日五行主气")
    lucky_colors: List[ColorInfo] = Field(..., description="今日幸运色")
    fortune_beauty_summary: str = Field(..., description="今日美学运势总评，结合脸型和当日能量，100字左右")
    makeup_looks: List[MakeupLookDetail] = Field(..., description="2个推荐妆容方案")
    accessories: List[AccessoryRecommendation] = Field(..., description="4-5个配饰建议（耳饰、项链、发饰、眼镜等）")
    look_image_url: Optional[str] = Field(None, description="AI 生成的妆容参考图 URL（可能为 null）")


# Update forward reference
FaceAnalysisResponse.model_rebuild()


# ============== Face Style Analysis (Upload) ==============

class HairStyleRecommendation(BaseModel):
    """A single hairstyle recommendation with details."""
    name: str = Field(..., description="Hairstyle name")
    description: str = Field(..., description="Why this style suits the face shape")
    length: str = Field(..., description="Hair length (short/medium/long)")
    styling_tips: str = Field(..., description="How to achieve this style")


class HairColorRecommendation(BaseModel):
    """A single hair color recommendation."""
    color_name: str = Field(..., description="Hair color name in Chinese")
    color_hex: str = Field(..., description="Approximate hex color code")
    reason: str = Field(..., description="Why this color suits the person")


class FaceStyleResponse(BaseModel):
    """Combined response: face analysis + hairstyle + hair color recommendations."""
    # 用户上传的分析用照片 URL（用于「我的报告」列表缩略图）
    input_image_url: Optional[str] = Field(None, description="Relative URL of uploaded face photo, e.g. /uploads/face/xxx.jpg")
    # Face analysis
    face_shape: FaceShape = Field(..., description="Detected face shape")
    face_shape_cn: str = Field(..., description="Face shape in Chinese")
    face_analysis: str = Field(..., description="Detailed face shape analysis")
    # Skin tone (for hair color matching)
    skin_tone: str = Field(..., description="Skin tone description")
    # Hairstyle recommendations
    hairstyle_recommendations: List[HairStyleRecommendation] = Field(
        ..., description="Top 3 recommended hairstyles"
    )
    # Hair color recommendations
    hair_color_recommendations: List[HairColorRecommendation] = Field(
        ..., description="Top 3 recommended hair colors"
    )
    # Overall advice
    overall_advice: str = Field(..., description="Overall styling advice combining face shape and skin tone")


# ============== Face Edit (Upload + Instructions → Modified Photo) ==============

class ImageEditResponse(BaseModel):
    """Response for photo modification: returns the saved image path and change summary."""
    image_url: str = Field(..., description="Relative URL to download the edited image, e.g. /uploads/edited/xxx.png")
    image_path: str = Field(..., description="Server-side file path where the edited image is stored")
    modification_applied: str = Field(..., description="Echo of the hair modification instructions")
    provider: str = Field(..., description="Image edit provider used: 'gpt-image-1' or 'flux-kontext'")


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


# ============== Stylist Card (理髮師溝通卡) ==============

class StylistCardRequest(BaseModel):
    """Request for generating a professional stylist communication card.

    All fields should come from the prior face-style analysis / face-edit results
    so that the cutting guide remains **consistent** with the AI-generated effect photo.
    """
    hairstyle_name: str = Field(..., description="選定的髮型名稱")
    hairstyle_description: str = Field(..., description="髮型描述（為何適合該臉型）")
    hairstyle_length: str = Field(..., description="髮型長度: short / medium / long")
    styling_tips: str = Field(..., description="造型技巧原文（來自 face-style 分析）")
    color_name: str = Field(..., description="選定的髮色中文名稱")
    color_hex: str = Field(..., description="近似十六進制色值，如 #A0522D")
    face_shape: str = Field(..., description="臉型英文標識 (oval/round/square/heart/oblong/diamond)")
    face_shape_cn: str = Field(..., description="臉型中文名稱")
    face_analysis: Optional[str] = Field(None, description="臉型詳細分析")
    skin_tone: Optional[str] = Field(None, description="膚色描述")
    effect_image_url: str = Field(..., description="AI 生成效果圖的相對 URL")


class CuttingGuide(BaseModel):
    """修剪注意事項"""
    outline: str = Field(..., description="輪廓線定義，基於骨相分析的外輪廓設計說明")
    technique: str = Field(..., description="修剪技法（含專業術語如滑剪、點剪、紋理剪等）")
    weight_balance: str = Field(..., description="視覺重心位置，決定臉型修飾效果")
    key_points: List[str] = Field(..., description="關鍵修剪要點列表")


class ColorFormula(BaseModel):
    """專業染髮色彩公式"""
    formula_code: str = Field(..., description="國際標準染髮色號，如 6/34")
    formula_name: str = Field(..., description="色彩公式完整名稱（含色調和級別）")
    brand_reference: str = Field(..., description="主品牌參考，如 Wella Koleston Perfect 6/34")
    brand_alt: str = Field(..., description="替代品牌參考，如 L'Oréal Majirel 6/34")
    bleach_required: bool = Field(..., description="是否需要先脫色")
    bleach_level: int = Field(..., ge=0, description="脫色次數（0 表示不需要）")
    processing_time: str = Field(..., description="染色停留時間")
    energy_note: str = Field(..., description="色彩能量搭配建議（結合膚色分析）")


class StylingGuide(BaseModel):
    """造型與維護指南"""
    daily_routine: str = Field(..., description="日常打理方法")
    products: List[str] = Field(..., description="推薦護理/造型產品")
    tools: List[str] = Field(..., description="推薦造型工具（含規格如卷髮棒直徑）")
    maintenance_cycle: str = Field(..., description="補染/維護週期建議")


class DetailNote(BaseModel):
    """局部細節注意事項"""
    area: str = Field(..., description="局部區域（如劉海、髮尾、鬢角、層次）")
    note: str = Field(..., description="該區域的注意事項和美學要求")


class StylistCardResponse(BaseModel):
    """Complete stylist communication card response."""
    card_image_url: Optional[str] = Field(None, description="合成的溝通卡長圖 URL（後端未合成時為 null）")
    cutting_guide: CuttingGuide = Field(..., description="修剪注意事項")
    color_formula: ColorFormula = Field(..., description="專業染髮色彩公式")
    styling_guide: StylingGuide = Field(..., description="造型與維護指南")
    detail_notes: List[DetailNote] = Field(..., description="局部細節注意事項")


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


# ============== Fortune Analysis (命理 + 今日运势 by Gemini 3 Pro) ==============

class FortuneRequest(BaseModel):
    """Request for fortune analysis (destiny + today's horoscope)."""
    birth_year: int = Field(..., ge=1900, le=2100, description="Birth year")
    birth_month: int = Field(..., ge=1, le=12, description="Birth month")
    birth_day: int = Field(..., ge=1, le=31, description="Birth day")
    birth_hour: Optional[int] = Field(None, ge=0, le=23, description="Birth hour (0-23), optional")
    occasion: Optional[str] = Field(None, description="Today's occasion, e.g. '面試','約會','重要會議'")


class FortuneResponse(BaseModel):
    """Comprehensive fortune response combining destiny analysis and today's horoscope."""
    # ---- BaZi basics ----
    date: str = Field(..., description="Today's date")
    bazi_chart: List[BaziPillar] = Field(..., description="Four pillars of destiny (年柱/月柱/日柱/時柱)")
    day_master: str = Field(..., description="Day master summary, e.g. '甲木（旺）'")
    five_elements: Dict[str, int] = Field(..., description="Five elements distribution, e.g. {'木':2,'火':1,...}")
    favorable_element: str = Field(..., description="Favorable element (喜用神)")
    # ---- Destiny analysis (命理) ----
    personality: str = Field(..., description="Personality traits based on BaZi")
    destiny_overview: str = Field(..., description="Overall destiny analysis")
    # ---- Today's fortune (今日运势) ----
    daily_stem_branch: str = Field(..., description="Today's stem-branch, e.g. '丙午'")
    daily_element: str = Field(..., description="Today's dominant element, e.g. '火'")
    fortune_summary: str = Field(..., description="Today's fortune summary for this person")
    fortune_score: int = Field(..., ge=1, le=100, description="Today's fortune score (1-100)")
    fortune_areas: Dict[str, str] = Field(
        ..., description="Fortune by area: e.g. {'事業':'...','感情':'...','財運':'...','健康':'...'}"
    )
    # ---- Actionable tips ----
    lucky_colors: List[ColorInfo] = Field(..., description="Today's lucky colors")
    outfit_suggestions: str = Field(..., description="Outfit suggestions for today")
    energy_tips: str = Field(..., description="Energy and mindset tips")
    occasion_special: Optional[str] = Field(None, description="Special tips for the occasion, if provided")


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


# ============== Authentication ==============

class DeviceRegisterRequest(BaseModel):
    """Register (or login) via device identifier (legacy)."""
    device_id: str = Field(..., min_length=1, max_length=128, description="Unique device identifier")
    nickname: Optional[str] = Field(None, max_length=64, description="Optional display name")


class SmsSendRequest(BaseModel):
    """Request to send SMS verification code."""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号码（中国大陆 11 位）")


class SmsSendResponse(BaseModel):
    """Response after sending SMS code."""
    success: bool = Field(..., description="是否发送成功")
    message: str = Field(..., description="提示信息")
    expires_in: int = Field(..., description="验证码有效期（秒）")


class SmsLoginRequest(BaseModel):
    """Login or register via SMS verification code."""
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号码")
    code: str = Field(..., min_length=4, max_length=8, description="短信验证码")
    nickname: Optional[str] = Field(None, max_length=64, description="昵称（首次注册时可选）")


class TokenResponse(BaseModel):
    """JWT token response returned after login / register / refresh."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: str = Field(..., description="User ID")
    phone: Optional[str] = Field(None, description="手机号（脱敏）")
    nickname: Optional[str] = Field(None, description="User nickname")
    is_member: bool = Field(default=False, description="是否为会员")


class TokenRefreshRequest(BaseModel):
    """Refresh an existing token (client sends current token in header, body can be empty)."""
    pass


class OAuthMobileUserInfo(BaseModel):
    """OAuth 登录后返回的简要用户信息（与 APP 约定一致）。"""
    user_id: str = Field(..., description="用户 ID")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像 URL")
    is_member: bool = Field(default=False, description="是否为会员")


class OAuthMobileResponse(BaseModel):
    """GET /api/oauth/mobile 响应：APP 将 app_session_id 存为 Bearer token。"""
    app_session_id: str = Field(..., description="会话 token，后续请求 Header: Authorization: Bearer <此值>")
    user: OAuthMobileUserInfo = Field(..., description="当前用户简要信息")


class UserProfileResponse(BaseModel):
    """User profile with membership and quota info."""
    user_id: str = Field(..., description="用户 ID")
    phone: Optional[str] = Field(None, description="手机号（脱敏）")
    nickname: Optional[str] = Field(None, description="昵称")
    is_member: bool = Field(default=False, description="是否为会员")
    member_expires_at: Optional[str] = Field(None, description="会员到期时间（ISO 格式）")
    quotas: Dict[str, Any] = Field(
        ..., description="各功能剩余次数, e.g. {'face_style': {'used': 1, 'limit': 3, 'remaining': 2}, ...}"
    )
    created_at: str = Field(..., description="注册时间")


# ============== Membership (会员) ==============

class MembershipSubscribeRequest(BaseModel):
    """Request to subscribe to membership."""
    plan: str = Field(default="monthly", description="套餐类型: monthly")
    payment_order_id: Optional[str] = Field(None, description="支付平台订单号（支付完成后传入）")


class MembershipSubscribeResponse(BaseModel):
    """Response after subscribing."""
    success: bool = Field(..., description="是否订阅成功")
    message: str = Field(..., description="提示信息")
    plan: str = Field(..., description="套餐名称")
    price: float = Field(..., description="价格（元）")
    started_at: str = Field(..., description="生效时间")
    expires_at: str = Field(..., description="到期时间")


class MembershipStatusResponse(BaseModel):
    """Current membership status."""
    is_member: bool = Field(..., description="是否为有效会员")
    plan: Optional[str] = Field(None, description="当前套餐")
    price: Optional[float] = Field(None, description="套餐价格")
    started_at: Optional[str] = Field(None, description="开始时间")
    expires_at: Optional[str] = Field(None, description="到期时间")
    days_remaining: int = Field(default=0, description="剩余天数")


# ============== Quota (使用次数) ==============

class QuotaStatusResponse(BaseModel):
    """Usage quota status for all features."""
    year_month: str = Field(..., description="当前月份, e.g. '2026-02'")
    is_member: bool = Field(..., description="是否为会员")
    features: Dict[str, Any] = Field(
        ..., description="各功能使用情况, e.g. {'face_style': {'used': 1, 'limit': 3, 'remaining': 2}}"
    )


# ============== Report History (历史报告) ==============

class ReportHistoryItem(BaseModel):
    """Single item in the report history list (lightweight for list views)."""
    id: str = Field(..., description="报告 UUID")
    report_type: str = Field(..., description="报告类型: face_analysis / face_style / face_edit / destiny_fortune / daily_energy / stylist_card")
    title: str = Field(..., description="报告标题")
    summary: Optional[str] = Field(None, description="摘要（列表展示用）")
    thumbnail_url: Optional[str] = Field(None, description="缩略图 URL")
    created_at: str = Field(..., description="创建时间 (ISO 格式)")


class ReportHistoryListResponse(BaseModel):
    """Paginated list of report history."""
    reports: List[ReportHistoryItem] = Field(..., description="报告列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")


class ReportHistoryDetailResponse(BaseModel):
    """Full detail of a single report (includes the complete JSON data)."""
    id: str = Field(..., description="报告 UUID")
    report_type: str = Field(..., description="报告类型")
    title: str = Field(..., description="报告标题")
    summary: Optional[str] = Field(None, description="摘要")
    thumbnail_url: Optional[str] = Field(None, description="缩略图 URL")
    data: Dict[str, Any] = Field(..., description="完整的报告数据（与原接口响应体一致）")
    created_at: str = Field(..., description="创建时间 (ISO 格式)")


# ----- 报告落地（APP 聚合后创建）的 data 结构建模 -----


class FaceStyleLandingHairstyle(BaseModel):
    """落地数据：单条发型推荐."""
    name: str = Field("", description="发型名称")
    length: Optional[str] = Field(None, description="长度描述，如 中长")
    description: Optional[str] = Field(None, description="发型描述")
    styling_tips: Optional[str] = Field(None, description="造型建议")


class FaceStyleLandingHairColor(BaseModel):
    """落地数据：单条发色推荐."""
    color_name: str = Field("", description="发色名称")
    color_hex: Optional[str] = Field(None, description="色值 #RRGGBB")
    reason: Optional[str] = Field(None, description="推荐理由")


class FaceStyleLandingEditResult(BaseModel):
    """落地数据：单次 face-edit 生成结果（与 ImageEditResponse 一致）."""
    image_url: str = Field(..., description="生成图相对 URL")
    image_path: Optional[str] = Field(None, description="服务端路径")
    modification_applied: Optional[str] = Field(None, description="修改说明")
    provider: Optional[str] = Field(None, description="编辑引擎")


class FaceStyleLandingCombination(BaseModel):
    """落地数据：一套发型+发色+效果图."""
    id: int = Field(0, description="组合序号，0/1/2 等")
    hairstyle: Optional[FaceStyleLandingHairstyle] = Field(None, description="发型信息")
    hair_color: Optional[FaceStyleLandingHairColor] = Field(None, description="发色信息")
    edit_result: Optional[FaceStyleLandingEditResult] = Field(None, description="本套效果图")


class FaceStyleLandingFaceInfo(BaseModel):
    """落地数据：face-style 分析摘要（来自 POST /analysis/face-style）."""
    face_shape: Optional[str] = Field(None, description="脸型英文")
    face_shape_cn: Optional[str] = Field(None, description="脸型中文")
    face_analysis: Optional[str] = Field(None, description="脸部分析")
    skin_tone: Optional[str] = Field(None, description="肤色")
    overall_advice: Optional[str] = Field(None, description="整体建议")


class FaceStyleReportData(BaseModel):
    """report_type=face_style 时，POST /history/reports 的 data 字段结构（报告落地的建模）."""
    face_style: Optional[FaceStyleLandingFaceInfo] = Field(None, description="面部分析摘要")
    combinations: List[FaceStyleLandingCombination] = Field(default_factory=list, description="多套发型+发色+效果图")
    stylist_card: Optional[Dict[str, Any]] = Field(None, description="理发师沟通卡内容（可选）")


class ReportHistoryCreateRequest(BaseModel):
    """Request to create a report from the APP side (no backend AI call needed)."""
    report_type: str = Field(..., description="报告类型")
    title: str = Field(..., max_length=200, description="报告标题")
    summary: Optional[str] = Field(None, max_length=500, description="摘要")
    thumbnail_url: Optional[str] = Field(None, description="缩略图 URL")
    data: Dict[str, Any] = Field(..., description="完整的报告数据（见各 report_type 的落地建模）")


class ReportHistoryCreateResponse(BaseModel):
    """Response after creating a report."""
    id: str = Field(..., description="新报告 UUID")
    success: bool = Field(default=True, description="是否创建成功")


# ============== Landing Suggestion（报告落地建议）==============

class LandingSuggestionRequest(BaseModel):
    """请求生成「全面精简落地建议」：可传入多模块数据，至少一项。"""
    face_analysis: Optional[Dict[str, Any]] = Field(None, description="脸部分析结果（与 FaceAnalysisResponse 或报告详情 data 一致）")
    color_diagnosis: Optional[Dict[str, Any]] = Field(None, description="色彩诊断结果（与 ColorDiagnosisResponse 一致）")
    body_analysis: Optional[Dict[str, Any]] = Field(None, description="身材风格解析结果（与 BodyAnalysisResponse 一致）")
    destiny_fortune: Optional[Dict[str, Any]] = Field(None, description="命理色谱/今日运势结果（与 FortuneResponse 一致）")
    daily_energy: Optional[Dict[str, Any]] = Field(None, description="当日能量/穿搭建议（与 DailyEnergyResponse 一致）")


class LandingSuggestionSection(BaseModel):
    """落地建议中的一个板块（标题 + 精简内容）。"""
    title: str = Field(..., description="板块标题，如「今日穿搭要点」")
    content: str = Field(..., description="该板块的精简落地建议，2–4 句话")


class LandingSuggestionResponse(BaseModel):
    """结合多模块生成的全面精简落地建议。"""
    summary: str = Field(..., description="一段总述，综合所有输入给出 2–4 句核心建议")
    sections: List[LandingSuggestionSection] = Field(default_factory=list, description="分板块的精简建议，通常 3–5 条")
    report_id: Optional[str] = Field(None, description="若已写入历史报告，返回报告 UUID")


# ============== Chat Session ==============

class ChatSessionCreate(BaseModel):
    """Create a new chat session."""
    title: Optional[str] = Field(None, max_length=200, description="Optional session title")


class ChatSessionInfo(BaseModel):
    """Summary of a chat session (used in list responses)."""
    id: str = Field(..., description="Session UUID")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last activity time")
    message_count: int = Field(default=0, description="Total messages in this session")


class ChatSessionListResponse(BaseModel):
    """Paginated list of sessions."""
    sessions: List[ChatSessionInfo] = Field(..., description="List of chat sessions")
    total: int = Field(..., description="Total session count")


# ============== AI Chat ==============

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    image_url: Optional[str] = Field(None, description="Attached image URL (user messages only)")
    created_at: Optional[datetime] = Field(None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Request for AI chat (session-based)."""
    session_id: str = Field(..., description="Chat session ID")
    message: str = Field(..., description="User's message")
    image_url: Optional[str] = Field(None, description="Optional image URL for context")


class ChatResponse(BaseModel):
    """Response for AI chat."""
    session_id: str = Field(..., description="Chat session ID")
    reply: str = Field(..., description="AI assistant's reply")
    suggestions: Optional[List[str]] = Field(None, description="Follow-up suggestions")


class ChatHistoryResponse(BaseModel):
    """Full message history of a session."""
    session_id: str = Field(..., description="Chat session ID")
    title: Optional[str] = Field(None, description="Session title")
    messages: List[ChatMessage] = Field(..., description="Ordered messages")


# ============== Health Check ==============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")

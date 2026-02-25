"""
AI Beauty Muse - Analysis API Routes
Handles face analysis, color diagnosis, body analysis, and photo editing endpoints.
"""
import asyncio
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_optional_user, require_quota
from app.models.database import get_db, User
from app.services.history_service import history_service
from app.models.schemas import (
    FaceAnalysisResponse,
    FiveFeatureAnalysis,
    FaceProportions,
    FaceReadingDetail,
    FaceStyleResponse,
    HairStyleRecommendation,
    HairColorRecommendation,
    ColorDiagnosisResponse,
    BodyAnalysisRequest,
    BodyAnalysisResponse,
    ColorInfo,
    ImageEditResponse,
    FortuneBeautySection,
    MakeupLookDetail,
    AccessoryRecommendation,
    LandingSuggestionRequest,
    LandingSuggestionResponse,
    LandingSuggestionSection,
)
from app.services.face_analysis_service import face_analysis_service, file_to_data_uri
from app.services.color_diagnosis_service import color_diagnosis_service
from app.services.body_analysis_service import body_analysis_service
from app.services.openai_service import openai_service
from app.services.landing_suggestion_service import landing_suggestion_service


router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/face", response_model=FaceAnalysisResponse)
async def analyze_face(
    image: UploadFile = File(..., description="Face photo (JPEG/PNG/WebP, max 10 MB)"),
    birth_year: Optional[int] = Form(None, description="出生年（可选，用于个性化运势建议）"),
    birth_month: Optional[int] = Form(None, description="出生月（可选）"),
    birth_day: Optional[int] = Form(None, description="出生日（可选）"),
    include_fortune: bool = Form(True, description="是否包含运势美学建议（默认 true）"),
    _quota: dict = Depends(require_quota("face_analysis")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a face photo → AI analyzes face shape and provides recommendations,
    **including today's fortune-based makeup and accessory suggestions with a reference image**.

    **Accepts** ``multipart/form-data`` with fields:

    | Field | Required | Description |
    |-------|----------|-------------|
    | ``image`` | ✅ | Face photo |
    | ``birth_year`` | ❌ | Birth year (for personalized lucky colors) |
    | ``birth_month`` | ❌ | Birth month |
    | ``birth_day`` | ❌ | Birth day |
    | ``include_fortune`` | ❌ | Include fortune beauty section (default ``true``) |

    **Returns**:
    - Face shape classification & analysis
    - Five-feature & proportion analysis
    - Face reading (面相解读)
    - Hairstyle & makeup tips
    - **Fortune beauty section** (运势美学):
      - Today's energy (干支, 五行, 幸运色)
      - 2 makeup look schemes (with hex color codes)
      - 4-5 accessory recommendations
      - AI-generated beauty reference image
    """
    # ---- Validate file type ----
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. "
                   f"Allowed: {', '.join(settings.allowed_image_types)}",
        )

    # ---- Read & validate size ----
    file_bytes = await image.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
                   f"Maximum allowed: {settings.max_upload_size_mb} MB.",
        )

    # ---- Save uploaded face image for thumbnail (list "我的报告" 显示分析用照片) ----
    input_image_url: Optional[str] = None
    try:
        ext = "png" if image.content_type == "image/png" else "webp" if image.content_type == "image/webp" else "jpg"
        filename = f"face-{uuid.uuid4().hex}.{ext}"
        save_dir = Path(settings.upload_dir) / "face"
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / filename).write_bytes(file_bytes)
        input_image_url = f"/uploads/face/{filename}"
    except Exception as save_err:
        print(f"⚠️ Face input image save skipped: {save_err}")

    # ---- Convert to data URI for Vision model ----
    data_uri = file_to_data_uri(file_bytes, image.content_type)

    # ---- Compute today's energy context ----
    daily_context = face_analysis_service.get_daily_energy_context()

    # ---- Call LLM for face analysis (with daily energy) ----
    try:
        result = await face_analysis_service.analyze_face(data_uri, daily_context)

        # Build nested models with safe defaults
        ff = result.get("five_features", {})
        five_features = FiveFeatureAnalysis(
            eyebrows_tag=ff.get("eyebrows_tag", "自然弯眉"),
            eyebrows_score=int(ff.get("eyebrows_score", 75)),
            eyebrows=ff.get("eyebrows", "眉形自然"),
            eyes_tag=ff.get("eyes_tag", "明亮杏眼"),
            eyes_score=int(ff.get("eyes_score", 75)),
            eyes=ff.get("eyes", "眼型适中"),
            nose_tag=ff.get("nose_tag", "端正秀鼻"),
            nose_score=int(ff.get("nose_score", 75)),
            nose=ff.get("nose", "鼻梁端正"),
            mouth_tag=ff.get("mouth_tag", "红润饱满"),
            mouth_score=int(ff.get("mouth_score", 75)),
            mouth=ff.get("mouth", "唇形饱满"),
            ears_tag=ff.get("ears_tag", "未展示"),
            ears_score=int(ff.get("ears_score", 70)),
            ears=ff.get("ears", "耳朵位置适中"),
        )

        fp = result.get("face_proportions", {})
        face_proportions = FaceProportions(
            three_sections_ratio=fp.get("three_sections_ratio", "1:1:1"),
            three_sections_score=int(fp.get("three_sections_score", 75)),
            three_sections=fp.get("three_sections", "三庭比例匀称"),
            five_eyes_score=int(fp.get("five_eyes_score", 75)),
            five_eyes=fp.get("five_eyes", "五眼比例适中"),
            symmetry_score=int(fp.get("symmetry_score", 78)),
            symmetry=fp.get("symmetry", "面部基本对称"),
        )

        reading_raw = result.get("face_reading", {})
        if isinstance(reading_raw, str):
            reading_raw = {"overall": reading_raw}
        face_reading = FaceReadingDetail(
            career=reading_raw.get("career", "事业运势平稳"),
            career_score=int(reading_raw.get("career_score", 70)),
            career_today=reading_raw.get("career_today", ""),
            wealth=reading_raw.get("wealth", "财运适中"),
            wealth_score=int(reading_raw.get("wealth_score", 70)),
            wealth_today=reading_raw.get("wealth_today", ""),
            relationships=reading_raw.get("relationships", "感情运势稳定"),
            relationships_score=int(reading_raw.get("relationships_score", 70)),
            relationships_today=reading_raw.get("relationships_today", ""),
            health=reading_raw.get("health", "健康状况良好"),
            health_score=int(reading_raw.get("health_score", 70)),
            health_today=reading_raw.get("health_today", ""),
            personality=reading_raw.get("personality", "性格温和稳重"),
            personality_tag=reading_raw.get("personality_tag", ""),
            overall=reading_raw.get("overall", "面相端正，五官协调"),
            overall_score=int(reading_raw.get("overall_score", 70)),
        )

        # ---- Fortune beauty section ----
        fortune_beauty_model = None
        if include_fortune:
            try:
                fb_data = await face_analysis_service.generate_fortune_beauty(
                    image_url=data_uri,
                    face_result=result,
                    birth_year=birth_year,
                    birth_month=birth_month,
                    birth_day=birth_day,
                )

                # ---- Generate beauty reference image (best-effort, parallel-safe) ----
                look_image_url = None
                try:
                    makeup_looks = fb_data.get("makeup_looks", [])
                    first_look_name = makeup_looks[0]["look_name"] if makeup_looks else "运势美妆"
                    lucky_desc = "、".join(
                        f"{c['name']}({c['hex']})" for c in fb_data.get("lucky_colors", [])
                    )
                    img_prompt = face_analysis_service._build_beauty_image_prompt(
                        face_shape_cn=result.get("face_shape_cn", "鹅蛋脸"),
                        daily_element_cn=fb_data.get("daily_element", "土"),
                        lucky_colors_desc=lucky_desc,
                        makeup_look_name=first_look_name,
                    )
                    img_bytes = await openai_service.generate_beauty_image(img_prompt)
                    if img_bytes:
                        filename = f"beauty-{uuid.uuid4().hex}.png"
                        save_dir = Path(settings.upload_dir) / "beauty"
                        save_dir.mkdir(parents=True, exist_ok=True)
                        (save_dir / filename).write_bytes(img_bytes)
                        look_image_url = f"/uploads/beauty/{filename}"
                except Exception as img_err:
                    print(f"⚠️ Beauty image generation skipped: {img_err}")

                fb_data["look_image_url"] = look_image_url

                # Build Pydantic models
                makeup_looks_models = []
                for m in fb_data.get("makeup_looks", []):
                    try:
                        makeup_looks_models.append(MakeupLookDetail(**m))
                    except Exception:
                        pass

                accessories_models = []
                for a in fb_data.get("accessories", []):
                    try:
                        accessories_models.append(AccessoryRecommendation(**a))
                    except Exception:
                        pass

                lucky_colors_models = []
                for c in fb_data.get("lucky_colors", []):
                    try:
                        lucky_colors_models.append(ColorInfo(
                            name=c.get("name", ""),
                            hex=c.get("hex", "#000000"),
                            element=c.get("element"),
                        ))
                    except Exception:
                        pass

                fortune_beauty_model = FortuneBeautySection(
                    date=fb_data.get("date", ""),
                    daily_stem_branch=fb_data.get("daily_stem_branch", ""),
                    daily_element=fb_data.get("daily_element", ""),
                    lucky_colors=lucky_colors_models,
                    fortune_beauty_summary=fb_data.get("fortune_beauty_summary", ""),
                    makeup_looks=makeup_looks_models,
                    accessories=accessories_models,
                    look_image_url=look_image_url,
                )
            except Exception as fb_err:
                print(f"⚠️ Fortune beauty generation failed: {fb_err}")
                # Non-fatal: response still returns without fortune_beauty

        response = FaceAnalysisResponse(
            input_image_url=input_image_url,
            face_shape=result.get("face_shape", "oval"),
            face_shape_cn=result.get("face_shape_cn", "鵝蛋臉"),
            forehead=result.get("forehead", ""),
            cheekbones=result.get("cheekbones", ""),
            jawline=result.get("jawline", ""),
            chin=result.get("chin", ""),
            five_features=five_features,
            face_proportions=face_proportions,
            overall_analysis=result.get("overall_analysis", ""),
            face_reading=face_reading,
            hairstyle_recommendations=result.get("hairstyle_recommendations", []),
            makeup_tips=result.get("makeup_tips", []),
            fortune_beauty=fortune_beauty_model,
        )

        # 面相分析报告由 APP 端在展示结果后统一调用 POST /history/reports 保存，此处不再自动保存，避免与 APP 端重复写入导致「我的报告」出现两条相同记录。

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face analysis failed: {str(e)}")


@router.post("/face-style", response_model=FaceStyleResponse)
async def analyze_face_style(
    image: UploadFile = File(..., description="Face photo (JPEG/PNG/WebP, max 10 MB)"),
    _quota: dict = Depends(require_quota("face_style")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a face photo, AI will identify face shape and recommend hairstyles & hair colors.

    Accepts **multipart/form-data** with a single file field ``image``.

    Returns:
    - Face shape identification and analysis
    - Skin tone assessment
    - Top 3 hairstyle recommendations (with styling tips)
    - Top 3 hair color recommendations (with hex codes)
    - Overall styling advice
    """
    # ---- Validate file type ----
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. "
                   f"Allowed: {', '.join(settings.allowed_image_types)}",
        )

    # ---- Read & validate size ----
    file_bytes = await image.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
                   f"Maximum allowed: {settings.max_upload_size_mb} MB.",
        )

    # ---- Save uploaded face image（用于「我的报告」列表缩略图）----
    input_image_url: Optional[str] = None
    try:
        ext = "png" if image.content_type == "image/png" else "webp" if image.content_type == "image/webp" else "jpg"
        filename = f"face-style-{uuid.uuid4().hex}.{ext}"
        save_dir = Path(settings.upload_dir) / "face"
        save_dir.mkdir(parents=True, exist_ok=True)
        (save_dir / filename).write_bytes(file_bytes)
        input_image_url = f"/uploads/face/{filename}"
    except Exception as save_err:
        print(f"⚠️ Face-style input image save skipped: {save_err}")

    # ---- Convert to data URI for OpenAI Vision ----
    data_uri = file_to_data_uri(file_bytes, image.content_type)

    # ---- Call LLM ----
    try:
        result = await face_analysis_service.analyze_face_for_styling(data_uri)

        response = FaceStyleResponse(
            input_image_url=input_image_url,
            face_shape=result.get("face_shape", "oval"),
            face_shape_cn=result.get("face_shape_cn", "鵝蛋臉"),
            face_analysis=result.get("face_analysis", ""),
            skin_tone=result.get("skin_tone", ""),
            hairstyle_recommendations=[
                HairStyleRecommendation(**h)
                for h in result.get("hairstyle_recommendations", [])
            ],
            hair_color_recommendations=[
                HairColorRecommendation(**c)
                for c in result.get("hair_color_recommendations", [])
            ],
            overall_advice=result.get("overall_advice", ""),
        )

        # 不在分析接口自动保存：只保留 APP 端完成整套流程后保存的那一条完整 AI 发型（含 3 张效果图），且新结果不覆盖旧结果。

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Face style analysis failed: {str(e)}")


@router.post("/face-edit", response_model=ImageEditResponse)
async def edit_face_photo(
    image: UploadFile = File(..., description="Original face photo (JPEG/PNG/WebP, max 10 MB)"),
    instructions: str = Form(..., description="Modification instructions, e.g. '改成短发，染成蜜茶色'"),
    provider: Optional[str] = Form(
        None,
        description=(
            "Image edit provider: 'gemini' or 'gpt-image-1'. "
            "Defaults to the server-side config value."
        ),
    ),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a face photo **and** hair modification instructions →
    AI edits the photo, changing only the hair.

    **Accepts** ``multipart/form-data`` with:
    - ``image`` — the original face photo
    - ``instructions`` — what to change (e.g. "改成齐耳短发，蜜茶棕色")
    - ``provider``  *(optional)* — ``"gemini"`` or ``"gpt-image-1"``

    **Providers**:

    | Provider | Backend | Face preservation |
    |----------|---------|-------------------|
    | ``gemini``        | Gemini generateContent (e.g. gemini-3-pro-image-preview) | Prompt-based |
    | ``gpt-image-1``  | OpenAI images.edit + mask | Mask-based (vision-detected face region) |

    **Returns**:
    - ``image_url`` — relative URL to download the edited image (persistent)
    - ``image_path`` — server-side file path
    - ``modification_applied`` — echo of the requested modifications
    - ``provider`` — which provider was actually used
    """
    # ---- Validate file type ----
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. "
                   f"Allowed: {', '.join(settings.allowed_image_types)}",
        )

    # ---- Read & validate size ----
    file_bytes = await image.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
                   f"Maximum allowed: {settings.max_upload_size_mb} MB.",
        )

    # ---- Resolve effective provider ----
    effective_provider = (provider or settings.image_edit_provider).lower().strip()

    # ---- Call image edit service ----
    try:
        edited_bytes = await openai_service.edit_image(
            image_bytes=file_bytes,
            content_type=image.content_type,
            instructions=instructions,
            provider=effective_provider,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Photo editing failed: {str(e)}")

    # ---- Save to local file ----
    filename = f"{uuid.uuid4().hex}.png"
    save_dir = Path(settings.upload_dir) / settings.edited_images_subdir
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    save_path.write_bytes(edited_bytes)

    # Relative URL that the client can use to download the image
    relative_url = f"/uploads/{settings.edited_images_subdir}/{filename}"

    response = ImageEditResponse(
        image_url=relative_url,
        image_path=str(save_path),
        modification_applied=instructions,
        provider=effective_provider,
    )

    # ---- Auto-save to history (only for logged-in users) ----
    if current_user:
        try:
            await history_service.save_report(
                db=db,
                user_id=current_user.id,
                report_type="face_edit",
                title=f"发型编辑 — {instructions[:20]}",
                data=response.model_dump(mode="json"),
                summary=instructions[:100],
                thumbnail_url=relative_url,
            )
        except Exception:
            pass

    return response


@router.post("/face-edit-by-reference", response_model=ImageEditResponse)
async def edit_face_photo_by_reference(
    image: UploadFile = File(..., description="用户人像照片 (JPEG/PNG/WebP, max 10 MB)"),
    reference_image: UploadFile = File(..., description="髮型參考圖 (用戶想要的效果髮型照片)"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    根據髮型參考圖換發：上傳人像照 + 髮型參考圖，將參考圖上的髮型遷移到人像上，生成效果圖。
    用於理髮師溝通卡「髮型參考圖」模式；生成效果圖後可再調用 POST /hairstyle/stylist-card 生成溝通卡。

    **Accepts** ``multipart/form-data``:
    - ``image`` — 用戶人像照片（必填）
    - ``reference_image`` — 髮型參考圖（必填）

    **Returns**: 與「人像換發」相同結構（image_url、image_path、modification_applied、provider）。
    """
    allowed = settings.allowed_image_types
    for f, name in [(image, "image"), (reference_image, "reference_image")]:
        ct = (f.content_type or "").split(";")[0].strip().lower()
        if ct and ct not in allowed and ct != "image/jpg":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported type for {name}: {f.content_type}. "
                       f"Allowed: {', '.join(allowed)}",
            )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    file_bytes = await image.read()
    ref_bytes = await reference_image.read()
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Portrait image too large (max {settings.max_upload_size_mb} MB).",
        )
    if len(ref_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Reference image too large (max {settings.max_upload_size_mb} MB).",
        )

    try:
        edited_bytes = await openai_service.edit_image_by_reference(
            image_bytes=file_bytes,
            content_type=image.content_type or "image/jpeg",
            reference_image_bytes=ref_bytes,
            reference_content_type=reference_image.content_type or "image/jpeg",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Face edit by reference failed: {str(e)}")

    filename = f"{uuid.uuid4().hex}.png"
    save_dir = Path(settings.upload_dir) / settings.edited_images_subdir
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    save_path.write_bytes(edited_bytes)
    relative_url = f"/uploads/{settings.edited_images_subdir}/{filename}"

    response = ImageEditResponse(
        image_url=relative_url,
        image_path=str(save_path),
        modification_applied="已根據參考圖遷移髮型",
        provider="gemini",
    )

    if current_user:
        try:
            await history_service.save_report(
                db=db,
                user_id=current_user.id,
                report_type="face_edit",
                title="髮型參考圖換發",
                data=response.model_dump(mode="json"),
                summary="根據髮型參考圖生成效果圖",
                thumbnail_url=relative_url,
            )
        except Exception:
            pass

    return response


@router.post("/hair-color-experiment", response_model=ImageEditResponse)
async def hair_color_experiment(
    image: UploadFile = File(..., description="Face photo (JPEG/PNG/WebP, max 10 MB)"),
    hair_color: str = Form(..., description="发色名称，如：蜜茶棕、栗棕色、黑茶色、亚麻金、玫瑰金、雾霾蓝"),
    provider: Optional[str] = Form(
        None,
        description=(
            "Image edit provider: 'gemini' or 'gpt-image-1'. "
            "Defaults to the server-side config value."
        ),
    ),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    **AI 实验室 - 发色实验**：上传照片 + 选择发色 → 生成仅改变发色的新照片。

    **Accepts** ``multipart/form-data`` with:
    - ``image`` — 用户上传的人像照片
    - ``hair_color`` — 目标发色（中文名，如：蜜茶棕、栗棕色、黑茶色、亚麻金、玫瑰金、雾霾蓝）
    - ``provider`` *(optional)* — ``"gemini"`` or ``"gpt-image-1"``

    仅修改头发颜色，保持脸型、五官、肤色、发型、背景等不变。底层复用与 face-edit 相同的 image edit 能力。

    **Returns**:
    - ``image_url`` — 生成图片的相对下载地址
    - ``image_path`` — 服务端存储路径
    - ``modification_applied`` — 本次修改描述（发色）
    - ``provider`` — 实际使用的编辑引擎
    """
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. "
                   f"Allowed: {', '.join(settings.allowed_image_types)}",
        )

    file_bytes = await image.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
                   f"Maximum allowed: {settings.max_upload_size_mb} MB.",
        )

    hair_color_clean = (hair_color or "").strip()
    if not hair_color_clean:
        raise HTTPException(status_code=400, detail="hair_color is required")

    # 发色实验：只改发色，不改发型/脸型/五官/背景
    instructions = f"将照片中人物的头发染成「{hair_color_clean}」发色。保持发型、脸型、五官、肤色、背景、光线完全不变，只改变头发颜色。输出一张写实风格的照片。"

    effective_provider = (provider or settings.image_edit_provider).lower().strip()

    try:
        edited_bytes = await openai_service.edit_image(
            image_bytes=file_bytes,
            content_type=image.content_type,
            instructions=instructions,
            provider=effective_provider,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hair color experiment failed: {str(e)}")

    filename = f"{uuid.uuid4().hex}.png"
    save_dir = Path(settings.upload_dir) / settings.edited_images_subdir
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    save_path.write_bytes(edited_bytes)

    relative_url = f"/uploads/{settings.edited_images_subdir}/{filename}"

    response = ImageEditResponse(
        image_url=relative_url,
        image_path=str(save_path),
        modification_applied=f"发色实验：{hair_color_clean}",
        provider=effective_provider,
    )

    if current_user:
        try:
            await history_service.save_report(
                db=db,
                user_id=current_user.id,
                report_type="hair_color_experiment",
                title=f"发色实验 — {hair_color_clean}",
                data=response.model_dump(mode="json"),
                summary=hair_color_clean[:100],
                thumbnail_url=relative_url,
            )
        except Exception:
            pass

    return response


@router.post("/color", response_model=ColorDiagnosisResponse)
async def diagnose_color(
    image: UploadFile = File(..., description="Face/skin photo (JPEG/PNG/WebP, max 10 MB)"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Diagnose personal color type and provide color recommendations.

    **Accepts** ``multipart/form-data`` with:
    - ``image`` — face/skin photo (required; APP 端必须上传图片文件，不能传本地 file:// URL)

    Returns comprehensive color diagnosis including:
    - Personal color season type
    - Skin undertone analysis
    - Best colors to wear
    - Colors to avoid
    - Makeup color recommendations
    - Hair color recommendations
    """
    if image.content_type not in settings.allowed_image_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image.content_type}. "
                   f"Allowed: {', '.join(settings.allowed_image_types)}",
        )

    file_bytes = await image.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes) / 1024 / 1024:.1f} MB). "
                   f"Maximum allowed: {settings.max_upload_size_mb} MB.",
        )

    data_uri = file_to_data_uri(file_bytes, image.content_type)

    try:
        result = await color_diagnosis_service.diagnose_color(data_uri)

        # Convert color dictionaries to ColorInfo objects
        best_colors = [ColorInfo(**c) for c in result.get("best_colors", [])]
        avoid_colors = [ColorInfo(**c) for c in result.get("avoid_colors", [])]
        neutral_colors = [ColorInfo(**c) for c in result.get("neutral_colors", [])]
        hair_colors = [ColorInfo(**c) for c in result.get("hair_colors", [])]

        # Convert makeup colors
        makeup_colors = {}
        for key, colors in result.get("makeup_colors", {}).items():
            makeup_colors[key] = [ColorInfo(**c) for c in colors]

        response = ColorDiagnosisResponse(
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
        if current_user:
            try:
                await history_service.save_report(
                    db=db,
                    user_id=current_user.id,
                    report_type="color_diagnosis",
                    title=f"色彩診斷 — {response.season_type_cn}",
                    data=response.model_dump(mode="json"),
                    summary=response.analysis[:100] if response.analysis else response.season_type_cn,
                    thumbnail_url=None,
                )
            except Exception:
                pass
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Color diagnosis failed: {str(e)}")


@router.post("/body", response_model=BodyAnalysisResponse)
async def analyze_body(
    request: BodyAnalysisRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
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

        response = BodyAnalysisResponse(
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
        if current_user:
            try:
                await history_service.save_report(
                    db=db,
                    user_id=current_user.id,
                    report_type="body_analysis",
                    title=f"身材風格 — {response.body_type_cn}",
                    data=response.model_dump(mode="json"),
                    summary=(response.body_type_description or response.body_type_cn)[:100],
                    thumbnail_url=None,
                )
            except Exception:
                pass
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Body analysis failed: {str(e)}")


@router.post("/landing-suggestion", response_model=LandingSuggestionResponse)
async def create_landing_suggestion(
    request: LandingSuggestionRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    报告落地建议：结合脸部分析、色彩诊断、身材风格、命理色谱、当日运势等，生成全面且精简的落地建议。

    请求体可传入多模块数据（与各分析接口的响应或历史报告详情的 data 一致），至少传入一项。
    后端会综合已有维度，用 AI 生成一段总述 + 3～5 个分板块的可执行建议。
    若用户已登录，结果会自动写入「我的报告」，类型为 landing_suggestion。
    """
    if not any([
        request.face_analysis,
        request.color_diagnosis,
        request.body_analysis,
        request.destiny_fortune,
        request.daily_energy,
    ]):
        raise HTTPException(
            status_code=400,
            detail="请至少传入一项分析数据（face_analysis / color_diagnosis / body_analysis / destiny_fortune / daily_energy）",
        )

    try:
        result = await landing_suggestion_service.generate(
            face_analysis=request.face_analysis,
            color_diagnosis=request.color_diagnosis,
            body_analysis=request.body_analysis,
            destiny_fortune=request.destiny_fortune,
            daily_energy=request.daily_energy,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成落地建议失败: {str(e)}")

    sections = [
        LandingSuggestionSection(title=s["title"], content=s["content"])
        for s in result.get("sections", [])
    ]
    report_id: Optional[str] = None
    if current_user:
        try:
            report_id = await history_service.save_report(
                db=db,
                user_id=current_user.id,
                report_type="landing_suggestion",
                title="全面落地建议",
                data={
                    "summary": result.get("summary") or "",
                    "sections": result.get("sections", []),
                },
                summary=(result.get("summary") or "")[:100],
                thumbnail_url=None,
            )
        except Exception:
            pass

    return LandingSuggestionResponse(
        summary=result.get("summary") or "",
        sections=sections,
        report_id=report_id,
    )

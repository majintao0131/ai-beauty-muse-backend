"""
AI Beauty Muse - FastAPI Main Application
"""
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import HealthResponse
from app.models.database import init_db
from app.api import analysis, hairstyle, destiny, daily, chat, auth, membership, history, media


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    await init_db()
    print("📦 Database tables initialised")
    # Ensure upload directories exist
    edited_dir = Path(settings.upload_dir) / settings.edited_images_subdir
    edited_dir.mkdir(parents=True, exist_ok=True)
    beauty_dir = Path(settings.upload_dir) / "beauty"
    beauty_dir.mkdir(parents=True, exist_ok=True)
    face_dir = Path(settings.upload_dir) / "face"
    face_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Upload directory ready: {edited_dir.resolve()}")
    print(f"📍 Server running at http://{settings.host}:{settings.port}")
    print(f"📚 API docs available at http://{settings.host}:{settings.port}/docs")
    yield
    # Shutdown
    print(f"👋 Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
# AI Beauty Muse Backend API

AI-powered beauty and styling assistant API providing:

## Features

- **Face Analysis**: Analyze face shape and get personalized recommendations
- **Color Diagnosis**: Determine personal color type and get color palette
- **Body Analysis**: Analyze body type and get styling recommendations
- **Photo Editing**: Upload photo + instructions → AI-generated modified portrait
- **Hairstyle Generation**: AI-generated hairstyle previews
- **Destiny Analysis**: BaZi-based color and styling recommendations
- **Daily Energy**: Daily outfit and energy guidance
- **AI Chat**: Interactive beauty assistant with server-side session management

## Authentication

Phone-based JWT authentication:
1. Call `POST /api/v1/auth/sms/send` with phone number to get verification code
2. Call `POST /api/v1/auth/sms/login` with phone + code to login/register and get Bearer token
3. Include token in all authenticated requests: `Authorization: Bearer <token>`

Legacy device-based auth (`POST /api/v1/auth/register`) is still supported.

## Chat Sessions

Chat history is managed server-side.  Create a session via
`POST /api/v1/chat/sessions`, then send messages referencing the `session_id`.
    """,
    version=settings.app_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(membership.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(hairstyle.router, prefix="/api/v1")
app.include_router(destiny.router, prefix="/api/v1")
app.include_router(daily.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")

# 图片通过鉴权接口 GET /api/v1/media/{path} 获取，不再公开挂载 /uploads
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "AI-powered beauty and styling assistant API",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(),
    )


@app.get("/api/v1", tags=["API Info"])
async def api_info():
    """API version information."""
    return {
        "version": "v1",
        "endpoints": {
            "auth": {
                "sms_send": "/api/v1/auth/sms/send  [POST] 发送验证码",
                "sms_login": "/api/v1/auth/sms/login  [POST] 手机号登录/注册",
                "register": "/api/v1/auth/register  [POST] 设备登录 (legacy)",
                "refresh": "/api/v1/auth/refresh  [POST] 刷新 token",
                "me": "/api/v1/auth/me  [GET] 个人信息+配额",
            },
            "membership": {
                "subscribe": "/api/v1/membership/subscribe  [POST] 订阅会员",
                "status": "/api/v1/membership/status  [GET] 会员状态",
                "quota": "/api/v1/membership/quota  [GET] 使用次数查询",
            },
            "analysis": {
                "face": "/api/v1/analysis/face",
                "face_style": "/api/v1/analysis/face-style  [POST multipart/form-data]",
                "face_edit": "/api/v1/analysis/face-edit  [POST multipart/form-data: image + instructions]",
                "face_edit_by_reference": "/api/v1/analysis/face-edit-by-reference  [POST multipart/form-data: image + reference_image]",
                "hair_color_experiment": "/api/v1/analysis/hair-color-experiment  [POST multipart/form-data: image + hair_color]",
                "color": "/api/v1/analysis/color",
                "body": "/api/v1/analysis/body",
                "landing_suggestion": "/api/v1/analysis/landing-suggestion  [POST JSON: 多模块数据]",
            },
            "hairstyle": {
                "generate": "/api/v1/hairstyle/generate",
                "color": "/api/v1/hairstyle/color",
                "stylist_card": "/api/v1/hairstyle/stylist-card",
            },
            "destiny": {
                "analyze": "/api/v1/destiny/analyze",
            },
            "daily": {
                "energy": "/api/v1/daily/energy",
                "quick": "/api/v1/daily/quick",
            },
            "chat": {
                "sessions": "/api/v1/chat/sessions",
                "send_message": "/api/v1/chat/",
                "history": "/api/v1/chat/sessions/{session_id}/history",
                "suggestions": "/api/v1/chat/suggestions",
            },
            "media": {
                "protected_image": "/api/v1/media/{path}  [GET] 鉴权获取图片，需 Bearer token",
            },
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

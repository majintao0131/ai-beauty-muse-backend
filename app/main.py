"""
AI Beauty Muse - FastAPI Main Application
"""
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import HealthResponse
from app.api import analysis, hairstyle, destiny, daily, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
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
- **Hairstyle Generation**: AI-generated hairstyle previews
- **Destiny Analysis**: BaZi-based color and styling recommendations
- **Daily Energy**: Daily outfit and energy guidance
- **AI Chat**: Interactive beauty assistant

## Authentication

Currently, all endpoints are public. Authentication will be added in future versions.

## Rate Limiting

Please be mindful of API usage. Rate limiting may be implemented in future versions.
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
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(hairstyle.router, prefix="/api/v1")
app.include_router(destiny.router, prefix="/api/v1")
app.include_router(daily.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


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
            "analysis": {
                "face": "/api/v1/analysis/face",
                "color": "/api/v1/analysis/color",
                "body": "/api/v1/analysis/body",
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
                "chat": "/api/v1/chat/",
                "suggestions": "/api/v1/chat/suggestions",
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

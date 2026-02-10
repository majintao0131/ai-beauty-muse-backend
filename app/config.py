"""
AI Beauty Muse Backend Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    app_name: str = "AI Beauty Muse Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 19000
    
    # CORS Settings
    # 使用 credentials 时不能写 "*"，需明确列出前端地址。Expo Web 默认 8081，可通过 CORS_ORIGINS 覆盖
    cors_origins: list[str] = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # LLM Provider: "openai" or "gemini"
    llm_provider: str = "gemini"
    
    # OpenAI Settings
    openai_api_key: Optional[str] = ""
    openai_base_url: Optional[str] = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    openai_vision_model: str = "gpt-4o"
    openai_image_model: str = "dall-e-3"
    openai_image_edit_model: str = "gpt-image-1"


    # Gemini Settings (uses OpenAI-compatible endpoint)
    gemini_api_key: Optional[str] = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-3-flash-preview"
    gemini_vision_model: str = "gemini-3-flash-preview"
    gemini_image_edit_model: str = "gemini-3-pro-image-preview"
    gemini_destiny_model: str = "gemini-3-pro-preview"   # Gemini 3 Pro for destiny/fortune

    # Image edit provider: "gpt-image-1" or "gemini"
    image_edit_provider: str = "gemini"

    # HTTP Proxy (留空表示不使用代理)
    # 示例: "http://127.0.0.1:7890" 或 "socks5://127.0.0.1:1080"
    http_proxy: Optional[str] = "http://127.0.0.1:10820"    # None

    # Upload / Storage Settings
    max_upload_size_mb: int = 10
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    upload_dir: str = "uploads"          # root dir for saved files
    edited_images_subdir: str = "edited" # sub-dir under upload_dir for edited images

    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./ai_beauty_muse.db"
    
    # JWT Settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days (long-lived for mobile)

    # SMS Settings (短信验证码)
    sms_provider: str = "mock"              # "mock" (dev) or "aliyun" / "tencent" (prod)
    sms_code_length: int = 6               # 验证码位数
    sms_code_expire_minutes: int = 5       # 验证码有效期
    sms_send_interval_seconds: int = 60    # 同一手机号发送间隔
    sms_test_phones: list[str] = ["18910284131"]   # 测试手机号列表（仅 mock 模式生效）
    sms_test_code: str = "000000"                   # 万能测试验证码（仅 mock 模式生效）

    # Quota Settings (功能使用次数)
    quota_free_limit: int = 10              # 免费用户每月每功能次数
    quota_member_limit: int = 10           # 会员每月每功能次数

    # Membership Settings (会员)
    membership_monthly_price: float = 19.9  # 月费 (元)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

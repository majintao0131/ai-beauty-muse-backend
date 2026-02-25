"""
AI Beauty Muse Backend Configuration

所有密钥与敏感配置均通过环境变量加载，优先从项目根目录的 .env 文件读取。
复制 .env.example 为 .env 并填入实际值，勿将 .env 提交到版本库。
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
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
    
    # OpenAI Settings（从 .env 加载，勿提交密钥到代码库）
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_vision_model: str = "gpt-4o"
    openai_image_model: str = "dall-e-3"
    openai_image_edit_model: str = "gpt-image-1"

    # Gemini Settings（从 .env 加载）
    gemini_api_key: Optional[str] = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-3-flash-preview"
    gemini_vision_model: str = "gemini-3-flash-preview"
    gemini_image_edit_model: str = "gemini-3-pro-image-preview"
    gemini_destiny_model: str = "gemini-3-pro-preview"   # Gemini 3 Pro for destiny/fortune

    # Image edit provider: "gpt-image-1" or "gemini"
    image_edit_provider: str = "gemini"
    # 调用 Gemini 图片生成/换发时的 HTTP 超时（秒），请求较慢时可适当调大，避免中途断连
    gemini_request_timeout_seconds: int = 300

    # HTTP Proxy（从 .env 加载，留空表示不使用代理）
    http_proxy: Optional[str] = None

    # Upload / Storage Settings
    max_upload_size_mb: int = 10
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    upload_dir: str = "uploads"          # root dir for saved files
    edited_images_subdir: str = "edited" # sub-dir under upload_dir for edited images

    # Database Settings
    database_url: str = "sqlite+aiosqlite:///./ai_beauty_muse.db"
    
    # JWT Settings（SECRET_KEY 必须通过 .env 设置，生产环境务必使用强随机串）
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days (long-lived for mobile)

    # SMS Settings (短信验证码)
    sms_provider: str = "mock"              # "mock" (dev) or "aliyun" / "tencent" (prod)
    sms_code_length: int = 6               # 验证码位数
    sms_code_expire_minutes: int = 5       # 验证码有效期
    sms_send_interval_seconds: int = 60    # 同一手机号发送间隔
    sms_test_phones: list[str] = []                 # 测试手机号列表（仅 mock 模式）
    sms_test_code: str = "000000"                   # 万能测试验证码（仅 mock 模式）

    @field_validator("sms_test_phones", mode="before")
    @classmethod
    def parse_sms_test_phones(cls, v):  # .env 中可用逗号分隔: SMS_TEST_PHONES=138xxx,189xxx
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v or []

    # Quota Settings (功能使用次数)
    quota_free_limit: int = 10              # 免费用户每月每功能次数
    quota_member_limit: int = 10            # 会员每月每功能次数
    quota_disabled: bool = False            # 为 True 时不做次数限制（测试环境可设 QUOTA_DISABLED=true）

    # Membership Settings (会员)
    membership_monthly_price: float = 19.9  # 月费 (元)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        # 环境变量名与字段名一致，如 OPENAI_API_KEY -> openai_api_key（不区分大小写）


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

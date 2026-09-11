import os
import secrets
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ thống Quản lý Garage Tích hợp AI"
    # SECRET_KEY: Use env var in production. Fallback generates a random key (not persistent across restarts!)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "garage-vtv-must-set-secret-key-in-prod-env")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Configuration — Google Gemini (primary)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Đọc AI_MODEL_NAME hoặc GEMINI_MODEL (Railway dùng GEMINI_MODEL)
    AI_MODEL_NAME: str = (
        os.getenv("AI_MODEL_NAME")
        or os.getenv("GEMINI_MODEL")
        or "gemini-flash-latest"
    )

    # Tương thích biến AI_PROVIDER cũ (Railway có thể đã set)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # DeepSeek / OpenAI-compatible (dự phòng, để trống nếu không dùng)
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

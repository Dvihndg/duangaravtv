import os
import secrets
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ thống Quản lý Garage Tích hợp AI"
    # SECRET_KEY: Use env var in production. Fallback generates a random key (not persistent across restarts!)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "garage-vtv-must-set-secret-key-in-prod-env")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Configuration
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-9vWcOHQtsCZ5J0gu9wYTU7YawMLVDc80HoMilS9hOHgiQ9ks")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://seekai.cc/v1")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "deepseek-v4-pro")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

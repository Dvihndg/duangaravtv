import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ thống Quản lý Garage Tích hợp AI"
    SECRET_KEY: str = "garage-super-secret-jwt-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./garage.db")
    
    DEEPSEEK_API_KEY: str = "sk-9vWcOHQtsCZ5J0gu9wYTU7YawMLVDc80HoMilS9hOHgiQ9ks"
    DEEPSEEK_BASE_URL: str = "https://seekai.cc/v1"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_NAME: str = "deepseek-v4-pro"


    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()


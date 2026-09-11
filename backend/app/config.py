import os
import secrets
try:
    # pyrefly: ignore [missing-import]
    from pydantic_settings import BaseSettings  # type: ignore
except ImportError:
    try:
        # pyrefly: ignore [missing-import]
        from pydantic import BaseSettings  # type: ignore
    except ImportError:
        # pyrefly: ignore [missing-import]
        from pydantic import BaseModel as BaseSettings  # type: ignore

# Tự động nạp các file .env từ cả backend/ lẫn thư mục gốc vào os.environ
def _load_env_files():
    search_paths = [
        os.path.join(os.path.dirname(__file__), "../.env"),
        os.path.join(os.path.dirname(__file__), "../../.env"),
        os.path.abspath(".env")
    ]
    for p in search_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ or not os.environ[k]:
                                os.environ[k] = v
            except Exception:
                pass

_load_env_files()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hệ thống Quản lý Garage Tích hợp AI"
    # SECRET_KEY: Use env var in production. Fallback generates a random key (not persistent across restarts!)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "garage-vtv-must-set-secret-key-in-prod-env")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Configuration — Google Gemini (primary)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gemini-1.5-flash")
    # Groq AI (nhanh, miễn phí, không bị chặn VN)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # DeepSeek / OpenAI-compatible (dự phòng, để trống nếu không dùng)
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

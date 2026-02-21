from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AI Providers
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    qwen_api_key: Optional[str] = None
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_ai_provider: str = "gemini"

    # News
    tavily_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./deepstock.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ["../.env", ".env"], "env_file_encoding": "utf-8"}


settings = Settings()

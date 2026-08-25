from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dailyconnect.db"
    secret_key: str = "change-me-in-development"
    access_token_expire_minutes: int = 60 * 24
    frontend_url: str = "http://localhost:5173"
    api_url: str = "http://127.0.0.1:8000"
    cloudinary_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

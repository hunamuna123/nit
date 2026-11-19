from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "Нить API"
    api_prefix: str = "/api"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "postgresql+asyncpg://nit:nit@localhost:5434/nit"
    # nullpool только для тестов, иначе testclient ловит чужой event loop
    db_null_pool: bool = False

    jwt_secret: str = "dev-only-secret-change-me-in-production-0123456789"
    session_cookie: str = "nit_session"
    session_days: int = 30
    cookie_secure: bool = False

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "deepseek/deepseek-v4.1-flash"
    embedding_model: str = "baai/bge-m3"
    embedding_dim: int = 1024
    ai_fake: bool = False
    ai_user_hourly_limit: int = 40
    ai_timeout_s: float = 60.0

    s3_endpoint: str = "localhost:9010"
    s3_access_key: str = "nit"
    s3_secret_key: str = "nit-s3-secret"
    s3_bucket: str = "nit-media"
    s3_secure: bool = False
    s3_region: str = "us-east-1"
    media_url_prefix: str = "/media"
    upload_max_mb: int = 8

    # дольше этого без движения = бросил
    abandon_after_minutes: int = 30

    @property
    def ai_enabled(self) -> bool:
        return self.ai_fake or bool(self.openrouter_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application configuration loaded from environment."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Makeable Jobs API"
    APP_ENV: str = "development"
    DEBUG: bool = True

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    DATABASE_URL: str = "sqlite+aiosqlite:///./makeable.db"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,https://makeable-jobs.vercel.app"

    FIREBASE_CREDENTIALS: str = ""
    FIREBASE_CREDENTIALS_JSON: str = ""
    FIREBASE_PROJECT_ID: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    ADMIN_EMAIL: str = "admin@makeable.example"
    ADMIN_PASSWORD: str = "change-me"

    # Job providers (multi-source aggregation).
    JOB_PROVIDER: str = "serpapi"
    ENABLED_PROVIDERS: str = "serpapi,jsearch,usajobs,remoteok"
    SERPAPI_API_KEY: str = ""
    SERPAPI_GL: str = "IN"
    SERPAPI_MONTHLY_LIMIT: int = 250
    SERPAPI_CACHE_TTL_HOURS: float = 6.0

    USAJOBS_API_KEY: str = ""
    USAJOBS_EMAIL: str = ""
    JSEARCH_API_KEY: str = ""

    @property
    def enabled_provider_list(self) -> list[str]:
        return [p.strip() for p in self.ENABLED_PROVIDERS.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
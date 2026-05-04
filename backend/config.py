"""
Liopleurodon — Configuration
Loads all environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Liopleurodon"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Job Search APIs
    JSEARCH_API_KEY: str = ""
    SERPAPI_KEY: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_API_KEY: str = ""
    THEIRSTACK_API_KEY: str = ""
    APIFY_TOKEN: str = ""
    THEMUSE_API_KEY: str = ""
    FINDWORK_API_KEY: str = ""

    # AI Providers
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    SAMBANOVA_API_KEY: str = ""

    # Algolia
    ALGOLIA_APP_ID: str = ""
    ALGOLIA_API_KEY: str = ""
    ALGOLIA_INDEX_NAME: str = "jobhacker_jobs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

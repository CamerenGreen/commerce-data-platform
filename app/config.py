from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    postgres_dsn: str = "postgresql://commerce_app:commerce_dev@localhost:5432/commerce_data"
    mongo_dsn: str = "mongodb://localhost:27017"
    mongo_database: str = "commerce_data"
    redis_dsn: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

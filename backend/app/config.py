from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    app_origin: str = "https://localhost:8443"
    brevo_api_key: SecretStr = SecretStr("")
    mail_from_email: str = ""
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://equiptrack_app@127.0.0.1:5432/equiptrack"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POLYOCR_", extra="ignore")

    auth_enabled: bool = False
    api_key: str = ""
    cors_origins: list[str] = Field(default_factory=list)
    cors_allow_credentials: bool = False
    max_upload_mb: int = Field(default=10, gt=0)
    default_language: str = "zh"
    log_level: str = "INFO"
    translation_api_key: str | None = None
    translation_base_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8001/v1")
    translation_model: str = "change-me"

    @property
    def translation_enabled(self) -> bool:
        return bool(self.translation_api_key)

    @model_validator(mode="after")
    def validate_security_boundaries(self) -> "Settings":
        if self.auth_enabled and not self.api_key.strip():
            raise ValueError("Authentication requires a non-empty API key.")
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError("Wildcard CORS is not allowed when credentials are enabled.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()

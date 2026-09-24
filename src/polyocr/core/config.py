"""Environment-backed application settings."""

from pathlib import Path
from typing import Any

from pydantic import Field, HttpUrl, PositiveInt, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="POLYOCR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    auth_enabled: bool = True
    api_key: str = ""
    cors_origins: str = "http://localhost:8000"
    cors_allow_credentials: bool = False
    max_upload_mb: PositiveInt = 10
    max_image_pixels: PositiveInt = 25_000_000
    max_concurrency: PositiveInt = 2
    ocr_workers: PositiveInt = 2
    blur_variance_floor: float = 45.0
    default_language: str = "ch"
    max_translation_items: PositiveInt = 50
    max_translation_chars: PositiveInt = 20_000
    translation_api_key: str | None = Field(
        default=None,
        validation_alias="TRANSLATION_API_KEY",
    )
    translation_base_url: HttpUrl = Field(
        default="https://api.openai.com/v1",
        validation_alias="TRANSLATION_BASE_URL",
    )
    translation_model: str = Field(
        default="gpt-4o-mini",
        validation_alias="TRANSLATION_MODEL",
    )
    vl_api_key: str | None = Field(default=None, validation_alias="POLYOCR_VL_API_KEY")
    vl_max_upload_mb: PositiveInt = Field(
        default=20,
        validation_alias="POLYOCR_VL_MAX_UPLOAD_MB",
    )

    @field_validator("api_key", "translation_api_key", "vl_api_key")
    @classmethod
    def strip_secrets(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value

    @model_validator(mode="after")
    def validate_security(self) -> "Settings":
        if self.auth_enabled and not self.api_key:
            raise ValueError("POLYOCR_API_KEY is required when authentication is enabled")
        if self.cors_allow_credentials and "*" in self.cors_origin_list:
            raise ValueError("Wildcard CORS is forbidden when credentials are enabled")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def vl_max_upload_bytes(self) -> int:
        return self.vl_max_upload_mb * 1024 * 1024

    @property
    def translation_enabled(self) -> bool:
        return bool(self.translation_api_key)


def load_settings(env_file: str | Path = ".env", **overrides: Any) -> Settings:
    return Settings(_env_file=env_file, **overrides)

import pytest
from pydantic import ValidationError

from polyocr.core.config import Settings


def test_auth_requires_non_placeholder_key() -> None:
    with pytest.raises(ValidationError):
        Settings(auth_enabled=True, api_key="")


def test_credentials_reject_wildcard_cors() -> None:
    with pytest.raises(ValidationError):
        Settings(cors_origins=["*"], cors_allow_credentials=True)


def test_translation_is_optional() -> None:
    settings = Settings(auth_enabled=False, translation_api_key=None)
    assert settings.translation_enabled is False

import pytest
from fastapi import HTTPException

from polyocr.core.security import verify_api_key


def test_valid_api_key_is_accepted() -> None:
    assert verify_api_key("secret", "secret") is True


def test_invalid_api_key_is_rejected() -> None:
    assert verify_api_key("wrong", "secret") is False


def test_missing_key_raises_generic_error() -> None:
    with pytest.raises(HTTPException) as exc:
        verify_api_key(None, "secret", raise_error=True)
    assert exc.value.detail == "Missing or invalid API key."

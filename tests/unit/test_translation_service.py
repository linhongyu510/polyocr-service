import httpx
import pytest

from polyocr.api.errors import ServiceError
from polyocr.core.config import Settings
from polyocr.services.translation import TranslationService


@pytest.fixture
def settings() -> Settings:
    return Settings(
        auth_enabled=False,
        translation_api_key="translation-secret",
        translation_base_url="https://translator.test/v1",
        translation_model="test-model",
    )


async def test_provider_error_is_redacted(settings: Settings) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(401, json={"error": "secret upstream body"})
    )
    service = TranslationService(settings, transport=transport)
    with pytest.raises(ServiceError) as exc:
        await service.translate(["hello"], "zh")
    assert "secret upstream body" not in str(exc.value)


async def test_provider_response_is_parsed_without_network(settings: Settings) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": '["你好"]'}}]},
        )
    )
    service = TranslationService(settings, transport=transport)
    assert await service.translate(["hello"], "zh") == ["你好"]

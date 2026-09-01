import pytest
from fastapi.testclient import TestClient

from polyocr.core.config import Settings
from polyocr.main import create_app


@pytest.fixture
def translation_disabled_client() -> TestClient:
    return TestClient(create_app(settings=Settings(auth_enabled=False)))


@pytest.mark.parametrize("path", ["/v2/translate", "/v1/translation/translate"])
def test_missing_translation_config_is_explicit(
    translation_disabled_client: TestClient,
    path: str,
) -> None:
    response = translation_disabled_client.post(
        path,
        json={"texts": ["hello"], "target_language": "zh"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "translation_not_configured"

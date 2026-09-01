from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from polyocr.core.config import Settings
from polyocr.main import create_app
from polyocr.schemas.ocr import OCRItem


class FakeOCRService:
    def recognize(
        self,
        image: Image.Image,
        language: str,
        score_threshold: float,
        preprocess: bool,
    ) -> list[OCRItem]:
        assert image.mode == "RGB"
        assert language == "zh"
        assert score_threshold == 0.5
        assert preprocess is True
        return [OCRItem(text="测试", score=0.99, bbox=[[0, 0], [1, 0], [1, 1], [0, 1]])]


@pytest.fixture
def png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), "white").save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def client() -> TestClient:
    settings = Settings(auth_enabled=True, api_key="secret", max_upload_mb=1)
    return TestClient(create_app(settings=settings, ocr_service=FakeOCRService()))

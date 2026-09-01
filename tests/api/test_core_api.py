from fastapi.testclient import TestClient


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "PolyOCR Service"}


def test_ocr_requires_authentication(client: TestClient, png_bytes: bytes) -> None:
    response = client.post("/v1/ocr", files={"file": ("test.png", png_bytes, "image/png")})
    assert response.status_code == 401


def test_fake_ocr_returns_items(client: TestClient, png_bytes: bytes) -> None:
    response = client.post(
        "/v1/ocr",
        headers={"X-API-Key": "secret"},
        files={"file": ("test.png", png_bytes, "image/png")},
        data={"language": "zh", "score_threshold": "0.5", "preprocess": "true"},
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["text"] == "测试"


def test_broken_image_has_safe_error_and_request_id(client: TestClient) -> None:
    response = client.post(
        "/v1/ocr",
        headers={"Authorization": "Bearer secret"},
        files={"file": ("broken.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_image"
    assert error["request_id"]

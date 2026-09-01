import pytest

from polyocr.api.errors import ServiceError
from polyocr.services.ocr import decode_image, normalize_ocr_result


def test_normalizes_legacy_result() -> None:
    result = [[[[[0, 0], [10, 0], [10, 10], [0, 10]], ("hello", 0.98)]]]
    assert normalize_ocr_result(result, 0.5)[0].text == "hello"


def test_normalizes_mapping_result() -> None:
    result = [{"rec_texts": ["hello"], "rec_scores": [0.98], "dt_polys": [[[0, 0]]]}]
    assert normalize_ocr_result(result, 0.5)[0].score == 0.98


def test_rejects_invalid_threshold() -> None:
    with pytest.raises(ServiceError):
        normalize_ocr_result([], 1.1)


def test_rejects_broken_image() -> None:
    with pytest.raises(ServiceError, match="decode"):
        decode_image(b"not-an-image", max_bytes=1024)

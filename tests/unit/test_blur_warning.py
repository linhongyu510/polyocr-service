"""Tests for the Laplacian-variance motion-blur pre-warning."""

import asyncio
import io

import numpy as np
from PIL import Image

from polyocr.schemas.ocr import OCRItem
from polyocr.services.ocr import (
    DEFAULT_BLUR_VARIANCE_FLOOR,
    OCRService,
    laplacian_variance,
)


def _sharp_image() -> np.ndarray:
    # High-frequency checkerboard -> large Laplacian variance.
    tile = np.indices((64, 64)).sum(axis=0) % 2
    return (np.stack([tile, tile, tile], axis=-1) * 255).astype(np.uint8)


def _flat_image() -> np.ndarray:
    # Uniform grey -> Laplacian variance is ~0 (blurred / featureless).
    return np.full((64, 64, 3), 128, dtype=np.uint8)


def _png_from_array(array: np.ndarray) -> bytes:
    output = io.BytesIO()
    Image.fromarray(array).save(output, format="PNG")
    return output.getvalue()


def test_laplacian_variance_orders_sharp_above_flat() -> None:
    assert laplacian_variance(_sharp_image()) > laplacian_variance(_flat_image())


def test_laplacian_variance_tiny_image_never_warns() -> None:
    assert laplacian_variance(np.zeros((2, 2, 3), dtype=np.uint8)) == float("inf")


def _service_returning(items: list[OCRItem], array: np.ndarray) -> OCRService:
    class Backend:
        def predict(self, image: object) -> list[object]:
            # Mimic PaddleOCR 3.x mapping output built from the given items.
            return [
                {
                    "rec_texts": [i.text for i in items],
                    "rec_scores": [i.score for i in items],
                    "dt_polys": [[[0, 0], [1, 0], [1, 1], [0, 1]] for _ in items],
                }
            ]

    return OCRService(lambda _language: Backend())


def test_blurred_image_with_text_emits_warning() -> None:
    items = [OCRItem(text="ghost", score=0.97)]
    service = _service_returning(items, _flat_image())
    result = asyncio.run(service.recognize_detailed(_png_from_array(_flat_image()), "en", 0.5))
    assert [w.code for w in result.warnings] == ["suspected_blur"]
    assert result.warnings[0].detail["laplacian_variance"] < DEFAULT_BLUR_VARIANCE_FLOOR
    assert result.items[0].text == "ghost"


def test_sharp_image_emits_no_warning() -> None:
    items = [OCRItem(text="clean", score=0.97)]
    service = _service_returning(items, _sharp_image())
    result = asyncio.run(service.recognize_detailed(_png_from_array(_sharp_image()), "en", 0.5))
    assert result.warnings == []


def test_blurred_image_without_text_stays_silent() -> None:
    # A blank/blurred page that yields no text needs no advisory.
    service = _service_returning([], _flat_image())
    result = asyncio.run(service.recognize_detailed(_png_from_array(_flat_image()), "en", 0.5))
    assert result.warnings == []


def test_recognize_still_returns_plain_items() -> None:
    items = [OCRItem(text="compat", score=0.9)]
    service = _service_returning(items, _sharp_image())
    plain = asyncio.run(service.recognize(_png_from_array(_sharp_image()), "en", 0.5))
    assert [i.text for i in plain] == ["compat"]


def test_blur_floor_is_configurable() -> None:
    items = [OCRItem(text="edgey", score=0.9)]

    class Backend:
        def predict(self, image: object) -> list[object]:
            return [
                {
                    "rec_texts": [i.text for i in items],
                    "rec_scores": [i.score for i in items],
                    "dt_polys": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                }
            ]

    # A very high floor makes even a sharp image trip the warning.
    service = OCRService(lambda _l: Backend(), blur_variance_floor=1e12)
    result = asyncio.run(service.recognize_detailed(_png_from_array(_sharp_image()), "en", 0.5))
    assert [w.code for w in result.warnings] == ["suspected_blur"]

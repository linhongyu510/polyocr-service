from collections.abc import Mapping, Sequence
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from polyocr.api.errors import ServiceError
from polyocr.schemas.ocr import OCRItem


def _plain_list(value: Any) -> Any:
    return value.tolist() if hasattr(value, "tolist") else value


def decode_image(data: bytes, max_bytes: int) -> Image.Image:
    if len(data) > max_bytes:
        raise ServiceError("file_too_large", "Image exceeds the upload size limit.", 413)
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise ServiceError("invalid_image", "Could not decode image.", 422) from exc


def _mapping_items(value: Any) -> tuple[Sequence[Any], Sequence[Any], Sequence[Any]] | None:
    if isinstance(value, Mapping):
        source = value
        getter = source.get
    elif all(hasattr(value, field) for field in ("rec_texts", "rec_scores", "dt_polys")):
        getter = lambda field, default=None: getattr(value, field, default)
    else:
        return None

    texts = _plain_list(getter("rec_texts", []))
    scores = _plain_list(getter("rec_scores", []))
    boxes = _plain_list(getter("dt_polys", []))
    if not (len(texts) == len(scores) == len(boxes)):
        raise ServiceError("invalid_ocr_result", "OCR result fields have different lengths.", 500)
    return texts, scores, boxes


def normalize_ocr_result(result: Any, score_threshold: float) -> list[OCRItem]:
    if not 0 <= score_threshold <= 1:
        raise ServiceError("invalid_threshold", "Score threshold must be between 0 and 1.", 422)

    items: list[OCRItem] = []
    for page in _plain_list(result) or []:
        mapping_values = _mapping_items(page)
        if mapping_values is not None:
            texts, scores, boxes = mapping_values
            candidates = zip(boxes, zip(texts, scores))
        else:
            candidates = _plain_list(page)

        for candidate in candidates:
            try:
                bbox, recognition = candidate
                text, score = recognition
                numeric_score = float(score)
            except (TypeError, ValueError) as exc:
                raise ServiceError("invalid_ocr_result", "Unexpected OCR result structure.", 500) from exc
            if numeric_score >= score_threshold:
                items.append(
                    OCRItem(text=str(text), score=numeric_score, bbox=_plain_list(bbox))
                )
    return items

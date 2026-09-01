from collections.abc import Callable
from threading import RLock
from typing import Any, Protocol

from polyocr.api.errors import ServiceError
from polyocr.services.languages import normalize_language


class OCRBackend(Protocol):
    def ocr(self, image: Any, **kwargs: Any) -> Any: ...


class ModelManager:
    def __init__(self, factory: Callable[..., OCRBackend]) -> None:
        self._factory = factory
        self._models: dict[str, OCRBackend] = {}
        self._lock = RLock()

    def get(self, language: str) -> OCRBackend:
        paddle_code = normalize_language(language)
        with self._lock:
            if paddle_code in self._models:
                return self._models[paddle_code]
            try:
                model = self._factory(lang=paddle_code)
            except Exception as exc:
                raise ServiceError(
                    "model_unavailable",
                    f"OCR model for {paddle_code} could not be loaded.",
                    503,
                ) from exc
            self._models[paddle_code] = model
            return model

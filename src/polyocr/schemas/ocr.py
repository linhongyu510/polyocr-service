from typing import Any

from pydantic import BaseModel


class OCRItem(BaseModel):
    text: str
    score: float
    bbox: list[Any]


class OCRResponse(BaseModel):
    code: str = "ok"
    message: str = "OCR completed."
    request_id: str
    cost_ms: float
    language: str
    items: list[OCRItem]

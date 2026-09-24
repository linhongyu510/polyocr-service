"""OCR response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class OCRItem(BaseModel):
    text: str
    score: float = Field(ge=0, le=1)
    bbox: list[int] = Field(default_factory=list)


class OCRWarning(BaseModel):
    """A non-fatal advisory attached to a successful recognition.

    ``code`` is a stable machine-readable identifier (e.g. ``suspected_blur``);
    ``detail`` carries structured context such as the measured focus value.
    """

    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class OCRResponse(BaseModel):
    code: int = 0
    message: str = "Recognition succeeded."
    request_id: str
    cost_ms: float
    language: str
    items: list[OCRItem]
    warnings: list[OCRWarning] = Field(default_factory=list)

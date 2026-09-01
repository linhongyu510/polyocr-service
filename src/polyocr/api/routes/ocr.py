from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from polyocr.api.dependencies import get_ocr_service
from polyocr.core.security import require_api_key
from polyocr.schemas.ocr import OCRResponse
from polyocr.services.ocr import OCRService, decode_image

router = APIRouter()


@router.post("/v1/ocr", response_model=OCRResponse, dependencies=[Depends(require_api_key)])
async def recognize(
    request: Request,
    file: Annotated[UploadFile, File()],
    ocr_service: Annotated[OCRService, Depends(get_ocr_service)],
    language: Annotated[str, Form()] = "zh",
    score_threshold: Annotated[float, Form()] = 0.5,
    preprocess: Annotated[bool, Form()] = True,
) -> OCRResponse:
    started = perf_counter()
    settings = request.app.state.settings
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    image = decode_image(data, max_bytes)
    items = ocr_service.recognize(image, language, score_threshold, preprocess)
    return OCRResponse(
        request_id=request.state.request_id,
        cost_ms=round((perf_counter() - started) * 1000, 3),
        language=language,
        items=items,
    )

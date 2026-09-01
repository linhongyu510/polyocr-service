from fastapi import APIRouter, Depends, Request

from polyocr.core.security import require_api_key
from polyocr.schemas.translation import TranslationRequest, TranslationResponse
from polyocr.services.translation import TranslationService

router = APIRouter()


@router.post(
    "/v1/translation/translate",
    response_model=TranslationResponse,
    dependencies=[Depends(require_api_key)],
)
@router.post(
    "/v2/translate",
    response_model=TranslationResponse,
    dependencies=[Depends(require_api_key)],
)
async def translate(request: Request, payload: TranslationRequest) -> TranslationResponse:
    service = TranslationService(request.app.state.settings)
    translations = await service.translate(
        payload.texts,
        payload.target_language,
        request.state.request_id,
    )
    return TranslationResponse(
        translations=translations,
        request_id=request.state.request_id,
    )

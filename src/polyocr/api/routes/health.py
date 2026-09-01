from fastapi import APIRouter

from polyocr.schemas.common import HealthResponse

router = APIRouter()


@router.get("/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="PolyOCR Service")

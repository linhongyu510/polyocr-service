from collections.abc import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from polyocr.api.errors import ServiceError, service_error_handler
from polyocr.api.routes import health, languages, ocr, translation
from polyocr.core.config import Settings, get_settings
from polyocr.services.model_manager import ModelManager, OCRBackend
from polyocr.services.ocr import OCRService


def _paddle_factory(**kwargs: object) -> OCRBackend:
    from paddleocr import PaddleOCR

    return PaddleOCR(**kwargs)


def create_app(
    settings: Settings | None = None,
    ocr_service: OCRService | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_ocr_service = ocr_service or OCRService(ModelManager(_paddle_factory))
    app = FastAPI(title="PolyOCR Service", version="0.1.0")
    app.state.settings = resolved_settings
    app.state.ocr_service = resolved_ocr_service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=resolved_settings.cors_allow_credentials,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        request.state.request_id = request.headers.get("X-Request-ID") or uuid4().hex
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    app.add_exception_handler(ServiceError, service_error_handler)
    app.include_router(health.router)
    app.include_router(languages.router)
    app.include_router(ocr.router)
    app.include_router(translation.router)
    return app

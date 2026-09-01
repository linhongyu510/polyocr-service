from fastapi import Request

from polyocr.services.ocr import OCRService


def get_ocr_service(request: Request) -> OCRService:
    return request.app.state.ocr_service

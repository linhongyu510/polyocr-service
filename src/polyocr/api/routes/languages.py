from dataclasses import asdict

from fastapi import APIRouter

from polyocr.services.languages import supported_languages

router = APIRouter()


@router.get("/v1/languages")
def languages() -> list[dict[str, object]]:
    return [asdict(language) for language in supported_languages()]

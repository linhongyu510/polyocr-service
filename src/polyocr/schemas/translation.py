from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    texts: list[str] = Field(min_length=1)
    target_language: str = Field(min_length=1)


class TranslationResponse(BaseModel):
    translations: list[str]
    request_id: str

import json
import logging

import httpx

from polyocr.api.errors import ServiceError
from polyocr.core.config import Settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Translate each input text to the requested target language. "
    "Return only a JSON array of translated strings in the original order."
)


class TranslationService:
    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._transport = transport

    async def translate(
        self,
        texts: list[str],
        target_language: str,
        request_id: str = "",
    ) -> list[str]:
        if not self._settings.translation_enabled:
            raise ServiceError(
                "translation_not_configured",
                "Translation service is not configured.",
                503,
            )

        payload = {
            "model": self._settings.translation_model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"texts": texts, "target_language": target_language},
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        timeout = httpx.Timeout(30.0, connect=5.0, read=20.0, write=10.0, pool=5.0)
        try:
            async with httpx.AsyncClient(transport=self._transport, timeout=timeout) as client:
                response = await client.post(
                    f"{str(self._settings.translation_base_url).rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self._settings.translation_api_key}"},
                    json=payload,
                )
        except httpx.HTTPError as exc:
            logger.warning("Translation provider request failed request_id=%s", request_id)
            raise self._provider_error() from exc

        if not response.is_success:
            logger.warning(
                "Translation provider returned status=%s request_id=%s",
                response.status_code,
                request_id,
            )
            raise self._provider_error()

        try:
            content = response.json()["choices"][0]["message"]["content"]
            translations = json.loads(content)
            if not isinstance(translations, list) or not all(
                isinstance(item, str) for item in translations
            ):
                raise ValueError("Provider content is not a string list.")
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Translation provider response was invalid request_id=%s", request_id)
            raise self._provider_error() from exc
        return translations

    @staticmethod
    def _provider_error() -> ServiceError:
        return ServiceError(
            "translation_provider_error",
            "Translation provider request failed.",
            502,
        )

import secrets
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from polyocr.core.config import Settings


def verify_api_key(
    supplied_key: str | None,
    expected_key: str,
    *,
    raise_error: bool = False,
) -> bool:
    valid = bool(supplied_key) and secrets.compare_digest(supplied_key, expected_key)
    if not valid and raise_error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )
    return valid


def require_api_key(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    settings: Settings = request.app.state.settings
    if not settings.auth_enabled:
        return
    bearer_key = None
    if authorization and authorization.startswith("Bearer "):
        bearer_key = authorization.removeprefix("Bearer ").strip()
    verify_api_key(x_api_key or bearer_key, settings.api_key, raise_error=True)

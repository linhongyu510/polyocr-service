import pytest

from polyocr.api.errors import ServiceError
from polyocr.services.languages import normalize_language, supported_languages


@pytest.mark.parametrize(
    ("alias", "expected"),
    [("zh", "ch"), ("中文", "ch"), ("ja", "japan"), ("ko", "korean"), ("FR", "fr")],
)
def test_normalize_language(alias: str, expected: str) -> None:
    assert normalize_language(alias) == expected


def test_unknown_language_is_not_silently_fallback() -> None:
    with pytest.raises(ServiceError, match="Unsupported language"):
        normalize_language("not-a-language")


def test_language_list_has_unique_codes() -> None:
    codes = [item.code for item in supported_languages()]
    assert len(codes) == len(set(codes))

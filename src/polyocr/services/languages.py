from dataclasses import dataclass

from polyocr.api.errors import ServiceError


@dataclass(frozen=True)
class Language:
    code: str
    paddle_code: str
    name: str
    aliases: tuple[str, ...]


_LANGUAGES = (
    Language("zh", "ch", "中文", ("zh", "ch", "中文", "简体中文", "chinese")),
    Language("en", "en", "English", ("en", "english", "英文")),
    Language("ja", "japan", "日本語", ("ja", "jp", "japan", "japanese", "日文", "日本語")),
    Language("ko", "korean", "한국어", ("ko", "kr", "korean", "韩文", "한국어")),
    Language("fr", "fr", "Français", ("fr", "french", "法文", "français")),
    Language("de", "german", "Deutsch", ("de", "german", "德文", "deutsch")),
    Language("es", "es", "Español", ("es", "spanish", "西班牙文", "español")),
    Language("pt", "pt", "Português", ("pt", "portuguese", "葡萄牙文", "português")),
    Language("ru", "ru", "Русский", ("ru", "russian", "俄文", "русский")),
    Language("th", "th", "ไทย", ("th", "thai", "泰文", "ไทย")),
    Language("latin", "latin", "Latin", ("latin", "拉丁语", "拉丁语系")),
)

_ALIASES = {
    alias.strip().casefold(): language.paddle_code
    for language in _LANGUAGES
    for alias in language.aliases
}


def normalize_language(value: str) -> str:
    normalized = value.strip().casefold()
    try:
        return _ALIASES[normalized]
    except KeyError as exc:
        raise ServiceError(
            "unsupported_language",
            f"Unsupported language: {value}",
            422,
        ) from exc


def supported_languages() -> tuple[Language, ...]:
    return _LANGUAGES

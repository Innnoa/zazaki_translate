SUPPORTED_LANGUAGES = {"zh", "en"}


def contains_chinese(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _opposite_language(language_code: str) -> str:
    return "en" if language_code == "zh" else "zh"


def resolve_direction(
    text: str,
    from_code: str | None,
    to_code: str | None,
) -> tuple[str, str]:
    if from_code and to_code:
        return from_code, to_code
    if from_code:
        return from_code, _opposite_language(from_code)
    if to_code:
        return _opposite_language(to_code), to_code
    return ("zh", "en") if contains_chinese(text) else ("en", "zh")

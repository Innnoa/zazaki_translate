from trans_cli.core import contains_chinese, resolve_direction


def test_contains_chinese_detects_cjk_text() -> None:
    assert contains_chinese("你好 world") is True
    assert contains_chinese("hello world") is False


def test_resolve_direction_uses_auto_detection() -> None:
    assert resolve_direction("你好", None, None) == ("zh", "en")
    assert resolve_direction("hello", None, None) == ("en", "zh")


def test_resolve_direction_prefers_explicit_flags() -> None:
    assert resolve_direction("hello", "zh", "en") == ("zh", "en")

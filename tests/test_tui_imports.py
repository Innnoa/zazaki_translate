import importlib.util

import pytest

from trans_cli.backend import DependencyMissingError
from trans_cli.history import HistoryEntry
from trans_cli.tui.app import _append_history_safely, build_tui_app, run_tui

TEXTUAL_AVAILABLE = importlib.util.find_spec("textual") is not None


def test_run_tui_reports_missing_textual_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_textual(module_name: str):
        if module_name.startswith("textual"):
            raise ModuleNotFoundError(module_name)
        raise AssertionError(module_name)

    monkeypatch.setattr("trans_cli.tui.app.import_module", missing_textual)

    with pytest.raises(DependencyMissingError, match=r"pip install --no-build-isolation -e '\.\[tui\]'"):
        run_tui(object())


def test_append_history_safely_reports_write_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_append(*args, **kwargs) -> None:
        raise OSError("read-only")

    monkeypatch.setattr("trans_cli.tui.app.append_history", failing_append)

    message = _append_history_safely(
        HistoryEntry("hello", "你好", "en", "zh", "2026"),
        enabled=True,
    )

    assert message == "History was not saved: read-only"


def test_append_history_safely_ignores_disabled_history(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_append(*args, **kwargs) -> None:
        raise AssertionError("should not write")

    monkeypatch.setattr("trans_cli.tui.app.append_history", failing_append)

    assert _append_history_safely(
        HistoryEntry("hello", "你好", "en", "zh", "2026"),
        enabled=False,
    ) is None


@pytest.mark.asyncio
@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual behavior tests require the tui extra")
async def test_tui_uses_vim_page_navigation() -> None:
    app = build_tui_app(object())

    async with app.run_test() as pilot:
        assert app.current_page == "translate"

        await pilot.press("l")
        assert app.current_page == "history"

        await pilot.press("l")
        assert app.current_page == "models"

        await pilot.press("h")
        assert app.current_page == "history"


@pytest.mark.asyncio
@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual behavior tests require the tui extra")
async def test_tui_normal_mode_enter_starts_translation() -> None:
    class FakeTranslator:
        def translate(self, text, from_code=None, to_code=None):
            return f"{from_code or 'auto'}->{to_code or 'auto'}:{text}"

        def _load_modules(self):
            class Module:
                def get_installed_languages(self):
                    return []

            return object(), Module()

    app = build_tui_app(FakeTranslator())

    async with app.run_test() as pilot:
        app.query_one("#input").text = "hello"
        await pilot.press("enter")
        await pilot.pause(0.2)

        assert app.last_output == "auto->auto:hello"
        assert app.translation_in_progress is False

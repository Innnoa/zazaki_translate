"""TUI 导入测试"""

from __future__ import annotations

import importlib.util

import pytest

from trans_cli.tui.app import build_tui_app, run_tui
from trans_cli.tui.state import AppState, Mode, Page
from trans_cli.tui.keys import GLOBAL_BINDINGS, TRANSLATE_BINDINGS
from trans_cli.tui.widgets.sidebar import Sidebar, NavButton
from trans_cli.tui.widgets.history_item import HistoryItem
from trans_cli.tui.widgets.command_palette import CommandPalette, Command
from trans_cli.tui.views.translate import TranslateView
from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView

TEXTUAL_AVAILABLE = importlib.util.find_spec("textual") is not None


def test_tui_imports():
    """测试所有 TUI 模块均可导入"""
    # 验证导入成功
    assert build_tui_app is not None
    assert run_tui is not None
    assert AppState is not None
    assert Mode is not None
    assert Page is not None
    assert GLOBAL_BINDINGS is not None
    assert TRANSLATE_BINDINGS is not None
    assert Sidebar is not None
    assert NavButton is not None
    assert HistoryItem is not None
    assert CommandPalette is not None
    assert Command is not None
    assert TranslateView is not None
    assert HistoryView is not None
    assert ModelsView is not None
    assert SettingsView is not None


@pytest.mark.asyncio
@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual behavior tests require the tui extra")
async def test_tui_uses_vim_page_navigation() -> None:
    """测试 Vim 风格 h/l 页面导航"""
    from unittest.mock import MagicMock

    mock_config = MagicMock()
    mock_config.theme = "mocha"
    mock_config.default_direction = "zh-en"
    mock_config.save_history = False
    mock_config.startup_page = "translate"

    translator = MagicMock()

    import trans_cli.tui.app as app_module
    original_load_config = app_module.load_config
    app_module.load_config = lambda: mock_config
    try:
        app = build_tui_app(translator)

        async with app.run_test() as pilot:
            assert app.state.current_page == Page.TRANSLATE

            await pilot.press("l")
            assert app.state.current_page == Page.HISTORY

            await pilot.press("l")
            assert app.state.current_page == Page.MODELS

            await pilot.press("h")
            assert app.state.current_page == Page.HISTORY

            # l from history → models
            await pilot.press("l")
            assert app.state.current_page == Page.MODELS

            # l from models → settings
            await pilot.press("l")
            assert app.state.current_page == Page.SETTINGS

            # l from settings → translate (wrap around)
            await pilot.press("l")
            assert app.state.current_page == Page.TRANSLATE
    finally:
        app_module.load_config = original_load_config

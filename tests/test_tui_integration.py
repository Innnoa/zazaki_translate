"""TUI 集成测试

完整应用级别的集成测试：compose 结构、页面导航、命令面板。
"""

from __future__ import annotations

import importlib.util

import pytest

from unittest.mock import MagicMock

TEXTUAL_AVAILABLE = importlib.util.find_spec("textual") is not None

pytestmark = pytest.mark.skipif(
    not TEXTUAL_AVAILABLE, reason="Textual is required for TUI integration tests"
)


if TEXTUAL_AVAILABLE:
    from textual.app import App

    from trans_cli.tui.app import TransApp, build_tui_app
    from trans_cli.tui.state import Page
    from trans_cli.tui.widgets.sidebar import Sidebar
    from trans_cli.tui.widgets.command_palette import CommandPalette


def _make_mock_config(
    theme: str = "mocha",
    default_direction: str = "zh-en",
    save_history: bool = False,
    startup_page: str = "translate",
) -> MagicMock:
    """创建 mock 配置"""
    config = MagicMock()
    config.theme = theme
    config.default_direction = default_direction
    config.save_history = save_history
    config.startup_page = startup_page
    return config


def _make_translator() -> MagicMock:
    """创建 mock 翻译器"""
    translator = MagicMock()
    translator.translate.return_value = "翻译结果"
    return translator


def _patch_load_config(monkeypatch: pytest.MonkeyPatch, config: MagicMock | None = None):
    """Patch load_config in the app module.

    使用 monkeypatch 直接替换模块属性，避免 @patch 装饰器与 async 测试的交互问题。
    """
    if config is None:
        config = _make_mock_config()
    import trans_cli.tui.app as app_module
    monkeypatch.setattr(app_module, "load_config", lambda: config)
    return config


# ── Compose structure ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_app_compose_sidebar_and_main(monkeypatch):
    """应用 compose 应包含 sidebar 和 main 容器"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        # 侧边栏
        sidebar = pilot.app.query_one("#sidebar")
        assert sidebar is not None

        # 主区域
        main = pilot.app.query_one("#main")
        assert main is not None


@pytest.mark.asyncio
async def test_app_compose_all_views_exist(monkeypatch):
    """应用 compose 应包含所有四个页面视图"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        translate_page = pilot.app.query_one("#page-translate")
        assert translate_page is not None

        history_page = pilot.app.query_one("#page-history")
        assert history_page is not None

        models_page = pilot.app.query_one("#page-models")
        assert models_page is not None

        settings_page = pilot.app.query_one("#page-settings")
        assert settings_page is not None


@pytest.mark.asyncio
async def test_app_compose_status_bar(monkeypatch):
    """应用 compose 应包含状态栏"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        status_bar = pilot.app.query_one("#status-bar")
        assert status_bar is not None


@pytest.mark.asyncio
async def test_app_compose_header_footer(monkeypatch):
    """应用 compose 应包含 Header 和 Footer"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        from textual.widgets import Header, Footer

        header = pilot.app.query_one(Header)
        assert header is not None

        footer = pilot.app.query_one(Footer)
        assert footer is not None


@pytest.mark.asyncio
async def test_app_default_page_is_translate(monkeypatch):
    """默认启动页面应为 translate"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.state.current_page == Page.TRANSLATE


# ── Page navigation via action_show_page ───────────────────────────


@pytest.mark.asyncio
async def test_page_navigation_all_pages(monkeypatch):
    """action_show_page 应能切换到所有页面"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        # translate → history
        app.action_show_page("history")
        await pilot.pause()
        assert app.state.current_page == Page.HISTORY

        # history → models
        app.action_show_page("models")
        await pilot.pause()
        assert app.state.current_page == Page.MODELS

        # models → settings
        app.action_show_page("settings")
        await pilot.pause()
        assert app.state.current_page == Page.SETTINGS

        # settings → translate
        app.action_show_page("translate")
        await pilot.pause()
        assert app.state.current_page == Page.TRANSLATE


@pytest.mark.asyncio
async def test_page_navigation_invalid_falls_back_to_translate(monkeypatch):
    """无效页面名应回退到 translate"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        app.action_show_page("nonexistent")
        await pilot.pause()
        assert app.state.current_page == Page.TRANSLATE


# ── Page navigation via h/l keys ──────────────────────────────────


@pytest.mark.asyncio
async def test_key_l_cycles_forward(monkeypatch):
    """按 l 应依次切换到 history → models → settings → translate"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        assert app.state.current_page == Page.TRANSLATE

        await pilot.press("l")
        assert app.state.current_page == Page.HISTORY

        await pilot.press("l")
        assert app.state.current_page == Page.MODELS

        await pilot.press("l")
        assert app.state.current_page == Page.SETTINGS

        # wrap around
        await pilot.press("l")
        assert app.state.current_page == Page.TRANSLATE


@pytest.mark.asyncio
async def test_key_h_cycles_backward(monkeypatch):
    """按 h 应依次切换到 settings → models → history → translate"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        assert app.state.current_page == Page.TRANSLATE

        # wrap backward: translate → settings
        await pilot.press("h")
        assert app.state.current_page == Page.SETTINGS

        await pilot.press("h")
        assert app.state.current_page == Page.MODELS

        await pilot.press("h")
        assert app.state.current_page == Page.HISTORY

        await pilot.press("h")
        assert app.state.current_page == Page.TRANSLATE


@pytest.mark.asyncio
async def test_key_hl_roundtrip(monkeypatch):
    """h 后 l 应回到同一页面"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        for _ in range(4):
            original = app.state.current_page
            await pilot.press("l")
            await pilot.press("h")
            assert app.state.current_page == original


# ── Command palette via Ctrl+P ────────────────────────────────────


@pytest.mark.asyncio
async def test_ctrl_p_opens_command_palette(monkeypatch):
    """Ctrl+P 应打开命令面板"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        await pilot.pause()
        # 确认当前没有 CommandPalette 屏幕
        assert not any(
            isinstance(s, CommandPalette) for s in pilot.app.screen_stack
        )

        # 按 Ctrl+P
        await pilot.press("ctrl+p")
        await pilot.pause()

        # CommandPalette 应在 screen stack 上
        assert any(
            isinstance(s, CommandPalette) for s in pilot.app.screen_stack
        )


@pytest.mark.asyncio
async def test_command_palette_escape_closes(monkeypatch):
    """命令面板中按 Escape 应关闭"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        await pilot.press("ctrl+p")
        await pilot.pause()

        palette_on_stack = any(
            isinstance(s, CommandPalette) for s in pilot.app.screen_stack
        )
        assert palette_on_stack

        await pilot.press("escape")
        await pilot.pause()

        palette_on_stack = any(
            isinstance(s, CommandPalette) for s in pilot.app.screen_stack
        )
        assert not palette_on_stack


@pytest.mark.asyncio
async def test_command_palette_navigates_to_page(monkeypatch):
    """命令面板选择 translate 命令应切换到 translate 页面"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        # 先切到 history 页
        app.action_show_page("history")
        await pilot.pause()
        assert app.state.current_page == Page.HISTORY

        # 打开命令面板
        await pilot.press("ctrl+p")
        await pilot.pause()

        # CommandPalette is a ModalScreen — query from the active screen
        from textual.widgets import Input

        active_screen = pilot.app.screen
        cmd_input = active_screen.query_one("#command-input", Input)
        cmd_input.value = "translate"
        await pilot.pause()

        # 选择命令
        await pilot.press("enter")
        await pilot.pause()

        # 应切换回 translate 页面
        assert app.state.current_page == Page.TRANSLATE


# ── Sidebar integration ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_sidebar_reflects_current_page(monkeypatch):
    """侧边栏应高亮当前页面"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        sidebar = pilot.app.query_one(Sidebar)

        # 默认 translate
        active = sidebar.query_one("#nav-translate")
        assert "nav-active" in active.classes

        # 切换到 history
        app.action_show_page("history")
        await pilot.pause()

        active = sidebar.query_one("#nav-history")
        assert "nav-active" in active.classes

        # translate 不再高亮
        translate_btn = sidebar.query_one("#nav-translate")
        assert "nav-active" not in translate_btn.classes


@pytest.mark.asyncio
async def test_sidebar_button_click_navigates(monkeypatch):
    """点击侧边栏按钮应导航到对应页面"""
    _patch_load_config(monkeypatch)
    app = build_tui_app(_make_translator())

    async with app.run_test() as pilot:
        from textual.widgets import Button

        sidebar = pilot.app.query_one(Sidebar)
        history_btn = sidebar.query_one("#nav-history")

        # 触发按钮事件 (Button.Pressed is the event class in Textual 6.x)
        event = Button.Pressed(history_btn)
        pilot.app.on_button_pressed(event)
        await pilot.pause()

        assert app.state.current_page == Page.HISTORY


# ── App class-level checks ────────────────────────────────────────


def test_transapp_bindings_include_ctrl_p():
    """TransApp 应绑定 Ctrl+P"""
    binding_keys = [b.key for b in TransApp.BINDINGS]
    assert "ctrl+p" in binding_keys


def test_transapp_bindings_include_hl():
    """TransApp 应绑定 h 和 l"""
    binding_keys = [b.key for b in TransApp.BINDINGS]
    assert "h" in binding_keys
    assert "l" in binding_keys


def test_transapp_bindings_include_q():
    """TransApp 应绑定 q 退出"""
    binding_keys = [b.key for b in TransApp.BINDINGS]
    assert "q" in binding_keys


def test_build_tui_app_returns_transapp():
    """build_tui_app 应返回 TransApp 实例"""
    translator = _make_translator()
    import trans_cli.tui.app as app_module

    original = app_module.load_config
    app_module.load_config = lambda: _make_mock_config()
    try:
        result = build_tui_app(translator)
        assert isinstance(result, TransApp)
    finally:
        app_module.load_config = original

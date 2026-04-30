"""Sidebar 组件测试"""

import pytest
from textual.app import App, ComposeResult

from trans_cli.tui.state import Page
from trans_cli.tui.widgets.sidebar import NavButton, Sidebar


class SidebarApp(App):
    """测试应用"""

    def compose(self) -> ComposeResult:
        yield Sidebar()


@pytest.mark.asyncio
async def test_sidebar_compose():
    """测试 Sidebar 组合"""
    async with SidebarApp().run_test() as pilot:
        sidebar = pilot.app.query_one(Sidebar)
        assert sidebar is not None

        # 检查导航按钮
        buttons = sidebar.query(NavButton)
        assert len(buttons) == 4

        # 检查按钮页面
        pages = [btn.page for btn in buttons]
        assert Page.TRANSLATE in pages
        assert Page.HISTORY in pages
        assert Page.MODELS in pages
        assert Page.SETTINGS in pages


@pytest.mark.asyncio
async def test_sidebar_highlight():
    """测试高亮功能"""
    async with SidebarApp().run_test() as pilot:
        sidebar = pilot.app.query_one(Sidebar)

        # 高亮翻译页
        sidebar.highlight_page(Page.TRANSLATE)
        translate_btn = sidebar.query_one("#nav-translate", NavButton)
        assert "nav-active" in translate_btn.classes

        # 高亮历史页
        sidebar.highlight_page(Page.HISTORY)
        history_btn = sidebar.query_one("#nav-history", NavButton)
        assert "nav-active" in history_btn.classes
        assert "nav-active" not in translate_btn.classes

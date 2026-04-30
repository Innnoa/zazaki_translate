"""侧边导航栏组件"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Static

from trans_cli.tui.state import Page


# 导航项定义
NAV_ITEMS = [
    ("T", Page.TRANSLATE, "Translate", "ctrl+t"),
    ("H", Page.HISTORY, "History", "ctrl+h"),
    ("M", Page.MODELS, "Models", "ctrl+m"),
    ("S", Page.SETTINGS, "Settings", "ctrl+s"),
]


class NavButton(Button):
    """导航按钮"""

    def __init__(self, icon: str, page: Page, label: str, **kwargs) -> None:
        super().__init__(
            f"{icon} {label}",
            id=f"nav-{page.value}",
            classes="nav-button",
            **kwargs,
        )
        self.page = page


class Sidebar(Vertical):
    """侧边导航栏"""

    BINDINGS = [
        Binding("t", "navigate('translate')", "Translate", show=False),
        Binding("h", "navigate('history')", "History", show=False),
        Binding("m", "navigate('models')", "Models", show=False),
        Binding("s", "navigate('settings')", "Settings", show=False),
    ]

    def compose(self) -> ComposeResult:
        """组合组件"""
        yield Static("trans", classes="sidebar-title")
        for icon, page, label, _ in NAV_ITEMS:
            yield NavButton(icon, page, label)
        yield Static("q quit", classes="sidebar-hint")

    def action_navigate(self, page: str) -> None:
        """导航到指定页面"""
        self.app.action_show_page(page)  # type: ignore

    def highlight_page(self, page: Page) -> None:
        """高亮当前页面"""
        for nav_button in self.query(NavButton):
            if nav_button.page == page:
                nav_button.add_class("nav-active")
            else:
                nav_button.remove_class("nav-active")

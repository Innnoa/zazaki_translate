"""侧边导航栏组件"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static

from trans_cli.tui.state import Page


# 导航项定义
NAV_ITEMS = [
    ("T", Page.TRANSLATE, "Translate"),
    ("H", Page.HISTORY, "History"),
    ("M", Page.MODELS, "Models"),
    ("S", Page.SETTINGS, "Settings"),
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
    """侧边导航栏

    Navigation is handled via button clicks (on_button_pressed in app).
    Vim-style keys h/l are handled at the app level.
    """

    def compose(self) -> ComposeResult:
        """组合组件"""
        yield Static("trans", classes="accent")
        for icon, page, label in NAV_ITEMS:
            yield NavButton(icon, page, label)
        yield Static("q quit", classes="warning")

    def highlight_page(self, page: Page) -> None:
        """高亮当前页面"""
        for nav_button in self.query(NavButton):
            if nav_button.page == page:
                nav_button.add_class("nav-active")
            else:
                nav_button.remove_class("nav-active")

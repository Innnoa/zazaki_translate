"""历史记录视图"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, ListView, ListItem

from trans_cli.history import load_history, search_history
from trans_cli.tui.state import AppState
from trans_cli.tui.widgets.history_item import HistoryItem


class HistoryView(Vertical):
    """流式历史记录视图"""

    BINDINGS = [
        Binding("/", "search_history", "Search", show=True),
        Binding("r", "refresh_history", "Refresh", show=True),
        Binding("escape", "blur", "Esc", show=False),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state

    def compose(self) -> ComposeResult:
        """组合组件"""
        yield Input(placeholder="Search history...", id="history-search")
        yield ListView(id="history-list")

    def on_mount(self) -> None:
        """挂载后加载历史"""
        self._load_history()

    def _load_history(self, query: str = "") -> None:
        """加载历史记录"""
        list_view = self.query_one("#history-list", ListView)
        list_view.clear()

        if query:
            entries = search_history(query, limit=50)
        else:
            entries = load_history(limit=50)

        for entry in entries:
            list_view.append(ListItem(HistoryItem(entry)))

    def on_input_changed(self, event: Input.Changed) -> None:
        """搜索输入变化"""
        if event.input.id == "history-search":
            self._load_history(event.value.strip())

    def action_search_history(self) -> None:
        """聚焦搜索框"""
        self.query_one("#history-search", Input).focus()

    def action_refresh_history(self) -> None:
        """刷新历史记录"""
        search_input = self.query_one("#history-search", Input)
        self._load_history(search_input.value.strip())
        self.app.notify("History refreshed", severity="information")

    def action_blur(self) -> None:
        """取消焦点，退出输入模式"""
        self.screen.focus(None)

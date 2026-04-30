"""历史记录条目组件"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Label, Static

from trans_cli.history import HistoryEntry


class HistoryItem(Static):
    """单条历史记录"""

    def __init__(self, entry: HistoryEntry, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entry = entry

    def compose(self) -> ComposeResult:
        """组合组件"""
        with Horizontal(classes="history-item-header"):
            yield Label(self.entry.created_at[:19], classes="history-time")
            yield Label(
                f"{self.entry.from_code}→{self.entry.to_code}",
                classes="history-lang",
            )
        with Horizontal(classes="history-item-content"):
            yield Label(self.entry.input_text[:80], classes="history-source")
            yield Label("→", classes="history-arrow")
            yield Label(self.entry.output_text[:80], classes="history-translation")

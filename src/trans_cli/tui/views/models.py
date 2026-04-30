"""模型管理视图"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, DataTable, Label

from trans_cli.backend import (
    DependencyMissingError,
    ModelMissingError,
    TranslationRuntimeError,
)
from trans_cli.model_status import get_model_statuses, install_default_models
from trans_cli.tui.state import AppState


class ModelsView(Vertical):
    """模型管理视图"""

    BINDINGS = [
        Binding("r", "refresh_models", "Refresh", show=True),
        Binding("i", "install_models", "Install", show=True),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state

    def compose(self) -> ComposeResult:
        """组合组件"""
        yield Label("Models", classes="view-title")
        yield DataTable(id="models-table")
        yield Button("Install All Models", id="install-all", classes="action-button")

    def on_mount(self) -> None:
        """挂载后初始化"""
        table = self.query_one("#models-table", DataTable)
        table.add_columns("Language Pair", "Status", "Size")
        self._refresh_models()

    def _refresh_models(self) -> None:
        """刷新模型状态"""
        table = self.query_one("#models-table", DataTable)
        table.clear()

        statuses = get_model_statuses(self.state.translator)
        for status in statuses:
            status_text = "✓ Installed" if status.status == "installed" else "✗ Not Installed"
            size_text = "~50MB" if status.status == "installed" else "N/A"
            table.add_row(
                f"{status.from_code}→{status.to_code}",
                status_text,
                size_text,
            )

    def action_refresh_models(self) -> None:
        """刷新模型"""
        self._refresh_models()
        self.app.notify("Models refreshed", severity="information")

    def action_install_models(self) -> None:
        """安装模型"""
        try:
            install_default_models(self.state.translator)
            self._refresh_models()
            self.app.notify("Models installed", severity="information")
        except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
            self.app.notify(str(exc), severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮点击处理"""
        if event.button.id == "install-all":
            self.action_install_models()

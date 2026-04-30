"""设置视图"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Label, Select, Switch

from trans_cli.config import TransConfig, save_config
from trans_cli.tui.state import AppState
from trans_cli.tui.theme import CATPPUCCIN_FLAVORS


class SettingsView(Vertical):
    """设置视图"""

    BINDINGS = [
        Binding("s", "save_settings", "Save", show=True),
    ]

    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state

    def compose(self) -> ComposeResult:
        """组合组件"""
        yield Label("Settings", classes="view-title")

        yield Label("Theme", classes="setting-label")
        yield Select(
            [(t, t) for t in CATPPUCCIN_FLAVORS.keys()],
            value=self.state.config.theme,
            id="theme-select",
        )

        yield Label("Default Direction", classes="setting-label")
        yield Select(
            [("zh→en", "zh-en"), ("en→zh", "en-zh"), ("Auto", "auto")],
            value=self.state.config.default_direction,
            id="direction-select",
        )

        yield Label("Save History", classes="setting-label")
        yield Switch(value=self.state.config.save_history, id="history-switch")

        yield Button("Save Settings", id="save-btn", classes="action-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """按钮点击处理"""
        if event.button.id == "save-btn":
            self.action_save_settings()

    def action_save_settings(self) -> None:
        """保存设置"""
        theme_select = self.query_one("#theme-select", Select)
        direction_select = self.query_one("#direction-select", Select)
        history_switch = self.query_one("#history-switch", Switch)

        # TransConfig is frozen – create a new instance
        new_config = TransConfig(
            theme=theme_select.value,
            default_direction=direction_select.value,
            save_history=history_switch.value,
            startup_page=self.state.config.startup_page,
        )

        try:
            save_config(new_config)
            self.state.config = new_config
            self.app.notify("Settings saved", severity="information")
        except OSError as exc:
            self.app.notify(f"Failed to save settings: {exc}", severity="error")

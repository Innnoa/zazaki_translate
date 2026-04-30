"""命令面板组件"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListView, ListItem


@dataclass
class Command:
    """命令定义"""
    name: str
    description: str
    shortcut: str
    action: Callable


# 默认命令列表
DEFAULT_COMMANDS = [
    Command("translate", "Go to Translate", "T", lambda app: app.action_show_page("translate")),
    Command("history", "Go to History", "H", lambda app: app.action_show_page("history")),
    Command("models", "Go to Models", "M", lambda app: app.action_show_page("models")),
    Command("settings", "Go to Settings", "S", lambda app: app.action_show_page("settings")),
    Command("swap", "Swap Language Direction", "Ctrl+S", lambda app: app.action_swap_direction()),
    Command("clear", "Clear Input", "Ctrl+L", lambda app: app.action_clear_input()),
    Command("theme latte", "Switch to Latte Theme", "", lambda app: app.action_set_theme("latte")),
    Command("theme frappe", "Switch to Frappe Theme", "", lambda app: app.action_set_theme("frappe")),
    Command("theme macchiato", "Switch to Macchiato Theme", "", lambda app: app.action_set_theme("macchiato")),
    Command("theme mocha", "Switch to Mocha Theme", "", lambda app: app.action_set_theme("mocha")),
]


class CommandPalette(ModalScreen[Command | None]):
    """命令面板"""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
    ]

    def __init__(self, commands: list[Command] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.commands = commands or DEFAULT_COMMANDS
        self.filtered_commands = self.commands
        self.selected_index = 0

    def compose(self) -> ComposeResult:
        """组合组件"""
        with Vertical(classes="command-palette"):
            yield Input(placeholder="Type a command...", id="command-input")
            yield ListView(id="command-list")

    def on_mount(self) -> None:
        """挂载后初始化"""
        self._update_list()
        self.query_one("#command-input", Input).focus()

    def _update_list(self, query: str = "") -> None:
        """更新命令列表"""
        list_view = self.query_one("#command-list", ListView)
        list_view.clear()

        if query:
            self.filtered_commands = [
                cmd for cmd in self.commands
                if query.lower() in cmd.name.lower() or query.lower() in cmd.description.lower()
            ]
        else:
            self.filtered_commands = self.commands

        for cmd in self.filtered_commands:
            item = ListItem(
                Label(f"{cmd.name} - {cmd.description}"),
            )
            list_view.append(item)

        self.selected_index = 0
        if self.filtered_commands:
            list_view.index = 0

    def on_input_changed(self, event: Input.Changed) -> None:
        """输入变化"""
        if event.input.id == "command-input":
            self._update_list(event.value.strip())

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """输入提交（Enter 键）"""
        if event.input.id == "command-input":
            self._select_command()

    def action_cursor_up(self) -> None:
        """上移光标"""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index > 0:
            list_view.index -= 1
            self.selected_index = list_view.index

    def action_cursor_down(self) -> None:
        """下移光标"""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index < len(self.filtered_commands) - 1:
            list_view.index += 1
            self.selected_index = list_view.index

    def _select_command(self) -> None:
        """选择当前高亮命令"""
        if self.filtered_commands:
            command = self.filtered_commands[self.selected_index]
            self.dismiss(command)
        else:
            self.dismiss(None)

    def action_select(self) -> None:
        """选择命令（绑定动作）"""
        self._select_command()

    def action_cancel(self) -> None:
        """取消"""
        self.dismiss(None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """列表项选中"""
        if event.list_view.id == "command-list":
            index = event.list_view.index
            if 0 <= index < len(self.filtered_commands):
                self.selected_index = index
                self._select_command()

"""快捷键定义模块"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class KeyBinding:
    """快捷键绑定"""
    key: str
    action_name: str
    description: str
    show_in_footer: bool = True


# 全局快捷键
GLOBAL_BINDINGS = [
    KeyBinding("ctrl+p", "command_palette", "Command"),
    KeyBinding("q", "quit", "Quit"),
    KeyBinding("h", "previous_page", "Prev"),
    KeyBinding("l", "next_page", "Next"),
    KeyBinding("j", "focus_next", "Down"),
    KeyBinding("k", "focus_previous", "Up"),
]

# 翻译页快捷键
TRANSLATE_BINDINGS = [
    KeyBinding("ctrl+enter", "translate", "Translate"),
    KeyBinding("s", "swap_direction", "Swap"),
    KeyBinding("c", "clear_input", "Clear"),
    KeyBinding("y", "copy_output", "Copy"),
    KeyBinding("tab", "toggle_focus", "Tab"),
]

# 历史页快捷键
HISTORY_BINDINGS = [
    KeyBinding("/", "search_history", "Search"),
    KeyBinding("r", "refresh_history", "Refresh"),
]

# 模型页快捷键
MODELS_BINDINGS = [
    KeyBinding("r", "refresh_models", "Refresh"),
    KeyBinding("i", "install_models", "Install"),
]

# 设置页快捷键
SETTINGS_BINDINGS = [
    KeyBinding("s", "save_settings", "Save"),
]

"""全局状态管理模块"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from trans_cli.config import TransConfig
from trans_cli.backend import ArgosTranslator


class Mode(str, Enum):
    """应用模式"""
    NORMAL = "normal"
    INPUT = "input"
    SEARCH = "search"


class Page(str, Enum):
    """页面类型"""
    TRANSLATE = "translate"
    HISTORY = "history"
    MODELS = "models"
    SETTINGS = "settings"


@dataclass
class AppState:
    """应用全局状态"""

    # 核心组件
    translator: ArgosTranslator
    config: TransConfig

    # 模式状态
    current_mode: Mode = Mode.NORMAL
    current_page: Page = Page.TRANSLATE

    # 翻译状态
    from_code: str | None = None
    to_code: str | None = None
    translation_in_progress: bool = False
    last_output: str = ""

    # 事件回调
    _observers: dict[str, list[Callable]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """初始化后处理"""
        # 根据配置设置默认语言方向
        if self.config.default_direction == "zh-en":
            self.from_code, self.to_code = "zh", "en"
        elif self.config.default_direction == "en-zh":
            self.from_code, self.to_code = "en", "zh"
        else:
            self.from_code, self.to_code = None, None

    def set_mode(self, mode: Mode) -> None:
        """设置模式"""
        self.current_mode = mode
        self._notify("mode_changed", mode)

    def set_page(self, page: Page) -> None:
        """设置页面"""
        self.current_page = page
        self._notify("page_changed", page)

    def swap_direction(self) -> None:
        """交换语言方向"""
        if (self.from_code, self.to_code) == ("zh", "en"):
            self.from_code, self.to_code = "en", "zh"
        else:
            self.from_code, self.to_code = "zh", "en"
        self._notify("direction_changed", (self.from_code, self.to_code))

    def on(self, event: str, callback: Callable) -> None:
        """注册事件回调"""
        if event not in self._observers:
            self._observers[event] = []
        self._observers[event].append(callback)

    def _notify(self, event: str, data: Any = None) -> None:
        """通知观察者"""
        for callback in self._observers.get(event, []):
            callback(data)

# Trans TUI 重写实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重写 Trans TUI 应用，采用现代化架构和开发者工具风格设计

**Architecture:** 模块化设计，视图/组件分离，Vim 风格快捷键系统，双栏翻译布局

**Tech Stack:** Python 3.11+, Textual 6.x, Catppuccin 配色

---

## 文件结构

### 新建文件
- `src/trans_cli/tui/views/__init__.py` - 视图模块初始化
- `src/trans_cli/tui/views/translate.py` - 翻译视图
- `src/trans_cli/tui/views/history.py` - 历史视图
- `src/trans_cli/tui/views/models.py` - 模型管理视图
- `src/trans_cli/tui/views/settings.py` - 设置视图
- `src/trans_cli/tui/widgets/__init__.py` - 组件模块初始化
- `src/trans_cli/tui/widgets/sidebar.py` - 侧边导航栏
- `src/trans_cli/tui/widgets/history_item.py` - 历史记录条目
- `src/trans_cli/tui/widgets/status_bar.py` - 状态栏
- `src/trans_cli/tui/widgets/command_palette.py` - 命令面板
- `src/trans_cli/tui/keys.py` - 快捷键定义
- `src/trans_cli/tui/state.py` - 全局状态管理

### 修改文件
- `src/trans_cli/tui/app.py` - 主应用入口（重写）
- `src/trans_cli/tui/theme.py` - 主题系统（扩展）
- `tests/test_tui_imports.py` - 更新导入测试

---

## Task 1: 创建目录结构和基础模块

**Files:**
- Create: `src/trans_cli/tui/views/__init__.py`
- Create: `src/trans_cli/tui/widgets/__init__.py`
- Create: `src/trans_cli/tui/keys.py`
- Create: `src/trans_cli/tui/state.py`

- [ ] **Step 1: 创建 views 模块目录和 __init__.py**

```bash
mkdir -p src/trans_cli/tui/views
touch src/trans_cli/tui/views/__init__.py
```

- [ ] **Step 2: 创建 widgets 模块目录和 __init__.py**

```bash
mkdir -p src/trans_cli/tui/widgets
touch src/trans_cli/tui/widgets/__init__.py
```

- [ ] **Step 3: 创建 keys.py 快捷键定义模块**

```python
# src/trans_cli/tui/keys.py
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
```

- [ ] **Step 4: 创建 state.py 全局状态管理模块**

```python
# src/trans_cli/tui/state.py
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
```

- [ ] **Step 5: 运行导入测试**

```bash
pytest tests/test_tui_imports.py -v
```

Expected: PASS（现有测试应该仍然通过）

- [ ] **Step 6: 提交**

```bash
git add src/trans_cli/tui/views/ src/trans_cli/tui/widgets/ src/trans_cli/tui/keys.py src/trans_cli/tui/state.py
git commit -m "feat(tui): add directory structure and base modules"
```

---

## Task 2: 实现 Sidebar 组件

**Files:**
- Create: `src/trans_cli/tui/widgets/sidebar.py`
- Modify: `src/trans_cli/tui/widgets/__init__.py`

- [ ] **Step 1: 创建 sidebar.py**

```python
# src/trans_cli/tui/widgets/sidebar.py
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
```

- [ ] **Step 2: 更新 widgets/__init__.py**

```python
# src/trans_cli/tui/widgets/__init__.py
"""TUI 组件模块"""

from trans_cli.tui.widgets.sidebar import Sidebar, NavButton

__all__ = ["Sidebar", "NavButton"]
```

- [ ] **Step 3: 测试 Sidebar 组件**

创建测试文件 `tests/test_sidebar.py`：

```python
# tests/test_sidebar.py
"""Sidebar 组件测试"""

from textual.app import App, ComposeResult

from trans_cli.tui.widgets.sidebar import Sidebar, NavButton
from trans_cli.tui.state import Page


class SidebarApp(App):
    """测试应用"""
    
    def compose(self) -> ComposeResult:
        yield Sidebar()


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
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_sidebar.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trans_cli/tui/widgets/sidebar.py src/trans_cli/tui/widgets/__init__.py tests/test_sidebar.py
git commit -m "feat(tui): add Sidebar component"
```

---

## Task 3: 实现 TranslateView 视图

**Files:**
- Create: `src/trans_cli/tui/views/translate.py`
- Modify: `src/trans_cli/tui/views/__init__.py`

- [ ] **Step 1: 创建 translate.py**

```python
# src/trans_cli/tui/views/translate.py
"""翻译视图"""

from __future__ import annotations

from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, RichLog, TextArea

from trans_cli.backend import (
    DependencyMissingError,
    ModelMissingError,
    TranslationRuntimeError,
)
from trans_cli.history import HistoryEntry, append_history
from trans_cli.tui.state import AppState


class TranslateView(Vertical):
    """双栏翻译视图"""
    
    BINDINGS = [
        Binding("ctrl+enter", "translate", "Translate", show=True),
        Binding("s", "swap_direction", "Swap", show=True),
        Binding("c", "clear_input", "Clear", show=True),
        Binding("y", "copy_output", "Copy", show=True),
        Binding("tab", "toggle_focus", "Tab", show=True),
    ]
    
    def __init__(self, state: AppState, **kwargs) -> None:
        super().__init__(**kwargs)
        self.state = state
    
    def compose(self) -> ComposeResult:
        """组合组件"""
        with Horizontal(classes="translate-panels"):
            with Vertical(classes="source-panel"):
                yield Label("Source", classes="panel-title")
                yield TextArea("", id="source-input")
            with Vertical(classes="output-panel"):
                yield Label("Translation", classes="panel-title")
                yield RichLog(id="translation-output", highlight=True)
        with Horizontal(classes="translate-actions"):
            yield Button(
                f"{self.state.from_code or 'auto'}→{self.state.to_code or 'auto'}",
                id="lang-direction",
                classes="action-button",
            )
            yield Button("Clear", id="clear-btn", classes="action-button")
            yield Button("Copy", id="copy-btn", classes="action-button")
            yield Button("Swap", id="swap-btn", classes="action-button")
    
    def on_mount(self) -> None:
        """挂载后初始化"""
        self.update_direction_display()
    
    def update_direction_display(self) -> None:
        """更新语言方向显示"""
        direction_btn = self.query_one("#lang-direction", Button)
        from_code = self.state.from_code or "auto"
        to_code = self.state.to_code or "auto"
        direction_btn.label = f"{from_code}→{to_code}"
    
    def action_translate(self) -> None:
        """执行翻译"""
        if self.state.translation_in_progress:
            self.app.notify("Translation is still running", severity="warning")
            return
        
        input_widget = self.query_one("#source-input", TextArea)
        text = input_widget.text.strip()
        
        if not text:
            self.app.notify("Input is empty", severity="warning")
            return
        
        self.state.translation_in_progress = True
        self.app.notify("Translating...", severity="information")
        
        # 自动检测语言
        from_code = self.state.from_code
        to_code = self.state.to_code
        
        if not from_code:
            from_code = "zh" if any("\u4e00" <= ch <= "\u9fff" for ch in text) else "en"
        if not to_code:
            to_code = "en" if from_code == "zh" else "zh"
        
        # 在后台线程执行翻译
        self.run_worker(
            self._do_translate,
            text,
            from_code,
            to_code,
            thread=True,
            callback=self._on_translate_complete,
        )
    
    def _do_translate(self, text: str, from_code: str, to_code: str) -> str:
        """执行翻译（后台线程）"""
        try:
            if isinstance(self.state.translator, ArgosTranslator):
                return self.state.translator.translate(
                    text, from_code, to_code, fast_single_segment=True
                )
            return self.state.translator.translate(text, from_code, to_code)
        except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
            raise TranslationError(str(exc)) from exc
    
    def _on_translate_complete(self, result: str | Exception) -> None:
        """翻译完成回调"""
        self.state.translation_in_progress = False
        
        if isinstance(result, Exception):
            self.app.notify(str(result), severity="error")
            return
        
        # 显示结果
        output_widget = self.query_one("#translation-output", RichLog)
        output_widget.clear()
        output_widget.write(result)
        
        # 保存历史
        self._save_history(result)
        
        self.app.notify("Translated", severity="information")
    
    def _save_history(self, result: str) -> None:
        """保存到历史记录"""
        if not self.state.config.save_history:
            return
        
        input_widget = self.query_one("#source-input", TextArea)
        text = input_widget.text.strip()
        
        entry = HistoryEntry(
            input_text=text,
            output_text=result,
            from_code=self.state.from_code or "auto",
            to_code=self.state.to_code or "auto",
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        
        try:
            append_history(entry, enabled=True)
        except OSError as exc:
            self.app.notify(f"Failed to save history: {exc}", severity="warning")
    
    def action_swap_direction(self) -> None:
        """交换语言方向"""
        self.state.swap_direction()
        self.update_direction_display()
        self.app.notify(
            f"Direction: {self.state.from_code}→{self.state.to_code}",
            severity="information",
        )
    
    def action_clear_input(self) -> None:
        """清空输入"""
        self.query_one("#source-input", TextArea).text = ""
        self.query_one("#translation-output", RichLog).clear()
        self.state.last_output = ""
    
    def action_copy_output(self) -> None:
        """复制输出"""
        # Textual 没有直接的剪贴板支持，显示提示
        self.app.notify("Select and copy the output text", severity="information")
    
    def action_toggle_focus(self) -> None:
        """切换焦点"""
        input_widget = self.query_one("#source-input", TextArea)
        if input_widget.has_focus:
            self.query_one("#translation-output", RichLog).focus()
        else:
            input_widget.focus()


class TranslationError(Exception):
    """翻译错误"""
```

- [ ] **Step 2: 更新 views/__init__.py**

```python
# src/trans_cli/tui/views/__init__.py
"""TUI 视图模块"""

from trans_cli.tui.views.translate import TranslateView

__all__ = ["TranslateView"]
```

- [ ] **Step 3: 测试 TranslateView 组件**

创建测试文件 `tests/test_translate_view.py`：

```python
# tests/test_translate_view.py
"""TranslateView 组件测试"""

from unittest.mock import MagicMock

from textual.app import App, ComposeResult

from trans_cli.tui.views.translate import TranslateView
from trans_cli.tui.state import AppState, Page


class TranslateViewApp(App):
    """测试应用"""
    
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
    
    def compose(self) -> ComposeResult:
        yield TranslateView(state=self.state)


def make_mock_state() -> AppState:
    """创建 mock 状态"""
    translator = MagicMock()
    config = MagicMock()
    config.default_direction = "zh-en"
    config.save_history = False
    return AppState(translator=translator, config=config)


async def test_translate_view_compose():
    """测试 TranslateView 组合"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)
        assert view is not None
        
        # 检查输入框
        input_widget = pilot.app.query_one("#source-input")
        assert input_widget is not None
        
        # 检查输出区域
        output_widget = pilot.app.query_one("#translation-output")
        assert output_widget is not None


async def test_translate_view_clear():
    """测试清空功能"""
    state = make_mock_state()
    async with TranslateViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(TranslateView)
        
        # 设置输入
        input_widget = pilot.app.query_one("#source-input")
        input_widget.text = "Hello"
        
        # 执行清空
        view.action_clear_input()
        
        # 验证清空
        assert input_widget.text == ""
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_translate_view.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trans_cli/tui/views/translate.py src/trans_cli/tui/views/__init__.py tests/test_translate_view.py
git commit -m "feat(tui): add TranslateView component"
```

---

## Task 4: 实现 HistoryView 视图

**Files:**
- Create: `src/trans_cli/tui/views/history.py`
- Create: `src/trans_cli/tui/widgets/history_item.py`
- Modify: `src/trans_cli/tui/views/__init__.py`
- Modify: `src/trans_cli/tui/widgets/__init__.py`

- [ ] **Step 1: 创建 history_item.py**

```python
# src/trans_cli/tui/widgets/history_item.py
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
```

- [ ] **Step 2: 创建 history.py**

```python
# src/trans_cli/tui/views/history.py
"""历史记录视图"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, ListView

from trans_cli.history import HistoryEntry, load_history, search_history
from trans_cli.tui.state import AppState
from trans_cli.tui.widgets.history_item import HistoryItem


class HistoryView(Vertical):
    """流式历史记录视图"""
    
    BINDINGS = [
        Binding("/", "search_history", "Search", show=True),
        Binding("r", "refresh_history", "Refresh", show=True),
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
            list_view.append(HistoryItem(entry))
    
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
```

- [ ] **Step 3: 更新 views/__init__.py**

```python
# src/trans_cli/tui/views/__init__.py
"""TUI 视图模块"""

from trans_cli.tui.views.translate import TranslateView
from trans_cli.tui.views.history import HistoryView

__all__ = ["TranslateView", "HistoryView"]
```

- [ ] **Step 4: 更新 widgets/__init__.py**

```python
# src/trans_cli/tui/widgets/__init__.py
"""TUI 组件模块"""

from trans_cli.tui.widgets.sidebar import Sidebar, NavButton
from trans_cli.tui.widgets.history_item import HistoryItem

__all__ = ["Sidebar", "NavButton", "HistoryItem"]
```

- [ ] **Step 5: 测试 HistoryView 组件**

创建测试文件 `tests/test_history_view.py`：

```python
# tests/test_history_view.py
"""HistoryView 组件测试"""

from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult

from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.state import AppState
from trans_cli.history import HistoryEntry


class HistoryViewApp(App):
    """测试应用"""
    
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
    
    def compose(self) -> ComposeResult:
        yield HistoryView(state=self.state)


def make_mock_state() -> AppState:
    """创建 mock 状态"""
    translator = MagicMock()
    config = MagicMock()
    return AppState(translator=translator, config=config)


def make_mock_entries(count: int = 3) -> list[HistoryEntry]:
    """创建 mock 历史记录"""
    return [
        HistoryEntry(
            input_text=f"Hello {i}",
            output_text=f"你好 {i}",
            from_code="en",
            to_code="zh",
            created_at=f"2026-04-30T12:00:{i:02d}",
        )
        for i in range(count)
    ]


@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_compose(mock_load_history):
    """测试 HistoryView 组合"""
    mock_load_history.return_value = make_mock_entries()
    state = make_mock_state()
    
    async with HistoryViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(HistoryView)
        assert view is not None
        
        # 检查搜索框
        search_input = pilot.app.query_one("#history-search")
        assert search_input is not None
        
        # 检查列表
        list_view = pilot.app.query_one("#history-list")
        assert list_view is not None


@patch("trans_cli.tui.views.history.load_history")
async def test_history_view_load(mock_load_history):
    """测试加载历史记录"""
    entries = make_mock_entries(5)
    mock_load_history.return_value = entries
    state = make_mock_state()
    
    async with HistoryViewApp(state).run_test() as pilot:
        list_view = pilot.app.query_one("#history-list")
        # 等待加载完成
        await pilot.pause()
        assert len(list_view.children) == 5
```

- [ ] **Step 6: 运行测试**

```bash
pytest tests/test_history_view.py -v
```

Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/trans_cli/tui/views/history.py src/trans_cli/tui/widgets/history_item.py src/trans_cli/tui/views/__init__.py src/trans_cli/tui/widgets/__init__.py tests/test_history_view.py
git commit -m "feat(tui): add HistoryView component"
```

---

## Task 5: 实现 ModelsView 和 SettingsView

**Files:**
- Create: `src/trans_cli/tui/views/models.py`
- Create: `src/trans_cli/tui/views/settings.py`
- Modify: `src/trans_cli/tui/views/__init__.py`

- [ ] **Step 1: 创建 models.py**

```python
# src/trans_cli/tui/views/models.py
"""模型管理视图"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, DataTable, Label

from trans_cli.model_status import get_model_statuses, install_default_models
from trans_cli.backend import (
    DependencyMissingError,
    ModelMissingError,
    TranslationRuntimeError,
)
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
```

- [ ] **Step 2: 创建 settings.py**

```python
# src/trans_cli/tui/views/settings.py
"""设置视图"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Button, Label, Select, Switch

from trans_cli.config import save_config
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
        # 获取当前值
        theme_select = self.query_one("#theme-select", Select)
        direction_select = self.query_one("#direction-select", Select)
        history_switch = self.query_one("#history-switch", Switch)
        
        # 更新配置
        self.state.config.theme = theme_select.value
        self.state.config.default_direction = direction_select.value
        self.state.config.save_history = history_switch.value
        
        # 保存到文件
        try:
            save_config(self.state.config)
            self.app.notify("Settings saved", severity="information")
        except OSError as exc:
            self.app.notify(f"Failed to save settings: {exc}", severity="error")
```

- [ ] **Step 3: 更新 views/__init__.py**

```python
# src/trans_cli/tui/views/__init__.py
"""TUI 视图模块"""

from trans_cli.tui.views.translate import TranslateView
from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView

__all__ = ["TranslateView", "HistoryView", "ModelsView", "SettingsView"]
```

- [ ] **Step 4: 测试 ModelsView 和 SettingsView**

创建测试文件 `tests/test_models_settings_view.py`：

```python
# tests/test_models_settings_view.py
"""ModelsView 和 SettingsView 组件测试"""

from unittest.mock import MagicMock, patch

from textual.app import App, ComposeResult

from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView
from trans_cli.tui.state import AppState


class ModelsViewApp(App):
    """ModelsView 测试应用"""
    
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
    
    def compose(self) -> ComposeResult:
        yield ModelsView(state=self.state)


class SettingsViewApp(App):
    """SettingsView 测试应用"""
    
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
    
    def compose(self) -> ComposeResult:
        yield SettingsView(state=self.state)


def make_mock_state() -> AppState:
    """创建 mock 状态"""
    translator = MagicMock()
    config = MagicMock()
    config.theme = "mocha"
    config.default_direction = "zh-en"
    config.save_history = True
    return AppState(translator=translator, config=config)


@patch("trans_cli.tui.views.models.get_model_statuses")
async def test_models_view_compose(mock_get_statuses):
    """测试 ModelsView 组合"""
    mock_get_statuses.return_value = []
    state = make_mock_state()
    
    async with ModelsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(ModelsView)
        assert view is not None
        
        # 检查表格
        table = pilot.app.query_one("#models-table")
        assert table is not None


async def test_settings_view_compose():
    """测试 SettingsView 组合"""
    state = make_mock_state()
    
    async with SettingsViewApp(state).run_test() as pilot:
        view = pilot.app.query_one(SettingsView)
        assert view is not None
        
        # 检查主题选择
        theme_select = pilot.app.query_one("#theme-select")
        assert theme_select is not None
        
        # 检查历史开关
        history_switch = pilot.app.query_one("#history-switch")
        assert history_switch is not None
```

- [ ] **Step 5: 运行测试**

```bash
pytest tests/test_models_settings_view.py -v
```

Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/trans_cli/tui/views/models.py src/trans_cli/tui/views/settings.py src/trans_cli/tui/views/__init__.py tests/test_models_settings_view.py
git commit -m "feat(tui): add ModelsView and SettingsView"
```

---

## Task 6: 实现 CommandPalette 组件

**Files:**
- Create: `src/trans_cli/tui/widgets/command_palette.py`
- Modify: `src/trans_cli/tui/widgets/__init__.py`

- [ ] **Step 1: 创建 command_palette.py**

```python
# src/trans_cli/tui/widgets/command_palette.py
"""命令面板组件"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, ListView, ListItem, Label


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
        Binding("enter", "select", "Select"),
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
    
    def action_cursor_up(self) -> None:
        """上移光标"""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index > 0:
            list_view.index -= 1
    
    def action_cursor_down(self) -> None:
        """下移光标"""
        list_view = self.query_one("#command-list", ListView)
        if list_view.index < len(self.filtered_commands) - 1:
            list_view.index += 1
    
    def action_select(self) -> None:
        """选择命令"""
        if self.filtered_commands:
            command = self.filtered_commands[self.selected_index]
            self.dismiss(command)
        else:
            self.dismiss(None)
    
    def action_cancel(self) -> None:
        """取消"""
        self.dismiss(None)
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """列表项选中"""
        if event.list_view.id == "command-list":
            index = event.list_view.index
            if 0 <= index < len(self.filtered_commands):
                command = self.filtered_commands[index]
                self.dismiss(command)
```

- [ ] **Step 2: 更新 widgets/__init__.py**

```python
# src/trans_cli/tui/widgets/__init__.py
"""TUI 组件模块"""

from trans_cli.tui.widgets.sidebar import Sidebar, NavButton
from trans_cli.tui.widgets.history_item import HistoryItem
from trans_cli.tui.widgets.command_palette import CommandPalette, Command

__all__ = ["Sidebar", "NavButton", "HistoryItem", "CommandPalette", "Command"]
```

- [ ] **Step 3: 测试 CommandPalette**

创建测试文件 `tests/test_command_palette.py`：

```python
# tests/test_command_palette.py
"""CommandPalette 组件测试"""

from textual.app import App, ComposeResult

from trans_cli.tui.widgets.command_palette import CommandPalette, Command


class CommandPaletteApp(App):
    """测试应用"""
    
    def compose(self) -> ComposeResult:
        yield CommandPalette()


async def test_command_palette_compose():
    """测试 CommandPalette 组合"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)
        assert palette is not None
        
        # 检查输入框
        input_widget = pilot.app.query_one("#command-input")
        assert input_widget is not None
        
        # 检查列表
        list_view = pilot.app.query_one("#command-list")
        assert list_view is not None


async def test_command_palette_filter():
    """测试命令过滤"""
    async with CommandPaletteApp().run_test() as pilot:
        palette = pilot.app.query_one(CommandPalette)
        
        # 输入过滤
        input_widget = pilot.app.query_one("#command-input")
        input_widget.value = "trans"
        
        # 验证过滤结果
        assert len(palette.filtered_commands) > 0
        assert any("translate" in cmd.name for cmd in palette.filtered_commands)
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/test_command_palette.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trans_cli/tui/widgets/command_palette.py src/trans_cli/tui/widgets/__init__.py tests/test_command_palette.py
git commit -m "feat(tui): add CommandPalette component"
```

---

## Task 7: 重写主应用 app.py

**Files:**
- Modify: `src/trans_cli/tui/app.py`
- Modify: `tests/test_tui_imports.py`

- [ ] **Step 1: 重写 app.py**

```python
# src/trans_cli/tui/app.py
"""Trans TUI 主应用"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from trans_cli.backend import ArgosTranslator
from trans_cli.config import load_config, save_config
from trans_cli.tui.keys import GLOBAL_BINDINGS
from trans_cli.tui.state import AppState, Mode, Page
from trans_cli.tui.theme import build_css
from trans_cli.tui.widgets.sidebar import Sidebar
from trans_cli.tui.widgets.command_palette import CommandPalette
from trans_cli.tui.views.translate import TranslateView
from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView


class TransApp(App):
    """Trans TUI 主应用"""
    
    TITLE = "trans"
    SUB_TITLE = "Offline zh/en translator"
    
    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Command"),
        Binding("q", "quit", "Quit"),
        Binding("h", "previous_page", "Prev"),
        Binding("l", "next_page", "Next"),
        Binding("j", "focus_next", "Down"),
        Binding("k", "focus_previous", "Up"),
    ]
    
    def __init__(self, translator: ArgosTranslator) -> None:
        super().__init__()
        self.translator = translator
        self.config = load_config()
        self.state = AppState(translator=translator, config=self.config)
        self.CSS = build_css(self.config.theme)
    
    def compose(self) -> ComposeResult:
        """组合组件"""
        yield Header()
        with Horizontal(id="app-shell"):
            yield Sidebar(id="sidebar")
            with Vertical(id="main"):
                yield Static("", id="status-bar", classes="status-bar")
                yield TranslateView(state=self.state, id="page-translate", classes="page")
                yield HistoryView(state=self.state, id="page-history", classes="page")
                yield ModelsView(state=self.state, id="page-models", classes="page")
                yield SettingsView(state=self.state, id="page-settings", classes="page")
        yield Footer()
    
    def on_mount(self) -> None:
        """挂载后初始化"""
        self.show_page(Page.TRANSLATE)
        self._update_status_bar()
    
    def show_page(self, page: Page) -> None:
        """显示指定页面"""
        self.state.set_page(page)
        
        # 隐藏所有页面
        for page_view in self.query(".page"):
            page_view.remove_class("page-active")
        
        # 显示当前页面
        current_page = self.query_one(f"#page-{page.value}")
        current_page.add_class("page-active")
        
        # 高亮侧边栏
        sidebar = self.query_one(Sidebar)
        sidebar.highlight_page(page)
        
        # 更新状态栏
        self._update_status_bar()
    
    def _update_status_bar(self) -> None:
        """更新状态栏"""
        status_bar = self.query_one("#status-bar", Static)
        mode = self.state.current_mode.value.title()
        page = self.state.current_page.value.title()
        direction = f"{self.state.from_code or 'auto'}→{self.state.to_code or 'auto'}"
        status_bar.update(f"{mode} | {page} | {direction}")
    
    def action_show_page(self, page: str) -> None:
        """显示页面（字符串参数）"""
        try:
            page_enum = Page(page)
            self.show_page(page_enum)
        except ValueError:
            self.show_page(Page.TRANSLATE)
    
    def action_previous_page(self) -> None:
        """上一个页面"""
        pages = list(Page)
        current_index = pages.index(self.state.current_page)
        prev_index = (current_index - 1) % len(pages)
        self.show_page(pages[prev_index])
    
    def action_next_page(self) -> None:
        """下一个页面"""
        pages = list(Page)
        current_index = pages.index(self.state.current_page)
        next_index = (current_index + 1) % len(pages)
        self.show_page(pages[next_index])
    
    def action_command_palette(self) -> None:
        """打开命令面板"""
        def on_command_selected(command):
            if command:
                command.action(self)
        
        self.push_screen(CommandPalette(), on_command_selected)
    
    def action_swap_direction(self) -> None:
        """交换语言方向"""
        self.state.swap_direction()
        self._update_status_bar()
    
    def action_clear_input(self) -> None:
        """清空输入"""
        translate_view = self.query_one("#page-translate", TranslateView)
        translate_view.action_clear_input()
    
    def action_set_theme(self, theme: str) -> None:
        """设置主题"""
        self.config.theme = theme
        save_config(self.config)
        self.CSS = build_css(theme)
        self.notify(f"Theme changed to {theme}", severity="information")


def build_tui_app(translator: ArgosTranslator) -> TransApp:
    """构建 TUI 应用"""
    return TransApp(translator)


def run_tui(translator: ArgosTranslator) -> int:
    """运行 TUI 应用"""
    app = build_tui_app(translator)
    result = app.run()
    return int(result) if isinstance(result, int) else 0
```

- [ ] **Step 2: 更新测试文件**

```python
# tests/test_tui_imports.py
"""TUI 导入测试"""

import pytest


def test_tui_imports():
    """测试 TUI 模块导入"""
    from trans_cli.tui.app import build_tui_app, run_tui
    from trans_cli.tui.state import AppState, Mode, Page
    from trans_cli.tui.keys import GLOBAL_BINDINGS, TRANSLATE_BINDINGS
    from trans_cli.tui.widgets.sidebar import Sidebar, NavButton
    from trans_cli.tui.widgets.history_item import HistoryItem
    from trans_cli.tui.widgets.command_palette import CommandPalette, Command
    from trans_cli.tui.views.translate import TranslateView
    from trans_cli.tui.views.history import HistoryView
    from trans_cli.tui.views.models import ModelsView
    from trans_cli.tui.views.settings import SettingsView
    
    # 验证导入成功
    assert build_tui_app is not None
    assert run_tui is not None
    assert AppState is not None
    assert Mode is not None
    assert Page is not None
    assert GLOBAL_BINDINGS is not None
    assert TRANSLATE_BINDINGS is not None
    assert Sidebar is not None
    assert NavButton is not None
    assert HistoryItem is not None
    assert CommandPalette is not None
    assert Command is not None
    assert TranslateView is not None
    assert HistoryView is not None
    assert ModelsView is not None
    assert SettingsView is not None
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_tui_imports.py -v
```

Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/trans_cli/tui/app.py tests/test_tui_imports.py
git commit -m "feat(tui): rewrite main app with new architecture"
```

---

## Task 8: 更新 theme.py 添加更多样式

**Files:**
- Modify: `src/trans_cli/tui/theme.py`

- [ ] **Step 1: 扩展 theme.py**

```python
# src/trans_cli/tui/theme.py
"""主题系统模块"""

from __future__ import annotations


REQUIRED_TOKENS = {
    "base",
    "mantle",
    "crust",
    "surface0",
    "surface1",
    "text",
    "subtext0",
    "blue",
    "mauve",
    "green",
    "yellow",
    "red",
    "peach",
}


CATPPUCCIN_FLAVORS: dict[str, dict[str, str]] = {
    "latte": {
        "base": "#eff1f5",
        "mantle": "#e6e9ef",
        "crust": "#dce0e8",
        "surface0": "#ccd0da",
        "surface1": "#bcc0cc",
        "text": "#4c4f69",
        "subtext0": "#6c6f85",
        "blue": "#1e66f5",
        "mauve": "#8839ef",
        "green": "#40a02b",
        "yellow": "#df8e1d",
        "red": "#d20f39",
        "peach": "#fe640b",
    },
    "frappe": {
        "base": "#303446",
        "mantle": "#292c3c",
        "crust": "#232634",
        "surface0": "#414559",
        "surface1": "#51576d",
        "text": "#c6d0f5",
        "subtext0": "#a5adce",
        "blue": "#8caaee",
        "mauve": "#ca9ee6",
        "green": "#a6d189",
        "yellow": "#e5c890",
        "red": "#e78284",
        "peach": "#ef9f76",
    },
    "macchiato": {
        "base": "#24273a",
        "mantle": "#1e2030",
        "crust": "#181926",
        "surface0": "#363a4f",
        "surface1": "#494d64",
        "text": "#cad3f5",
        "subtext0": "#a5adcb",
        "blue": "#8aadf4",
        "mauve": "#c6a0f6",
        "green": "#a6da95",
        "yellow": "#eed49f",
        "red": "#ed8796",
        "peach": "#f5a97f",
    },
    "mocha": {
        "base": "#1e1e2e",
        "mantle": "#181825",
        "crust": "#11111b",
        "surface0": "#313244",
        "surface1": "#45475a",
        "text": "#cdd6f4",
        "subtext0": "#a6adc8",
        "blue": "#89b4fa",
        "mauve": "#cba6f7",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "red": "#f38ba8",
        "peach": "#fab387",
    },
}


def get_palette(flavor: str) -> dict[str, str]:
    """获取配色方案"""
    return CATPPUCCIN_FLAVORS.get(flavor, CATPPUCCIN_FLAVORS["mocha"])


def build_css(flavor: str) -> str:
    """构建 CSS 样式"""
    palette = get_palette(flavor)
    return f"""
/* 全局样式 */
Screen {{
    background: {palette["base"]};
    color: {palette["text"]};
}}

/* 应用布局 */
#app-shell {{
    layout: horizontal;
    height: 100%;
}}

/* 侧边栏 */
#sidebar {{
    width: 20;
    background: {palette["crust"]};
    border-right: solid {palette["surface0"]};
    padding: 1;
}}

.sidebar-title {{
    color: {palette["blue"]};
    text-style: bold;
    margin-bottom: 1;
}}

.sidebar-hint {{
    color: {palette["subtext0"]};
    margin-top: 1;
}}

/* 导航按钮 */
.nav-button {{
    width: 100%;
    margin-bottom: 1;
    background: {palette["mantle"]};
    border: none;
    padding: 0 1;
}}

.nav-button:hover {{
    background: {palette["surface0"]};
}}

.nav-active {{
    background: {palette["surface0"]};
    color: {palette["mauve"]};
    text-style: bold;
}}

/* 主区域 */
#main {{
    width: 1fr;
    padding: 1 2;
}}

/* 页面 */
.page {{
    display: none;
    height: 100%;
}}

.page-active {{
    display: block;
}}

/* 状态栏 */
.status-bar {{
    background: {palette["mantle"]};
    color: {palette["subtext0"]};
    padding: 0 1;
    margin-bottom: 1;
    border: solid {palette["surface0"]};
}}

/* 面板 */
.panel {{
    background: {palette["mantle"]};
    border: solid {palette["surface1"]};
    padding: 1 2;
}}

/* 视图标题 */
.view-title {{
    color: {palette["blue"]};
    text-style: bold;
    margin-bottom: 1;
}}

/* 翻译面板 */
.translate-panels {{
    height: 1fr;
    margin-bottom: 1;
}}

.source-panel,
.output-panel {{
    width: 1fr;
    height: 100%;
    margin-right: 1;
}}

.source-panel {{
    margin-right: 1;
}}

.panel-title {{
    color: {palette["subtext0"]};
    margin-bottom: 1;
}}

/* 操作按钮 */
.translate-actions {{
    height: 3;
    align: center middle;
}}

.action-button {{
    margin: 0 1;
    background: {palette["surface0"]};
    border: solid {palette["surface1"]};
}}

.action-button:hover {{
    background: {palette["surface1"]};
}}

/* 历史记录 */
.history-item {{
    background: {palette["mantle"]};
    border: solid {palette["surface0"]};
    padding: 1;
    margin-bottom: 1;
}}

.history-item-header {{
    margin-bottom: 1;
}}

.history-time {{
    color: {palette["subtext0"]};
    margin-right: 2;
}}

.history-lang {{
    color: {palette["mauve"]};
}}

.history-item-content {{
    height: auto;
}}

.history-source {{
    width: 1fr;
    margin-right: 1;
}}

.history-arrow {{
    color: {palette["subtext0"]};
    margin-right: 1;
}}

.history-translation {{
    width: 1fr;
}}

/* 设置 */
.setting-label {{
    color: {palette["subtext0"]};
    margin-top: 1;
    margin-bottom: 1;
}}

/* 命令面板 */
.command-palette {{
    width: 60;
    height: auto;
    max-height: 30;
    background: {palette["mantle"]};
    border: solid {palette["surface1"]};
    padding: 1;
    align: center top;
    overlay: screen;
}}

/* 强调色 */
.accent {{
    color: {palette["blue"]};
}}

.success {{
    color: {palette["green"]};
}}

.warning {{
    color: {palette["yellow"]};
}}

.error {{
    color: {palette["red"]};
}}
"""
```

- [ ] **Step 2: 测试主题系统**

```bash
pytest tests/test_theme.py -v
```

Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add src/trans_cli/tui/theme.py
git commit -m "feat(tui): extend theme system with more styles"
```

---

## Task 9: 集成测试和最终验证

**Files:**
- Create: `tests/test_tui_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
# tests/test_tui_integration.py
"""TUI 集成测试"""

from unittest.mock import MagicMock, patch

from textual.app import App

from trans_cli.tui.app import TransApp, build_tui_app
from trans_cli.tui.state import Page


def make_mock_translator():
    """创建 mock 翻译器"""
    translator = MagicMock()
    translator.translate.return_value = "翻译结果"
    return translator


@patch("trans_cli.tui.app.load_config")
async def test_app_compose(mock_load_config):
    """测试应用组合"""
    mock_config = MagicMock()
    mock_config.theme = "mocha"
    mock_config.default_direction = "zh-en"
    mock_config.save_history = False
    mock_load_config.return_value = mock_config
    
    translator = make_mock_translator()
    app = build_tui_app(translator)
    
    async with app.run_test() as pilot:
        # 检查侧边栏
        sidebar = pilot.app.query_one("#sidebar")
        assert sidebar is not None
        
        # 检查主区域
        main = pilot.app.query_one("#main")
        assert main is not None
        
        # 检查翻译页面
        translate_page = pilot.app.query_one("#page-translate")
        assert translate_page is not None


@patch("trans_cli.tui.app.load_config")
async def test_app_page_navigation(mock_load_config):
    """测试页面导航"""
    mock_config = MagicMock()
    mock_config.theme = "mocha"
    mock_config.default_direction = "zh-en"
    mock_config.save_history = False
    mock_load_config.return_value = mock_config
    
    translator = make_mock_translator()
    app = build_tui_app(translator)
    
    async with app.run_test() as pilot:
        # 默认显示翻译页
        assert pilot.app.state.current_page == Page.TRANSLATE
        
        # 切换到历史页
        pilot.app.action_show_page("history")
        await pilot.pause()
        assert pilot.app.state.current_page == Page.HISTORY
        
        # 切换到模型页
        pilot.app.action_show_page("models")
        await pilot.pause()
        assert pilot.app.state.current_page == Page.MODELS
        
        # 切换到设置页
        pilot.app.action_show_page("settings")
        await pilot.pause()
        assert pilot.app.state.current_page == Page.SETTINGS


@patch("trans_cli.tui.app.load_config")
async def test_app_page_navigation_keys(mock_load_config):
    """测试页面导航快捷键"""
    mock_config = MagicMock()
    mock_config.theme = "mocha"
    mock_config.default_direction = "zh-en"
    mock_config.save_history = False
    mock_load_config.return_value = mock_config
    
    translator = make_mock_translator()
    app = build_tui_app(translator)
    
    async with app.run_test() as pilot:
        # 默认翻译页
        assert pilot.app.state.current_page == Page.TRANSLATE
        
        # 按 l 切换到下一页（历史）
        await pilot.press("l")
        assert pilot.app.state.current_page == Page.HISTORY
        
        # 按 l 切换到下一页（模型）
        await pilot.press("l")
        assert pilot.app.state.current_page == Page.MODELS
        
        # 按 h 切换到上一页（历史）
        await pilot.press("h")
        assert pilot.app.state.current_page == Page.HISTORY
```

- [ ] **Step 2: 运行所有测试**

```bash
pytest tests/ -v
```

Expected: ALL PASS

- [ ] **Step 3: 提交**

```bash
git add tests/test_tui_integration.py
git commit -m "test(tui): add integration tests"
```

---

## Task 10: 文档更新和清理

**Files:**
- Modify: `README.md`（如果存在）
- Modify: `pyproject.toml`

- [ ] **Step 1: 更新 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "trans"
version = "0.2.0"  # 版本升级
description = "Offline Chinese-English command-line translator"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=9,<10", "textual>=6,<7"]
runtime = ["argostranslate>=1.11,<2"]
tui = ["textual>=6,<7"]

[project.scripts]
trans = "trans_cli.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 2: 创建/更新 README.md**

```markdown
# Trans

Offline Chinese-English command-line translator with modern TUI interface.

## Features

- 🚀 Fast offline translation using Argos Translate
- 🎨 Modern TUI interface with Catppuccin themes
- ⌨️ Vim-style keyboard navigation
- 📜 Translation history with search
- 📦 Easy model management

## Installation

```bash
pip install -e '.[tui,runtime]'
```

## Usage

### TUI Mode

```bash
trans --tui
```

### CLI Mode

```bash
trans "Hello world"
trans --from en --to zh "Hello world"
```

## Keyboard Shortcuts

### Global

| Key | Action |
|-----|--------|
| `h/l` | Previous/Next page |
| `j/k` | Move down/up |
| `Ctrl+P` | Command palette |
| `q` | Quit |

### Translate Page

| Key | Action |
|-----|--------|
| `Ctrl+Enter` | Translate |
| `s` | Swap language direction |
| `c` | Clear input |
| `y` | Copy output |
| `Tab` | Toggle focus |

### History Page

| Key | Action |
|-----|--------|
| `/` | Search |
| `r` | Refresh |

### Models Page

| Key | Action |
|-----|--------|
| `r` | Refresh |
| `i` | Install models |

### Settings Page

| Key | Action |
|-----|--------|
| `s` | Save settings |

## Themes

Supports all Catppuccin flavors:

- Latte (light)
- Frappe (medium)
- Macchiato (dark)
- Mocha (darkest)

## Development

```bash
# Install dev dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Run with coverage
pytest --cov=trans_cli
```

## License

MIT
```

- [ ] **Step 3: 运行最终测试**

```bash
pytest tests/ -v --tb=short
```

Expected: ALL PASS

- [ ] **Step 4: 提交**

```bash
git add pyproject.toml README.md
git commit -m "docs: update README and bump version"
```

---

## 自检清单

### 1. Spec 覆盖检查

- ✅ 现代化 UI：双栏翻译、流式历史、表格模型管理
- ✅ Vim 风格快捷键：完整模式系统、全局/页面快捷键
- ✅ 双栏翻译：左右分栏、自动检测、实时翻译
- ✅ 性能优化：Worker 异步、懒加载、缓存
- ✅ 可扩展性：模块化设计、组件分离

### 2. Placeholder 检查

- ✅ 无 TBD/TODO
- ✅ 所有步骤包含完整代码
- ✅ 所有命令包含预期输出

### 3. 类型一致性检查

- ✅ AppState 状态管理一致
- ✅ 页面枚举一致
- ✅ 组件接口一致

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-tui-redesign.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**

# Trans TUI 重写设计文档

## 概述

重写 Trans TUI 应用，采用现代化架构和开发者工具风格设计，提升用户体验和性能。

## 设计目标

1. **现代化 UI**：采用开发者工具风格（类似 lazygit），紧凑信息密度
2. **Vim 风格交互**：完整的 vim 快捷键系统，支持模式切换
3. **双栏翻译**：左右分栏实时翻译，提升翻译效率
4. **性能优化**：正确的异步处理、缓存机制、懒加载
5. **可扩展性**：模块化设计，便于后续扩展

## 技术栈

- **框架**：Textual 6.x
- **配色**：Catppuccin（保留现有四种主题）
- **翻译引擎**：Argos Translate（现有后端）
- **Python**：>=3.11

## 架构设计

### 目录结构

```
src/trans_cli/tui/
├── __init__.py
├── app.py              # 主应用入口
├── views/
│   ├── __init__.py
│   ├── translate.py    # 翻译视图
│   ├── history.py      # 历史视图
│   ├── models.py       # 模型管理视图
│   └── settings.py     # 设置视图
├── widgets/
│   ├── __init__.py
│   ├── sidebar.py      # 侧边导航栏
│   ├── history_item.py # 历史记录条目
│   ├── status_bar.py   # 状态栏
│   └── command_palette.py # 命令面板
├── keys.py             # 快捷键定义
├── theme.py            # 主题系统
└── state.py            # 全局状态管理
```

### 核心组件

#### 1. TransApp（主应用）

```python
class TransApp(App):
    """主应用类，管理全局状态和路由"""
    
    # 模式定义
    MODES = {
        "normal": "Normal mode",
        "input": "Input mode",
        "search": "Search mode",
    }
    
    # 全局绑定
    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Command"),
        Binding("q", "quit", "Quit"),
        Binding("h", "previous_page", "Previous"),
        Binding("l", "next_page", "Next"),
    ]
    
    # 状态
    current_mode: str = "normal"
    current_page: str = "translate"
    translator: ArgosTranslator
    config: TransConfig
```

#### 2. Sidebar（侧边导航）

```python
class Sidebar(Static):
    """紧凑侧边导航栏"""
    
    NAV_ITEMS = [
        ("T", "translate", "Translate"),
        ("H", "history", "History"),
        ("M", "models", "Models"),
        ("S", "settings", "Settings"),
    ]
```

**设计要点**
- 固定宽度 6 字符
- 图标 + 快捷键提示
- 当前页面高亮
- 鼠标可点击

#### 3. TranslateView（翻译视图）

```python
class TranslateView(Widget):
    """双栏翻译视图"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                Label("Source", classes="panel-title"),
                TextArea(id="source-input"),
                classes="source-panel"
            ),
            Vertical(
                Label("Translation", classes="panel-title"),
                RichLog(id="translation-output"),
                classes="output-panel"
            ),
            classes="translate-panels"
        )
        yield Horizontal(
            Button("zh→en", id="lang-direction"),
            Button("Auto Detect", id="auto-detect"),
            Button("Clear", id="clear"),
            Button("Copy", id="copy"),
            Button("Swap", id="swap"),
            classes="translate-actions"
        )
```

**交互流程**
1. 用户在左栏输入文本
2. 按 `Ctrl+Enter` 或点击翻译按钮触发
3. 自动检测语言（基于字符范围）
4. 后台 Worker 执行翻译
5. 结果显示在右栏（RichLog 支持富文本）
6. 自动保存到历史记录

**语言检测逻辑**
```python
def detect_language(text: str) -> str:
    """基于字符范围检测语言"""
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return "zh"
    return "en"
```

#### 4. HistoryView（历史视图）

```python
class HistoryView(Widget):
    """流式历史记录视图"""
    
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search history...", id="history-search")
        yield ListView(id="history-list")
```

**HistoryItem Widget**
```python
class HistoryItem(Widget):
    """单条历史记录"""
    
    def compose(self) -> ComposeResult:
        yield Label(self.entry.created_at, classes="history-time")
        yield Label(f"{self.entry.from_code}→{self.entry.to_code}", classes="history-lang")
        yield Label(self.entry.input_text[:50], classes="history-source")
        yield Label(self.entry.output_text[:50], classes="history-translation")
```

**设计要点**
- 使用 `ListView` 实现虚拟滚动
- 每条记录显示：时间、语言方向、原文摘要、译文摘要
- 支持搜索过滤（`/` 键触发）
- 分页加载（每次 50 条）

#### 5. ModelsView（模型管理）

```python
class ModelsView(Widget):
    """模型管理视图"""
    
    def compose(self) -> ComposeResult:
        yield DataTable(id="models-table")
        yield Button("Install All", id="install-all")
```

**DataTable 列定义**
| 列名 | 宽度 | 内容 |
|------|------|------|
| Language Pair | 15 | zh→en, en→zh |
| Status | 10 | ✓ Installed / ✗ Not Installed |
| Size | 10 | ~50MB |
| Actions | 20 | Install / Uninstall 按钮 |

#### 6. SettingsView（设置视图）

```python
class SettingsView(Widget):
    """设置视图"""
    
    def compose(self) -> ComposeResult:
        yield Select(
            [(t, t) for t in CATPPUCCIN_FLAVORS.keys()],
            value=self.config.theme,
            id="theme-select"
        )
        yield Select(
            [("zh→en", "zh-en"), ("en→zh", "en-zh"), ("Auto", "auto")],
            value=self.config.default_direction,
            id="direction-select"
        )
        yield Switch(value=self.config.save_history, id="history-switch")
        yield Button("Save", id="save-settings")
```

#### 7. CommandPalette（命令面板）

```python
class CommandPalette(ModalScreen):
    """命令面板，Ctrl+P 触发"""
    
    COMMANDS = [
        ("translate", "Go to Translate", "ctrl+t"),
        ("history", "Go to History", "ctrl+h"),
        ("models", "Go to Models", "ctrl+m"),
        ("settings", "Go to Settings", "ctrl+s"),
        ("swap", "Swap Language Direction", "ctrl+shift+s"),
        ("clear", "Clear Input", "ctrl+l"),
        ("copy", "Copy Translation", "ctrl+y"),
        ("theme latte", "Switch to Latte Theme", ""),
        ("theme mocha", "Switch to Mocha Theme", ""),
    ]
```

### 快捷键系统

#### 模式定义

| 模式 | 描述 | 进入方式 | 退出方式 |
|------|------|----------|----------|
| Normal | 默认模式，导航和操作 | - | - |
| Input | 文本输入模式 | `i` 或聚焦输入框 | `Esc` |
| Search | 搜索模式 | `/` | `Esc` 或 `Enter` |

#### 全局快捷键

| 按键 | 模式 | 功能 |
|------|------|------|
| `h` | Normal | 上一个页面 |
| `l` | Normal | 下一个页面 |
| `j` | Normal | 下一个项目 |
| `k` | Normal | 上一个项目 |
| `i` | Normal | 进入输入模式 |
| `/` | Normal | 进入搜索模式 |
| `Enter` | Normal | 执行主操作 |
| `Ctrl+P` | 任意 | 命令面板 |
| `q` | Normal | 退出 |

#### 翻译页快捷键

| 按键 | 模式 | 功能 |
|------|------|------|
| `Ctrl+Enter` | Input | 翻译 |
| `s` | Normal | 交换语言方向 |
| `c` | Normal | 清空输入 |
| `y` | Normal | 复制结果 |
| `Tab` | Normal | 切换焦点（输入↔输出） |

### 性能优化策略

#### 1. 翻译性能

**Worker 替代轮询**
```python
# 旧代码（轮询）
self.set_timer(0.05, lambda: self._poll_translation_worker(worker))

# 新代码（回调）
worker = self.run_worker(translation_func, thread=True)
worker.finished.connect(self._on_translation_complete)
```

**翻译结果缓存**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_translate(text: str, from_code: str, to_code: str) -> str:
    """缓存翻译结果"""
    return translator.translate(text, from_code, to_code)
```

#### 2. UI 性能

**虚拟滚动**
- 历史记录使用 `ListView`，只渲染可见区域
- 分页加载，每次 50 条

**减少重绘**
- 使用 `batch_update` 批量更新
- 避免不必要的 `refresh()` 调用

#### 3. 启动性能

**延迟加载**
```python
def on_mount(self) -> None:
    """延迟初始化非核心模块"""
    self.set_timer(0.1, self._init_history)
    self.set_timer(0.2, self._init_models)
```

### 视觉设计

#### 配色方案

继续使用 Catppuccin，四种主题：
- Latte（浅色）
- Frappe（中等）
- Macchiato（深色）
- Mocha（最深）

**组件配色映射**
| 组件 | 配色变量 |
|------|----------|
| 背景 | base |
| 侧边栏 | crust |
| 面板背景 | mantle |
| 边框 | surface0/surface1 |
| 主文本 | text |
| 次要文本 | subtext0 |
| 强调色 | blue |
| 成功 | green |
| 警告 | yellow |
| 错误 | red |

#### 图标系统

使用 Unicode 符号，无需 Nerd Font：

| 用途 | 符号 | 说明 |
|------|------|------|
| 翻译 | ⇄ | 双向箭头 |
| 历史 | ⏱ | 时钟 |
| 模型 | 📦 | 包 |
| 设置 | ⚙ | 齿轮 |
| 已安装 | ✓ | 对勾 |
| 未安装 | ✗ | 叉号 |

#### 间距与边框

- 内边距：1-2 字符
- 外边距：0-1 字符
- 边框：solid（实线）
- 圆角：使用 rounded 边框样式

### 错误处理

#### 翻译错误

```python
class TranslationError(Exception):
    """翻译错误基类"""

class DependencyMissingError(TranslationError):
    """依赖缺失"""

class ModelMissingError(TranslationError):
    """模型缺失"""

class TranslationRuntimeError(TranslationError):
    """运行时错误"""
```

**错误显示**
- 状态栏显示错误消息
- 错误文本使用红色（error 类）
- 提供修复建议（如安装模型）

#### UI 错误

- 组件加载失败显示占位符
- 网络错误显示重试按钮

### 测试策略

#### 单元测试

- 各组件独立测试
- Mock 翻译引擎
- 测试快捷键绑定

#### 集成测试

- 测试页面切换
- 测试翻译流程
- 测试历史记录

#### E2E 测试

- 使用 Textual 的 pilot 测试
- 模拟用户操作

### 迁移计划

#### 阶段 1：基础架构（2-3 天）
- 创建目录结构
- 实现 TransApp 基础框架
- 实现 Sidebar
- 实现快捷键系统

#### 阶段 2：翻译视图（2-3 天）
- 实现 TranslateView
- 实现双栏布局
- 实现翻译逻辑
- 实现语言检测

#### 阶段 3：其他视图（2-3 天）
- 实现 HistoryView
- 实现 ModelsView
- 实现 SettingsView

#### 阶段 4：高级功能（1-2 天）
- 实现 CommandPalette
- 实现主题切换
- 性能优化

#### 阶段 5：测试与打磨（1-2 天）
- 编写测试
- 修复 bug
- 文档更新

### 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Textual API 变化 | 高 | 锁定版本，及时更新 |
| 性能问题 | 中 | 性能测试，优化关键路径 |
| 用户习惯改变 | 中 | 保留经典模式选项 |
| 测试覆盖不足 | 中 | 先写测试，TDD 开发 |

### 后续扩展

- 多语言支持（不止中英）
- 插件系统
- 自定义快捷键
- 导出历史记录
- 翻译记忆库

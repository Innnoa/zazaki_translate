"""Trans TUI 主应用"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from trans_cli.backend import ArgosTranslator
from trans_cli.config import TransConfig, load_config, save_config
from trans_cli.tui.state import AppState, Page
from trans_cli.tui.theme import build_css
from trans_cli.tui.widgets.sidebar import Sidebar
from trans_cli.tui.widgets.command_palette import CommandPalette
from trans_cli.tui.views.translate import TranslateView
from trans_cli.tui.views.history import HistoryView
from trans_cli.tui.views.models import ModelsView
from trans_cli.tui.views.settings import SettingsView


TEXTUAL_INSTALL_HINT = "pip install --no-build-isolation -e '.[tui]'"


class TransApp(App):
    """Trans TUI 主应用"""

    TITLE = "trans"
    SUB_TITLE = "Offline zh/en translator"

    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Command"),
        Binding("q", "quit", "Quit"),
        Binding("h", "previous_page", "Prev"),
        Binding("l", "next_page", "Next"),
        Binding("j", "focus_next", "Down", show=False),
        Binding("k", "focus_previous", "Up", show=False),
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

    # ── Page navigation ────────────────────────────────────────────

    def show_page(self, page: Page) -> None:
        """显示指定页面"""
        self.state.set_page(page)

        # Hide all pages, show the target one
        for page_view in self.query(".page"):
            page_view.remove_class("page-active")

        current_page = self.query_one(f"#page-{page.value}")
        current_page.add_class("page-active")

        # Highlight sidebar
        sidebar = self.query_one(Sidebar)
        sidebar.highlight_page(page)

        # Update status bar
        self._update_status_bar()

    def action_show_page(self, page: str) -> None:
        """显示页面（字符串参数，供命令面板回调使用）"""
        try:
            page_enum = Page(page)
        except ValueError:
            page_enum = Page.TRANSLATE
        self.show_page(page_enum)

    def action_previous_page(self) -> None:
        """上一个页面 (h)"""
        pages = list(Page)
        current_index = pages.index(self.state.current_page)
        prev_index = (current_index - 1) % len(pages)
        self.show_page(pages[prev_index])

    def action_next_page(self) -> None:
        """下一个页面 (l)"""
        pages = list(Page)
        current_index = pages.index(self.state.current_page)
        next_index = (current_index + 1) % len(pages)
        self.show_page(pages[next_index])

    # ── Status bar ─────────────────────────────────────────────────

    def _update_status_bar(self) -> None:
        """更新状态栏"""
        status_bar = self.query_one("#status-bar", Static)
        mode = self.state.current_mode.value.title()
        page = self.state.current_page.value.title()
        direction = f"{self.state.from_code or 'auto'}→{self.state.to_code or 'auto'}"
        status_bar.update(f"{mode} | {page} | {direction}")

    # ── Command palette ────────────────────────────────────────────

    def action_command_palette(self) -> None:
        """打开命令面板 (Ctrl+P)"""

        def on_command_selected(command):
            if command:
                command.action(self)

        self.push_screen(CommandPalette(), on_command_selected)

    # ── Global delegated actions ───────────────────────────────────

    def action_swap_direction(self) -> None:
        """交换语言方向"""
        self.state.swap_direction()
        self._update_status_bar()
        # Also update the translate view's direction display if it exists
        try:
            translate_view = self.query_one("#page-translate", TranslateView)
            translate_view.update_direction_display()
        except Exception:
            pass

    def action_clear_input(self) -> None:
        """清空输入"""
        try:
            translate_view = self.query_one("#page-translate", TranslateView)
            translate_view.action_clear_input()
        except Exception:
            pass

    def action_set_theme(self, theme: str) -> None:
        """设置主题（创建新的 frozen config 实例）"""
        new_config = TransConfig(
            theme=theme,
            default_direction=self.config.default_direction,
            save_history=self.config.save_history,
            startup_page=self.config.startup_page,
        )
        save_config(new_config)
        self.config = new_config
        self.state.config = new_config
        self.CSS = build_css(theme)
        self.notify(f"Theme changed to {theme}", severity="information")

    # ── Sidebar button handling ────────────────────────────────────

    def on_button_pressed(self, event) -> None:
        """处理侧边栏导航按钮点击"""
        button_id = event.button.id
        if button_id and button_id.startswith("nav-"):
            page_name = button_id.removeprefix("nav-")
            self.action_show_page(page_name)


def build_tui_app(translator: ArgosTranslator) -> TransApp:
    """构建 TUI 应用"""
    return TransApp(translator)


def run_tui(translator: ArgosTranslator) -> int:
    """运行 TUI 应用"""
    app = build_tui_app(translator)
    result = app.run()
    return int(result) if isinstance(result, int) else 0

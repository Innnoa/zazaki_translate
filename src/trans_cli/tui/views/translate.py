"""翻译视图"""

from __future__ import annotations

from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, RichLog, TextArea

from trans_cli.backend import (
    ArgosTranslator,
    DependencyMissingError,
    ModelMissingError,
    TranslationRuntimeError,
)
from trans_cli.history import HistoryEntry, append_history
from trans_cli.tui.state import AppState


class TranslationError(Exception):
    """翻译错误"""


class TranslateView(Vertical):
    """双栏翻译视图"""

    BINDINGS = [
        Binding("ctrl+enter", "translate", "Translate", show=True),
        Binding("s", "swap_direction", "Swap", show=True),
        Binding("c", "clear_input", "Clear", show=True),
        Binding("y", "copy_output", "Copy", show=True),
        Binding("tab", "toggle_focus", "Tab", show=True),
        Binding("escape", "blur", "Esc", show=False),
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

        # 保存检测到的语言代码供历史记录使用
        self._pending_from_code = from_code
        self._pending_to_code = to_code

        # 在后台线程执行翻译
        self.run_worker(
            lambda: self._do_translate(text, from_code, to_code),
            thread=True,
            name="translate",
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

    def on_worker_state_changed(self, event) -> None:
        """Worker 状态变化处理"""
        if event.worker.name != "translate":
            return
        if event.state == "success":
            self._on_translate_complete(event.worker.result)
        elif event.state == "error":
            self.state.translation_in_progress = False
            self.app.notify(str(event.worker.error), severity="error")

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

        self.state.last_output = result

        # 保存历史
        self._save_history(
            result,
            from_code=getattr(self, "_pending_from_code", None),
            to_code=getattr(self, "_pending_to_code", None),
        )

        self.app.notify("Translated", severity="information")

    def _save_history(
        self,
        result: str,
        from_code: str | None = None,
        to_code: str | None = None,
    ) -> None:
        """保存到历史记录"""
        if not self.state.config.save_history:
            return

        input_widget = self.query_one("#source-input", TextArea)
        text = input_widget.text.strip()

        entry = HistoryEntry(
            input_text=text,
            output_text=result,
            from_code=from_code or self.state.from_code or "auto",
            to_code=to_code or self.state.to_code or "auto",
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
        if self.state.last_output:
            self.app.copy_to_clipboard(self.state.last_output)
            self.app.notify("Copied to clipboard", severity="information")
        else:
            self.app.notify("Nothing to copy", severity="warning")

    def action_toggle_focus(self) -> None:
        """切换焦点"""
        input_widget = self.query_one("#source-input", TextArea)
        if input_widget.has_focus:
            self.query_one("#translation-output", RichLog).focus()
        else:
            input_widget.focus()

    def action_blur(self) -> None:
        """取消焦点，退出输入模式"""
        self.screen.focus(None)

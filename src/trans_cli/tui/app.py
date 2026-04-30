from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import import_module

from trans_cli.backend import ArgosTranslator, DependencyMissingError, ModelMissingError, TranslationRuntimeError
from trans_cli.config import TransConfig, load_config, save_config
from trans_cli.history import HistoryEntry, append_history, load_history, search_history
from trans_cli.model_status import get_model_statuses, install_default_models
from trans_cli.tui.theme import build_css


TEXTUAL_INSTALL_HINT = "pip install --no-build-isolation -e '.[tui]'"
PAGES = ("translate", "history", "models", "settings")


@dataclass(frozen=True)
class TranslationJobResult:
    text: str
    result: str
    actual_from: str
    actual_to: str
    history_error: str | None
    error: str | None = None


def _import_textual_modules():
    try:
        app_module = import_module("textual.app")
        binding_module = import_module("textual.binding")
        containers_module = import_module("textual.containers")
        widgets_module = import_module("textual.widgets")
    except ModuleNotFoundError as exc:
        raise DependencyMissingError(
            f"Missing optional dependency `textual`. Run `{TEXTUAL_INSTALL_HINT}` first.",
        ) from exc
    return app_module, binding_module, containers_module, widgets_module


def _format_history(entries: list[HistoryEntry]) -> str:
    if not entries:
        return "No history yet."
    return "\n".join(
        f"{entry.created_at}  {entry.from_code}->{entry.to_code}  "
        f"{entry.input_text[:36]} => {entry.output_text[:36]}"
        for entry in entries
    )


def _format_model_statuses(statuses) -> str:
    return "\n".join(
        f"{status.from_code}->{status.to_code}: {status.status}"
        + (f"  {status.message}" if status.message else "")
        for status in statuses
    )


def _append_history_safely(entry: HistoryEntry, *, enabled: bool) -> str | None:
    if not enabled:
        return None
    try:
        append_history(entry, enabled=True)
    except OSError as exc:
        return f"History was not saved: {exc}"
    return None


def _direction_codes(config: TransConfig) -> tuple[str | None, str | None]:
    if config.default_direction == "zh-en":
        return "zh", "en"
    if config.default_direction == "en-zh":
        return "en", "zh"
    return None, None


def _translate_for_tui(translator, text: str, from_code: str | None, to_code: str | None) -> str:
    if isinstance(translator, ArgosTranslator):
        return translator.translate(text, from_code, to_code, fast_single_segment=True)
    return translator.translate(text, from_code, to_code)


def _translate_job(
    translator,
    text: str,
    from_code: str | None,
    to_code: str | None,
    save_history: bool,
) -> TranslationJobResult:
    actual_from = from_code or ("zh" if any("\u4e00" <= ch <= "\u9fff" for ch in text) else "en")
    actual_to = to_code or ("en" if actual_from == "zh" else "zh")
    try:
        result = _translate_for_tui(translator, text, from_code, to_code)
    except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
        return TranslationJobResult(text, "", actual_from, actual_to, None, str(exc))
    history_error = _append_history_safely(
        HistoryEntry(
            input_text=text,
            output_text=result,
            from_code=actual_from,
            to_code=actual_to,
            created_at=datetime.now(UTC).isoformat(timespec="seconds"),
        ),
        enabled=save_history,
    )
    return TranslationJobResult(text, result, actual_from, actual_to, history_error)


def build_tui_app(translator):
    app_module, binding_module, containers_module, widgets_module = _import_textual_modules()
    App = app_module.App
    ComposeResult = app_module.ComposeResult
    Binding = binding_module.Binding
    Button = widgets_module.Button
    Footer = widgets_module.Footer
    Header = widgets_module.Header
    Input = widgets_module.Input
    Static = widgets_module.Static
    TextArea = widgets_module.TextArea
    Container = containers_module.Container
    Horizontal = containers_module.Horizontal
    Vertical = containers_module.Vertical

    class TransTuiApp(App):
        TITLE = "trans"
        SUB_TITLE = "Offline zh/en translator"
        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("ctrl+s", "swap_direction", "Swap"),
            Binding("ctrl+l", "clear_input", "Clear"),
            Binding("f2", "show_translate", "Translate"),
            Binding("f3", "show_history", "History"),
            Binding("f4", "show_models", "Models"),
            Binding("f5", "show_settings", "Settings"),
        ]

        def __init__(self) -> None:
            self.translator = translator
            self.config = load_config()
            super().__init__()
            self.CSS = build_css(self.config.theme)
            self.current_page = self.config.startup_page
            self.from_code, self.to_code = _direction_codes(self.config)
            self.last_output = ""
            self.translation_in_progress = False

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal(id="app-shell"):
                with Vertical(id="sidebar"):
                    yield Static("trans", classes="accent")
                    yield Button("Translate", id="nav-translate", classes="nav-button")
                    yield Button("History", id="nav-history", classes="nav-button")
                    yield Button("Models", id="nav-models", classes="nav-button")
                    yield Button("Settings", id="nav-settings", classes="nav-button")
                    yield Static("F2-F5 switch pages\nq quit", classes="warning")
                with Container(id="main"):
                    yield Static("", id="status", classes="warning")
                    with Container(id="page-translate", classes="page"):
                        yield Static("Translate", classes="accent")
                        yield TextArea("", id="input")
                        yield Static("", id="output", classes="panel")
                        yield Button("Translate", id="translate")
                    with Container(id="page-history", classes="page"):
                        yield Static("History", classes="accent")
                        yield Input(placeholder="Search history", id="history-search")
                        yield Static("", id="history", classes="panel")
                    with Container(id="page-models", classes="page"):
                        yield Static("Models", classes="accent")
                        yield Static("", id="models", classes="panel")
                        yield Button("Install models", id="install-models")
                    with Container(id="page-settings", classes="page"):
                        yield Static("Settings", classes="accent")
                        yield Static("", id="settings", classes="panel")
                        yield Button("Save settings", id="save-settings")
            yield Footer()

        def on_mount(self) -> None:
            self.refresh_panels()
            self.show_page(self.current_page if self.current_page in PAGES else "translate")

        def on_button_pressed(self, event) -> None:
            button_id = event.button.id
            if button_id == "translate":
                self.action_translate()
            elif button_id == "install-models":
                self.action_install_models()
            elif button_id == "save-settings":
                save_config(self.config)
                self.set_status("Settings saved.", "success")
            elif button_id and button_id.startswith("nav-"):
                self.show_page(button_id.removeprefix("nav-"))

        def on_key(self, event) -> None:
            focused = self.screen.focused
            editing_text = isinstance(focused, (Input, TextArea))
            if editing_text and event.key != "escape":
                return

            key_actions = {
                "h": self.action_previous_page,
                "l": self.action_next_page,
                "j": self.action_focus_next,
                "k": self.action_focus_previous,
                "i": self.action_focus_input,
                "escape": self.action_normal_mode,
                "enter": self.action_primary_action,
                "return": self.action_primary_action,
                "r": self.action_refresh_current_page,
                "s": self.action_swap_direction,
                "c": self.action_clear_input,
                "y": self.action_copy_output,
            }
            action = key_actions.get(event.key)
            if action is None:
                return
            event.stop()
            action()

        def on_input_changed(self, event) -> None:
            if event.input.id == "history-search":
                query = event.value.strip()
                entries = search_history(query, limit=50) if query else load_history(limit=50)
                self.query_one("#history", Static).update(_format_history(entries))

        def set_status(self, message: str, style_class: str = "warning") -> None:
            status = self.query_one("#status", Static)
            status.set_classes(style_class)
            status.update(message)

        def refresh_panels(self) -> None:
            self.refresh_history_panel()
            self.query_one("#models", Static).update(_format_model_statuses(get_model_statuses(self.translator)))
            self.query_one("#settings", Static).update(
                "\n".join(
                    [
                        f"Theme: {self.config.theme}",
                        f"Default direction: {self.config.default_direction}",
                        f"Save history: {self.config.save_history}",
                        f"Startup page: {self.config.startup_page}",
                    ],
                ),
            )

        def refresh_history_panel(self) -> None:
            self.query_one("#history", Static).update(_format_history(load_history(limit=50)))

        def show_page(self, page: str) -> None:
            if page not in PAGES:
                page = "translate"
            self.current_page = page
            for candidate in PAGES:
                page_widget = self.query_one(f"#page-{candidate}")
                page_widget.set_classes("page page-active" if candidate == page else "page")
                nav_widget = self.query_one(f"#nav-{candidate}")
                nav_widget.set_classes("nav-button nav-active" if candidate == page else "nav-button")
            self.screen.focus(None)
            messages = {
                "translate": "Translate page. i input, Enter translate, s swap, c clear.",
                "history": "History page. / search box, r refresh.",
                "models": "Models page. Enter installs models, r refresh.",
                "settings": "Settings page. Enter saves current settings.",
            }
            self.set_status(messages[page], "accent")

        def _move_page(self, offset: int) -> None:
            index = PAGES.index(self.current_page) if self.current_page in PAGES else 0
            self.show_page(PAGES[(index + offset) % len(PAGES)])

        def action_previous_page(self) -> None:
            self._move_page(-1)

        def action_next_page(self) -> None:
            self._move_page(1)

        def action_focus_input(self) -> None:
            if self.current_page == "translate":
                self.query_one("#input", TextArea).focus()
            elif self.current_page == "history":
                self.query_one("#history-search", Input).focus()

        def action_normal_mode(self) -> None:
            self.screen.focus(None)
            self.set_status("Normal mode.", "accent")

        def action_primary_action(self) -> None:
            if self.current_page == "translate":
                self.action_translate()
            elif self.current_page == "models":
                self.action_install_models()
            elif self.current_page == "settings":
                save_config(self.config)
                self.set_status("Settings saved.", "success")

        def action_refresh_current_page(self) -> None:
            if self.current_page == "history":
                self.refresh_history_panel()
            elif self.current_page == "models":
                self.query_one("#models", Static).update(_format_model_statuses(get_model_statuses(self.translator)))
            elif self.current_page == "settings":
                self.refresh_panels()
            self.set_status(f"{self.current_page.title()} refreshed.", "success")

        def action_show_translate(self) -> None:
            self.show_page("translate")

        def action_show_history(self) -> None:
            self.refresh_panels()
            self.show_page("history")

        def action_show_models(self) -> None:
            self.refresh_panels()
            self.show_page("models")

        def action_show_settings(self) -> None:
            self.refresh_panels()
            self.show_page("settings")

        def action_swap_direction(self) -> None:
            if (self.from_code, self.to_code) == ("zh", "en"):
                self.from_code, self.to_code = "en", "zh"
            else:
                self.from_code, self.to_code = "zh", "en"
            self.set_status(f"Direction set to {self.from_code} -> {self.to_code}.", "success")

        def action_clear_input(self) -> None:
            self.query_one("#input", TextArea).text = ""
            self.query_one("#output", Static).update("")
            self.last_output = ""

        def action_copy_output(self) -> None:
            self.set_status("Copy fallback: select the output text in your terminal.", "warning")

        def action_translate(self) -> None:
            if self.translation_in_progress:
                self.set_status("Translation is still running.", "warning")
                return
            input_widget = self.query_one("#input", TextArea)
            text = input_widget.text.strip()
            if not text:
                self.set_status("Input is empty.", "warning")
                return
            self.translation_in_progress = True
            self.set_status("Translating...", "warning")
            worker = self.run_worker(
                lambda: _translate_job(
                    self.translator,
                    text,
                    self.from_code,
                    self.to_code,
                    self.config.save_history,
                ),
                name="translate",
                thread=True,
            )
            self.set_timer(0.05, lambda: self._poll_translation_worker(worker))

        def _poll_translation_worker(self, worker) -> None:
            state_name = worker.state.name
            if state_name in {"PENDING", "RUNNING"}:
                self.set_timer(0.05, lambda: self._poll_translation_worker(worker))
                return
            self.translation_in_progress = False
            if state_name == "SUCCESS":
                self._handle_translation_result(worker.result)
                return
            if state_name == "ERROR":
                self.set_status(str(worker.error), "error")
                return
            self.set_status("Translation was cancelled.", "warning")

        def _handle_translation_result(self, job_result: TranslationJobResult) -> None:
            if job_result.error:
                self.set_status(job_result.error, "error")
                return
            self.last_output = job_result.result
            self.query_one("#output", Static).update(job_result.result)
            self.refresh_history_panel()
            self.set_status(
                job_result.history_error or "Translated.",
                "warning" if job_result.history_error else "success",
            )

        def action_install_models(self) -> None:
            try:
                install_default_models(self.translator)
            except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
                self.set_status(str(exc), "error")
                return
            self.refresh_panels()
            self.set_status("Installed zh <-> en models.", "success")

    return TransTuiApp()


def run_tui(translator) -> int:
    app = build_tui_app(translator)
    result = app.run()
    return int(result) if isinstance(result, int) else 0

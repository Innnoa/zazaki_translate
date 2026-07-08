from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from trans_cli.tui2.actions import (
    clear_input,
    close_modal,
    open_models_modal,
    open_settings_modal,
    refresh_model_status,
    schedule_debounced_translation,
    translate_input,
)
from trans_cli.tui2.clipboard import TerminalOutput, TextClipboard, copy_via_osc52
from trans_cli.tui2.state import DebounceScheduler, FocusTarget, ModalSurface, WorkbenchState


class WorkbenchTranslator(Protocol):
    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        *,
        fast_single_segment: bool = False,
    ) -> str: ...


class WorkbenchController:
    def __init__(
        self,
        *,
        state: WorkbenchState,
        translator: WorkbenchTranslator,
        scheduler: DebounceScheduler,
        invalidate: Callable[[], None],
    ) -> None:
        self.state = state
        self._translator = translator
        self._scheduler = scheduler
        self._invalidate = invalidate

    def handle_input_change(self, text: str) -> None:
        self.state.input_text = text
        self.state.focus_target = FocusTarget.INPUT
        self.state.last_main_focus_target = FocusTarget.INPUT
        schedule_debounced_translation(
            self.state,
            self._translator,
            self._scheduler,
            on_state_change=self._invalidate,
        )

    def retry_translation(self) -> None:
        translate_input(self.state, self._translator)
        self._invalidate()

    def clear(self) -> None:
        clear_input(self.state)
        self.state.focus_target = FocusTarget.INPUT
        self.state.last_main_focus_target = FocusTarget.INPUT
        self._invalidate()

    def open_settings(self) -> None:
        open_settings_modal(self.state)
        self._invalidate()

    def open_models(self) -> None:
        refresh_model_status(self.state, self._translator)
        open_models_modal(self.state)
        self._invalidate()

    def handle_escape(self) -> None:
        if self.state.active_modal is not ModalSurface.NONE:
            close_modal(self.state)
            self._invalidate()

    def focus_next_region(self) -> None:
        if self.state.active_modal is not ModalSurface.NONE:
            return
        next_focus = FocusTarget.OUTPUT if self.state.focus_target is FocusTarget.INPUT else FocusTarget.INPUT
        self.state.focus_target = next_focus
        self.state.last_main_focus_target = next_focus
        self._invalidate()

    def copy_result(self) -> str:
        return self.state.output_text.strip()

    def copy_result_to_clipboard(
        self,
        clipboard: TextClipboard,
        terminal_output: TerminalOutput | None = None,
    ) -> None:
        data = self.copy_result()
        if not data:
            self.state.copy_status = "nothing to copy"
            self._invalidate()
            return
        try:
            clipboard.set_text(data)
        except Exception:
            if terminal_output is not None:
                try:
                    copy_via_osc52(data, terminal_output)
                except Exception:
                    self.state.copy_status = "clipboard unavailable"
                    self._invalidate()
                    return
                self.state.copy_status = "copied"
                self._invalidate()
                return
            self.state.copy_status = "clipboard unavailable"
            self._invalidate()
            return
        self.state.copy_status = "copied"
        self._invalidate()

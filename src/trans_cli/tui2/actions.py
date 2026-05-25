from __future__ import annotations

from collections.abc import Callable

from trans_cli.backend import ArgosTranslator
from trans_cli.core import resolve_direction
from trans_cli.model_status import get_model_statuses
from trans_cli.tui2.state import DebounceScheduler, FocusTarget, ModalSurface, TranslationPhase, WorkbenchState


def _remember_main_focus_target(state: WorkbenchState) -> None:
    if state.focus_target in (FocusTarget.INPUT, FocusTarget.OUTPUT):
        state.last_main_focus_target = state.focus_target


def _resolve_translation_preferences(default_direction: str) -> tuple[str | None, str | None]:
    if default_direction == "zh-en":
        return "zh", "en"
    if default_direction == "en-zh":
        return "en", "zh"
    return None, None


def open_settings_modal(state: WorkbenchState) -> None:
    _remember_main_focus_target(state)
    state.active_modal = ModalSurface.SETTINGS
    state.focus_target = FocusTarget.SETTINGS_MODAL


def open_models_modal(state: WorkbenchState) -> None:
    _remember_main_focus_target(state)
    state.active_modal = ModalSurface.MODELS
    state.focus_target = FocusTarget.MODELS_MODAL


def close_modal(state: WorkbenchState) -> None:
    state.active_modal = ModalSurface.NONE
    state.focus_target = state.last_main_focus_target


def clear_input(state: WorkbenchState) -> None:
    state.input_text = ""
    state.output_text = ""
    state.phase = TranslationPhase.IDLE
    state.copy_status = None
    if state.debounce_handle is not None:
        state.debounce_handle.cancel()
        state.debounce_handle = None


def set_translation_pending(state: WorkbenchState) -> None:
    state.phase = TranslationPhase.TRANSLATING
    state.copy_status = None


def set_translation_success(state: WorkbenchState, output_text: str) -> None:
    state.output_text = output_text
    state.phase = TranslationPhase.SUCCESS
    state.copy_status = None


def set_translation_error(state: WorkbenchState, message: str) -> None:
    state.output_text = message
    state.phase = TranslationPhase.ERROR
    state.copy_status = None


def translate_input(state: WorkbenchState, translator) -> None:
    if state.debounce_handle is not None:
        state.debounce_handle.cancel()
        state.debounce_handle = None

    text = state.input_text.strip()
    if not text:
        clear_input(state)
        return

    set_translation_pending(state)
    preferred_from, preferred_to = _resolve_translation_preferences(state.default_direction)
    from_code, to_code = resolve_direction(text, preferred_from, preferred_to)

    try:
        if isinstance(translator, ArgosTranslator):
            result = translator.translate(text, from_code, to_code, fast_single_segment=True)
        else:
            result = translator.translate(text, from_code, to_code)
    except Exception as exc:
        set_translation_error(state, str(exc))
        return

    set_translation_success(state, result)


def refresh_model_status(state: WorkbenchState, translator) -> None:
    statuses = get_model_statuses(translator)
    state.model_status_rows = [
        (f"{status.from_code}->{status.to_code}", status.message or status.status)
        for status in statuses
    ]


def schedule_debounced_translation(
    state: WorkbenchState,
    translator,
    scheduler: DebounceScheduler,
    *,
    delay_ms: int = 300,
    on_state_change: Callable[[], None] | None = None,
) -> None:
    if state.debounce_handle is not None:
        state.debounce_handle.cancel()

    if not state.input_text.strip():
        state.debounce_handle = None
        clear_input(state)
        if on_state_change is not None:
            on_state_change()
        return

    set_translation_pending(state)
    if on_state_change is not None:
        on_state_change()

    def run_translation() -> None:
        state.debounce_handle = None
        translate_input(state, translator)
        if on_state_change is not None:
            on_state_change()

    state.debounce_handle = scheduler(delay_ms, run_translation)

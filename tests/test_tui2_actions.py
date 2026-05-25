from collections.abc import Callable

from trans_cli.tui2.actions import (
    clear_input,
    close_modal,
    open_models_modal,
    open_settings_modal,
    schedule_debounced_translation,
    set_translation_error,
    set_translation_pending,
    set_translation_success,
    translate_input,
)
from trans_cli.backend import ArgosTranslator
from trans_cli.tui2.state import FocusTarget, ModalSurface, TranslationPhase, WorkbenchState


class FakeTranslator:
    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        **kwargs,
    ) -> str:
        return f"translated:{text}:{from_code}:{to_code}:{kwargs}"


class ErroringTranslator:
    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        **kwargs,
    ) -> str:
        raise RuntimeError(f"boom:{text}:{from_code}:{to_code}:{kwargs}")


class RecordingArgosTranslator(ArgosTranslator):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, str | None, str | None, bool]] = []

    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        *,
        fast_single_segment: bool = False,
    ) -> str:
        self.calls.append((text, from_code, to_code, fast_single_segment))
        return f"argos:{text}:{from_code}:{to_code}:{fast_single_segment}"


class FakeDebounceHandle:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class RecordingScheduler:
    def __init__(self) -> None:
        self.calls: list[tuple[int, Callable[[], None], FakeDebounceHandle]] = []

    def __call__(self, delay_ms: int, callback: Callable[[], None]):
        handle = FakeDebounceHandle()
        self.calls.append((delay_ms, callback, handle))
        return handle


def test_open_settings_modal_sets_active_modal() -> None:
    state = WorkbenchState()

    open_settings_modal(state)

    assert state.active_modal is ModalSurface.SETTINGS


def test_open_models_modal_sets_active_modal() -> None:
    state = WorkbenchState()

    open_models_modal(state)

    assert state.active_modal is ModalSurface.MODELS


def test_clear_input_resets_input_output_and_phase() -> None:
    state = WorkbenchState(input_text="hello", output_text="你好", phase=TranslationPhase.SUCCESS)

    clear_input(state)

    assert state.input_text == ""
    assert state.output_text == ""
    assert state.phase is TranslationPhase.IDLE


def test_set_translation_success_sets_output_and_success_phase() -> None:
    state = WorkbenchState()

    set_translation_success(state, "你好")

    assert state.output_text == "你好"
    assert state.phase is TranslationPhase.SUCCESS


def test_set_translation_pending_sets_translating_phase() -> None:
    state = WorkbenchState(phase=TranslationPhase.IDLE)

    set_translation_pending(state)

    assert state.phase is TranslationPhase.TRANSLATING


def test_set_translation_error_sets_message_and_error_phase() -> None:
    state = WorkbenchState()

    set_translation_error(state, message="network timeout")

    assert state.output_text == "network timeout"
    assert state.phase is TranslationPhase.ERROR


def test_open_models_modal_then_close_restores_none() -> None:
    state = WorkbenchState(focus_target=FocusTarget.OUTPUT, last_main_focus_target=FocusTarget.OUTPUT)

    open_models_modal(state)
    assert state.active_modal is ModalSurface.MODELS
    assert state.focus_target is FocusTarget.MODELS_MODAL

    close_modal(state)
    assert state.active_modal is ModalSurface.NONE
    assert state.focus_target is FocusTarget.OUTPUT


def test_translate_input_sets_success_and_output() -> None:
    state = WorkbenchState(input_text="hello")

    translate_input(state, FakeTranslator())

    assert state.phase is TranslationPhase.SUCCESS
    assert "translated:hello" in state.output_text


def test_translate_input_clears_stale_copy_feedback_before_success() -> None:
    state = WorkbenchState(input_text="hello", copy_status="copied")

    translate_input(state, FakeTranslator())

    assert state.phase is TranslationPhase.SUCCESS
    assert state.copy_status is None


def test_translate_input_honors_default_direction_override() -> None:
    state = WorkbenchState(input_text="hello", default_direction="zh-en")

    translate_input(state, FakeTranslator())

    assert state.phase is TranslationPhase.SUCCESS
    assert ":zh:en:" in state.output_text


def test_translate_input_blank_text_clears_stale_output_and_returns_idle() -> None:
    state = WorkbenchState(input_text="   ", output_text="stale", phase=TranslationPhase.SUCCESS)

    translate_input(state, FakeTranslator())

    assert state.output_text == ""
    assert state.phase is TranslationPhase.IDLE


def test_translate_input_uses_fast_single_segment_for_argos_translator() -> None:
    state = WorkbenchState(input_text="参数比较")
    translator = RecordingArgosTranslator()

    translate_input(state, translator)

    assert state.phase is TranslationPhase.SUCCESS
    assert translator.calls == [("参数比较", "zh", "en", True)]


def test_translate_input_sets_error_state_when_translator_fails() -> None:
    state = WorkbenchState(input_text="hello")

    translate_input(state, ErroringTranslator())

    assert state.phase is TranslationPhase.ERROR
    assert "boom:hello:en:zh:{}" == state.output_text


def test_schedule_debounced_translation_cancels_prior_work_and_runs_latest() -> None:
    state = WorkbenchState(input_text="hello")
    scheduler = RecordingScheduler()

    schedule_debounced_translation(state, FakeTranslator(), scheduler, delay_ms=250)

    assert state.phase is TranslationPhase.TRANSLATING
    assert len(scheduler.calls) == 1
    first_handle = scheduler.calls[0][2]

    state.input_text = "hello again"
    schedule_debounced_translation(state, FakeTranslator(), scheduler, delay_ms=250)

    assert first_handle.cancelled is True
    assert len(scheduler.calls) == 2

    callback = scheduler.calls[-1][1]
    callback()

    assert state.debounce_handle is None
    assert state.phase is TranslationPhase.SUCCESS
    assert "translated:hello again:en:zh" in state.output_text


def test_schedule_debounced_translation_blank_input_clears_state_without_scheduling() -> None:
    existing_handle = FakeDebounceHandle()
    state = WorkbenchState(
        input_text="   ",
        output_text="stale",
        phase=TranslationPhase.SUCCESS,
        copy_status="copied",
        debounce_handle=existing_handle,
    )
    scheduler = RecordingScheduler()

    schedule_debounced_translation(state, FakeTranslator(), scheduler, delay_ms=250)

    assert existing_handle.cancelled is True
    assert scheduler.calls == []
    assert state.debounce_handle is None
    assert state.output_text == ""
    assert state.copy_status is None
    assert state.phase is TranslationPhase.IDLE


def test_schedule_debounced_translation_notifies_before_and_after_translation() -> None:
    state = WorkbenchState(input_text="hello")
    scheduler = RecordingScheduler()
    notifications: list[str] = []

    schedule_debounced_translation(
        state,
        FakeTranslator(),
        scheduler,
        delay_ms=250,
        on_state_change=lambda: notifications.append(state.phase.value),
    )

    assert notifications == ["translating"]

    callback = scheduler.calls[-1][1]
    callback()

    assert notifications == ["translating", "success"]


def test_translate_input_cancels_pending_debounce_before_running() -> None:
    pending_handle = FakeDebounceHandle()
    state = WorkbenchState(input_text="hello", debounce_handle=pending_handle)

    translate_input(state, FakeTranslator())

    assert pending_handle.cancelled is True
    assert state.debounce_handle is None
    assert state.phase is TranslationPhase.SUCCESS

from base64 import b64encode
from collections.abc import Callable

from trans_cli.tui2.controller import WorkbenchController
from trans_cli.tui2.state import FocusTarget, ModalSurface, TranslationPhase, WorkbenchState


class FakeTranslator:
    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        *,
        fast_single_segment: bool = False,
    ) -> str:
        _ = fast_single_segment
        return f"translated:{text}:{from_code}:{to_code}"

    def _load_modules(self) -> tuple[object, object]:
        return object(), FakeTranslateModule()


class FakeInstalledLanguage:
    def __init__(self, code: str, installed_targets: set[str]) -> None:
        self.code = code
        self._installed_targets = installed_targets

    def get_translation(self, to_language: "FakeInstalledLanguage") -> object | None:
        if to_language.code in self._installed_targets:
            return object()
        return None


class FakeTranslateModule:
    def get_installed_languages(self) -> list[FakeInstalledLanguage]:
        return [
            FakeInstalledLanguage("zh", {"en"}),
            FakeInstalledLanguage("en", {"zh"}),
        ]


class FakeDebounceHandle:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class RecordingScheduler:
    def __init__(self) -> None:
        self.calls: list[tuple[int, Callable[[], None], FakeDebounceHandle]] = []

    def __call__(self, delay_ms: int, callback: Callable[[], None]) -> FakeDebounceHandle:
        handle = FakeDebounceHandle()
        self.calls.append((delay_ms, callback, handle))
        return handle


class FakeClipboard:
    def __init__(self) -> None:
        self.values: list[str] = []

    def set_text(self, text: str) -> None:
        self.values.append(text)


class ErroringClipboard:
    def set_text(self, text: str) -> None:
        raise RuntimeError(f"clipboard failed:{text}")


class FakeOutput:
    def __init__(self) -> None:
        self.raw_writes: list[str] = []
        self.flush_count = 0

    def write_raw(self, data: str) -> None:
        self.raw_writes.append(data)

    def flush(self) -> None:
        self.flush_count += 1


def test_controller_copy_result_returns_current_output() -> None:
    controller = WorkbenchController(
        state=WorkbenchState(output_text="translated text"),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: None,
    )

    assert controller.copy_result() == "translated text"


def test_workbench_controller_updates_input_and_schedules_translation() -> None:
    scheduler = RecordingScheduler()
    invalidations: list[str] = []
    controller = WorkbenchController(
        state=WorkbenchState(),
        translator=FakeTranslator(),
        scheduler=scheduler,
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.handle_input_change("hello")

    assert controller.state.input_text == "hello"
    assert controller.state.phase is TranslationPhase.TRANSLATING
    assert len(scheduler.calls) == 1
    assert invalidations == ["invalidate"]

    scheduled_callback = scheduler.calls[0][1]
    scheduled_callback()

    assert controller.state.phase is TranslationPhase.SUCCESS
    assert "translated:hello" in controller.state.output_text
    assert invalidations == ["invalidate", "invalidate"]


def test_workbench_controller_escape_closes_modal_and_restores_focus() -> None:
    controller = WorkbenchController(
        state=WorkbenchState(
            active_modal=ModalSurface.MODELS,
            focus_target=FocusTarget.MODELS_MODAL,
            last_main_focus_target=FocusTarget.OUTPUT,
        ),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: None,
    )

    controller.handle_escape()

    assert controller.state.active_modal is ModalSurface.NONE
    assert controller.state.focus_target is FocusTarget.OUTPUT


def test_workbench_controller_retry_translation_cancels_pending_debounce() -> None:
    pending_handle = FakeDebounceHandle()
    controller = WorkbenchController(
        state=WorkbenchState(input_text="hello", debounce_handle=pending_handle),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: None,
    )

    controller.retry_translation()

    assert pending_handle.cancelled is True
    assert controller.state.debounce_handle is None
    assert controller.state.phase is TranslationPhase.SUCCESS


def test_workbench_controller_clear_resets_state_and_focus() -> None:
    invalidations: list[str] = []
    pending_handle = FakeDebounceHandle()
    controller = WorkbenchController(
        state=WorkbenchState(
            input_text="hello",
            output_text="translated text",
            phase=TranslationPhase.SUCCESS,
            copy_status="copied",
            focus_target=FocusTarget.OUTPUT,
            last_main_focus_target=FocusTarget.OUTPUT,
            debounce_handle=pending_handle,
        ),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.clear()

    assert controller.state.input_text == ""
    assert controller.state.output_text == ""
    assert controller.state.phase is TranslationPhase.IDLE
    assert controller.state.copy_status is None
    assert controller.state.focus_target is FocusTarget.INPUT
    assert controller.state.last_main_focus_target is FocusTarget.INPUT
    assert controller.state.debounce_handle is None
    assert pending_handle.cancelled is True
    assert invalidations == ["invalidate"]


def test_workbench_controller_open_settings_opens_modal_and_invalidates() -> None:
    invalidations: list[str] = []
    controller = WorkbenchController(
        state=WorkbenchState(
            focus_target=FocusTarget.OUTPUT,
            last_main_focus_target=FocusTarget.INPUT,
        ),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.open_settings()

    assert controller.state.active_modal is ModalSurface.SETTINGS
    assert controller.state.focus_target is FocusTarget.SETTINGS_MODAL
    assert controller.state.last_main_focus_target is FocusTarget.OUTPUT
    assert invalidations == ["invalidate"]


def test_workbench_controller_open_models_refreshes_status_opens_modal_and_invalidates() -> None:
    invalidations: list[str] = []
    controller = WorkbenchController(
        state=WorkbenchState(
            focus_target=FocusTarget.INPUT,
            last_main_focus_target=FocusTarget.OUTPUT,
        ),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.open_models()

    assert controller.state.active_modal is ModalSurface.MODELS
    assert controller.state.focus_target is FocusTarget.MODELS_MODAL
    assert controller.state.last_main_focus_target is FocusTarget.INPUT
    assert controller.state.model_status_rows == [
        ("zh->en", "installed"),
        ("en->zh", "installed"),
    ]
    assert invalidations == ["invalidate"]


def test_workbench_controller_focus_next_region_toggles_between_input_and_output() -> None:
    invalidations: list[str] = []
    controller = WorkbenchController(
        state=WorkbenchState(
            focus_target=FocusTarget.INPUT,
            last_main_focus_target=FocusTarget.INPUT,
        ),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.focus_next_region()

    assert controller.state.focus_target is FocusTarget.OUTPUT
    assert controller.state.last_main_focus_target is FocusTarget.OUTPUT

    controller.focus_next_region()

    assert controller.state.focus_target is FocusTarget.INPUT
    assert controller.state.last_main_focus_target is FocusTarget.INPUT
    assert invalidations == ["invalidate", "invalidate"]


def test_workbench_controller_focus_next_region_is_noop_while_modal_is_active() -> None:
    invalidations: list[str] = []
    controller = WorkbenchController(
        state=WorkbenchState(
            active_modal=ModalSurface.SETTINGS,
            focus_target=FocusTarget.SETTINGS_MODAL,
            last_main_focus_target=FocusTarget.OUTPUT,
        ),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.focus_next_region()

    assert controller.state.focus_target is FocusTarget.SETTINGS_MODAL
    assert controller.state.last_main_focus_target is FocusTarget.OUTPUT
    assert invalidations == []


def test_workbench_controller_copy_result_to_clipboard_sets_success_feedback() -> None:
    invalidations: list[str] = []
    clipboard = FakeClipboard()
    controller = WorkbenchController(
        state=WorkbenchState(output_text="translated text"),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.copy_result_to_clipboard(clipboard)

    assert clipboard.values == ["translated text"]
    assert controller.state.copy_status == "copied"
    assert invalidations == ["invalidate"]


def test_workbench_controller_copy_result_to_clipboard_handles_empty_output() -> None:
    invalidations: list[str] = []
    clipboard = FakeClipboard()
    controller = WorkbenchController(
        state=WorkbenchState(output_text=""),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.copy_result_to_clipboard(clipboard)

    assert clipboard.values == []
    assert controller.state.copy_status == "nothing to copy"
    assert invalidations == ["invalidate"]


def test_workbench_controller_copy_result_to_clipboard_handles_clipboard_failure() -> None:
    invalidations: list[str] = []
    controller = WorkbenchController(
        state=WorkbenchState(output_text="translated text"),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.copy_result_to_clipboard(ErroringClipboard())

    assert controller.state.copy_status == "clipboard unavailable"
    assert invalidations == ["invalidate"]


def test_workbench_controller_copy_result_to_clipboard_falls_back_to_terminal_clipboard() -> None:
    invalidations: list[str] = []
    output = FakeOutput()
    controller = WorkbenchController(
        state=WorkbenchState(output_text="translated text"),
        translator=FakeTranslator(),
        scheduler=RecordingScheduler(),
        invalidate=lambda: invalidations.append("invalidate"),
    )

    controller.copy_result_to_clipboard(ErroringClipboard(), output)

    assert controller.state.copy_status == "copied"
    assert output.raw_writes == [f"\x1b]52;c;{b64encode(b'translated text').decode('ascii')}\x07"]
    assert output.flush_count == 2
    assert invalidations == ["invalidate"]

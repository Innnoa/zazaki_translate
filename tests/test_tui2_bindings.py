from types import SimpleNamespace

from trans_cli.tui2.bindings import build_key_bindings
from trans_cli.tui2.state import FocusTarget, WorkbenchState


def test_build_key_bindings_is_importable() -> None:
    assert callable(build_key_bindings)


class FakeBindings:
    def __init__(self) -> None:
        self.handlers: dict[str, object] = {}
        self.filters: dict[str, object | None] = {}

    def add(self, key: str, filter=None):
        def decorator(func):
            self.handlers[key] = func
            self.filters[key] = filter
            return func

        return decorator


class FakeLayout:
    def __init__(self) -> None:
        self.focused: list[object] = []

    def focus(self, target: object) -> None:
        self.focused.append(target)


class FakeApp:
    def __init__(self, *, clipboard: object | None = None) -> None:
        self.clipboard = clipboard
        self.layout = FakeLayout()
        self.exit_results: list[int] = []

    def exit(self, *, result: int) -> None:
        self.exit_results.append(result)


class FakeController:
    def __init__(self, state: WorkbenchState) -> None:
        self.state = state
        self.calls: list[str] = []
        self.clipboards: list[object] = []
        self.escape_focus_target = state.focus_target
        self.next_focus_target = state.focus_target

    def clear(self) -> None:
        self.calls.append("clear")
        self.state.input_text = ""

    def retry_translation(self) -> None:
        self.calls.append("retry_translation")

    def open_settings(self) -> None:
        self.calls.append("open_settings")

    def open_models(self) -> None:
        self.calls.append("open_models")

    def handle_escape(self) -> None:
        self.calls.append("handle_escape")
        self.state.focus_target = self.escape_focus_target

    def focus_next_region(self) -> None:
        self.calls.append("focus_next_region")
        self.state.focus_target = self.next_focus_target

    def copy_result_to_clipboard(self, clipboard: object) -> None:
        self.calls.append("copy_result_to_clipboard")
        self.clipboards.append(clipboard)


def test_build_key_bindings_registers_expected_shortcuts_and_q_filter() -> None:
    state = WorkbenchState(focus_target=FocusTarget.OUTPUT)
    controller = FakeController(state)
    input_window = object()
    output_window = object()
    modal_window = object()
    allow_calls: list[WorkbenchState] = []

    bindings = build_key_bindings(
        state=state,
        controller=controller,
        input_area=SimpleNamespace(window=input_window),
        input_buffer=SimpleNamespace(text="seed"),
        output_window=output_window,
        modal_window=modal_window,
        allow_plain_quit=lambda current_state: allow_calls.append(current_state) or True,
        Condition=lambda callback: callback,
        KeyBindings=FakeBindings,
        FocusTarget=FocusTarget,
    )

    assert set(bindings.handlers) == {"q", "c-c", "c-d", "c-r", "f2", "f3", "escape", "tab", "c-y"}
    assert bindings.filters["q"]() is True
    assert allow_calls == [state]


def test_build_key_bindings_clear_binding_resets_buffer_text_from_state() -> None:
    state = WorkbenchState(input_text="seed")
    controller = FakeController(state)
    input_buffer = SimpleNamespace(text="stale")
    bindings = build_key_bindings(
        state=state,
        controller=controller,
        input_area=SimpleNamespace(window=object()),
        input_buffer=input_buffer,
        output_window=object(),
        modal_window=object(),
        allow_plain_quit=lambda _state: True,
        Condition=lambda callback: callback,
        KeyBindings=FakeBindings,
        FocusTarget=FocusTarget,
    )

    bindings.handlers["c-d"](SimpleNamespace(app=FakeApp()))

    assert controller.calls == ["clear"]
    assert state.input_text == ""
    assert input_buffer.text == ""


def test_build_key_bindings_modal_focus_and_clipboard_bindings_drive_controller() -> None:
    state = WorkbenchState(focus_target=FocusTarget.INPUT)
    controller = FakeController(state)
    input_window = object()
    output_window = object()
    modal_window = object()
    clipboard = object()
    app = FakeApp(clipboard=clipboard)
    bindings = build_key_bindings(
        state=state,
        controller=controller,
        input_area=SimpleNamespace(window=input_window),
        input_buffer=SimpleNamespace(text="seed"),
        output_window=output_window,
        modal_window=modal_window,
        allow_plain_quit=lambda _state: True,
        Condition=lambda callback: callback,
        KeyBindings=FakeBindings,
        FocusTarget=FocusTarget,
    )

    bindings.handlers["f2"](SimpleNamespace(app=app))
    controller.escape_focus_target = FocusTarget.OUTPUT
    bindings.handlers["escape"](SimpleNamespace(app=app))
    controller.next_focus_target = FocusTarget.INPUT
    bindings.handlers["tab"](SimpleNamespace(app=app))
    bindings.handlers["c-y"](SimpleNamespace(app=app))

    assert controller.calls == [
        "open_settings",
        "handle_escape",
        "focus_next_region",
        "copy_result_to_clipboard",
    ]
    assert app.layout.focused == [modal_window, output_window, input_window]
    assert controller.clipboards == [clipboard]


def test_build_key_bindings_exit_shortcuts_exit_application() -> None:
    bindings = build_key_bindings(
        state=WorkbenchState(focus_target=FocusTarget.OUTPUT),
        controller=FakeController(WorkbenchState()),
        input_area=SimpleNamespace(window=object()),
        input_buffer=SimpleNamespace(text="seed"),
        output_window=object(),
        modal_window=object(),
        allow_plain_quit=lambda _state: True,
        Condition=lambda callback: callback,
        KeyBindings=FakeBindings,
        FocusTarget=FocusTarget,
    )
    app = FakeApp()
    event = SimpleNamespace(app=app)

    bindings.handlers["q"](event)
    bindings.handlers["c-c"](event)

    assert app.exit_results == [0, 0]

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, Protocol

from trans_cli.backend import DependencyMissingError
from trans_cli.tui2.bindings import build_key_bindings
from trans_cli.tui2.clipboard import build_clipboard
from trans_cli.tui2.controller import WorkbenchController
from trans_cli.tui2.modals import build_active_modal_lines
from trans_cli.tui2.render import render_status_line, render_workbench_snapshot
from trans_cli.tui2.runtime import create_debounce_scheduler, warmup_translator
from trans_cli.tui2.state import FocusTarget, ModalSurface, WorkbenchState


class WorkbenchShell(Protocol):
    def run(self) -> int: ...


ShellFactory = Callable[..., WorkbenchShell]


def build_workbench_state() -> WorkbenchState:
    return WorkbenchState()


def _direction_label(default_direction: str) -> str:
    if default_direction == "zh-en":
        return "zh->en"
    if default_direction == "en-zh":
        return "en->zh"
    return "auto"


def build_workbench_text(state: WorkbenchState) -> str:
    status_line = render_status_line(state, direction_label=_direction_label(state.default_direction))
    snapshot = render_workbench_snapshot(state)
    return "\n\n".join([status_line, snapshot, "Press Ctrl+C to exit, or q when not editing input."])


def _allow_plain_quit(state: WorkbenchState) -> bool:
    return state.focus_target is not FocusTarget.INPUT


class PromptToolkitWorkbenchShell:
    def __init__(self, application: Any) -> None:
        self._application = application

    def run(self) -> int:
        result = self._application.run()
        return 0 if result is None else int(result)


def build_workbench_shell(*, state: WorkbenchState, translator) -> WorkbenchShell:
    try:
        application_module = import_module("prompt_toolkit.application")
        key_binding_module = import_module("prompt_toolkit.key_binding")
        layout_module = import_module("prompt_toolkit.layout")
        containers_module = import_module("prompt_toolkit.layout.containers")
        controls_module = import_module("prompt_toolkit.layout.controls")
        dimension_module = import_module("prompt_toolkit.layout.dimension")
        filters_module = import_module("prompt_toolkit.filters")
        widgets_module = import_module("prompt_toolkit.widgets")
    except ModuleNotFoundError as exc:
        raise DependencyMissingError(
            "Missing TUI dependencies `prompt_toolkit`. Run `pip install -e '.[tui]'` first.",
        ) from exc

    Application = application_module.Application
    KeyBindings = key_binding_module.KeyBindings
    Layout = layout_module.Layout
    ConditionalContainer = containers_module.ConditionalContainer
    HSplit = containers_module.HSplit
    Window = containers_module.Window
    FormattedTextControl = controls_module.FormattedTextControl
    Dimension = dimension_module.Dimension
    Condition = filters_module.Condition
    Frame = widgets_module.Frame
    TextArea = widgets_module.TextArea

    output_control = FormattedTextControl(text=lambda: state.output_text or "", focusable=True)
    modal_control = FormattedTextControl(text=lambda: "\n".join(build_active_modal_lines(state)), focusable=True)

    app_holder: dict[str, Any] = {}

    def invalidate() -> None:
        application = app_holder.get("app")
        if application is not None:
            application.invalidate()

    controller = WorkbenchController(
        state=state,
        translator=translator,
        scheduler=create_debounce_scheduler(lambda: app_holder["app"]),
        invalidate=invalidate,
    )

    def handle_buffer_change(_buffer: Any) -> None:
        controller.handle_input_change(input_area.text)

    input_area = TextArea(
        text=state.input_text,
        multiline=True,
        wrap_lines=True,
        scrollbar=True,
        style="class:input",
    )
    input_buffer = input_area.buffer
    input_buffer.on_text_changed += handle_buffer_change

    output_window = Window(content=output_control, wrap_lines=True, always_hide_cursor=True)
    modal_window = Window(content=modal_control, wrap_lines=True, always_hide_cursor=True)

    bindings = build_key_bindings(
        state=state,
        controller=controller,
        input_area=input_area,
        input_buffer=input_buffer,
        output_window=output_window,
        modal_window=modal_window,
        allow_plain_quit=_allow_plain_quit,
        Condition=Condition,
        KeyBindings=KeyBindings,
        FocusTarget=FocusTarget,
    )

    header_window = Window(
        content=FormattedTextControl(text=lambda: render_status_line(state, direction_label=_direction_label(state.default_direction))),
        height=1,
        always_hide_cursor=True,
    )

    root = HSplit(
        [
            header_window,
            Frame(input_area, title="Input"),
            Frame(output_window, title="Result", height=Dimension(weight=1)),
            ConditionalContainer(
                content=Frame(modal_window, title="Modal"),
                filter=Condition(lambda: state.active_modal is not ModalSurface.NONE),
            ),
        ]
    )
    application = Application(
        layout=Layout(root, focused_element=input_area.window),
        key_bindings=bindings,
        full_screen=True,
        clipboard=build_clipboard(),
    )
    app_holder["app"] = application
    return PromptToolkitWorkbenchShell(application)


def run_tui(translator, *, shell_factory: ShellFactory | None = None) -> int:
    state = build_workbench_state()
    app_holder = import_module("threading")
    app_holder.Thread(target=warmup_translator, args=(translator,), kwargs={"state": state}, daemon=True).start()
    shell = (shell_factory or build_workbench_shell)(state=state, translator=translator)
    return shell.run()

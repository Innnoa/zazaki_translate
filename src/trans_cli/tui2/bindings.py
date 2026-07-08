from __future__ import annotations

from collections.abc import Callable
from typing import Any


def build_key_bindings(
    *,
    state,
    controller,
    input_area,
    input_buffer,
    output_window,
    modal_window,
    allow_plain_quit: Callable[[Any], bool],
    Condition,
    KeyBindings,
    FocusTarget,
):
    bindings = KeyBindings()

    @bindings.add("q", filter=Condition(lambda: allow_plain_quit(state)))
    def _exit_on_q(event) -> None:
        event.app.exit(result=0)

    @bindings.add("c-c")
    def _exit_on_ctrl_c(event) -> None:
        event.app.exit(result=0)

    @bindings.add("c-d")
    def _clear_input(_event) -> None:
        controller.clear()
        input_buffer.text = state.input_text

    @bindings.add("c-r")
    def _retry_translation(_event) -> None:
        controller.retry_translation()

    @bindings.add("f2")
    def _open_settings(event) -> None:
        controller.open_settings()
        event.app.layout.focus(modal_window)

    @bindings.add("f3")
    def _open_models(event) -> None:
        controller.open_models()
        event.app.layout.focus(modal_window)

    @bindings.add("escape")
    def _escape(event) -> None:
        controller.handle_escape()
        if state.focus_target is FocusTarget.INPUT:
            event.app.layout.focus(input_area.window)
        elif state.focus_target is FocusTarget.OUTPUT:
            event.app.layout.focus(output_window)

    @bindings.add("tab")
    def _tab(event) -> None:
        controller.focus_next_region()
        if state.focus_target is FocusTarget.INPUT:
            event.app.layout.focus(input_area.window)
        else:
            event.app.layout.focus(output_window)

    @bindings.add("c-y")
    def _copy_result(event) -> None:
        controller.copy_result_to_clipboard(event.app.clipboard, event.app.output)

    return bindings

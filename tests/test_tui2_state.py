from trans_cli.tui2.actions import close_modal
from trans_cli.tui2.state import ModalSurface, TranslationPhase, WorkbenchState


def test_workbench_state_defaults_to_input_focused_idle_translate_view() -> None:
    state = WorkbenchState()

    assert state.input_text == ""
    assert state.output_text == ""
    assert state.phase is TranslationPhase.IDLE
    assert state.active_modal is ModalSurface.NONE
    assert state.focus_target == "input"


def test_close_modal_returns_to_none_surface() -> None:
    state = WorkbenchState(active_modal=ModalSurface.MODELS)

    close_modal(state)

    assert state.active_modal is ModalSurface.NONE

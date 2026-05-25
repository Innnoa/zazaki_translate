from trans_cli.model_status import ModelPairStatus
from trans_cli.tui2.modals import build_models_modal_lines, build_settings_modal_lines
from trans_cli.tui2.render import render_status_line, render_workbench_snapshot
from trans_cli.tui2.state import TranslationPhase, WorkbenchState


def test_render_status_line_includes_direction_and_phase() -> None:
    state = WorkbenchState(phase=TranslationPhase.TRANSLATING)

    status = render_status_line(state, direction_label="auto->zh")

    assert "auto->zh" in status
    assert "translating" in status
    assert "Ctrl+Y Copy Result" in status
    assert "F2" not in status
    assert "F3" not in status
    assert "Retry" not in status
    assert "Clear" not in status


def test_render_status_line_shows_warming_up_until_runtime_is_ready() -> None:
    warming = render_status_line(WorkbenchState(warmup_ready=False), direction_label="auto")
    ready = render_status_line(WorkbenchState(warmup_ready=True), direction_label="auto")

    assert "warming up" in warming
    assert "ready" not in warming
    assert "ready" in ready


def test_render_status_line_includes_copy_feedback_when_present() -> None:
    status = render_status_line(WorkbenchState(copy_status="copied"), direction_label="auto")

    assert "copied" in status


def test_render_workbench_snapshot_includes_input_and_output_labels() -> None:
    state = WorkbenchState(input_text="hello", output_text="你好")

    snapshot = render_workbench_snapshot(state)

    assert "Input" in snapshot
    assert "Result" in snapshot
    assert "hello" in snapshot
    assert "你好" in snapshot


def test_build_settings_modal_lines_includes_theme_and_direction() -> None:
    lines = build_settings_modal_lines(theme="mocha", default_direction="auto")

    assert any("Theme" in line for line in lines)
    assert any("Direction" in line for line in lines)


def test_build_models_modal_lines_includes_install_hint() -> None:
    lines = build_models_modal_lines([("zh->en", "missing")])

    assert any("zh->en" in line for line in lines)
    assert any("Install" in line for line in lines)


def test_build_models_modal_lines_uses_model_status_messages() -> None:
    rows = [
        ModelPairStatus("zh", "en", "missing", "Run `trans --install-models` first."),
    ]

    lines = build_models_modal_lines([(f"{row.from_code}->{row.to_code}", row.message or row.status) for row in rows])

    assert any("Run `trans --install-models` first." in line for line in lines)

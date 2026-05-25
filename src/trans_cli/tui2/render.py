from __future__ import annotations

from trans_cli.tui2.modals import build_active_modal_lines
from trans_cli.tui2.state import WorkbenchState
from trans_cli.tui2.theme import (
    COPY_RESULT_LABEL,
    INPUT_LABEL,
    RESULT_LABEL,
    STATUS_LABELS,
    WORKBENCH_TITLE,
)


def render_status_line(state: WorkbenchState, *, direction_label: str) -> str:
    phase = STATUS_LABELS[state.phase.value]
    warmup_state = "ready" if state.warmup_ready else "warming up"
    parts = [
        WORKBENCH_TITLE,
        direction_label,
        warmup_state,
        phase,
        f"Ctrl+Y {COPY_RESULT_LABEL}",
    ]
    if state.copy_status:
        parts.append(state.copy_status)
    return " | ".join(parts)


def render_workbench_snapshot(state: WorkbenchState) -> str:
    lines = [
        INPUT_LABEL,
        state.input_text,
        "",
        RESULT_LABEL,
        state.output_text,
    ]
    modal_lines = build_active_modal_lines(state)
    if modal_lines:
        lines.extend(["", *modal_lines])
    return "\n".join(lines)

from __future__ import annotations

from trans_cli.tui2.state import ModalSurface, WorkbenchState


def build_settings_modal_lines(*, theme: str, default_direction: str) -> list[str]:
    return [
        "Settings",
        f"Theme: {theme}",
        f"Direction: {default_direction}",
        "Esc Close",
    ]


def build_models_modal_lines(status_rows: list[tuple[str, str]]) -> list[str]:
    lines = ["Models"]
    lines.extend(f"{pair}: {message}" for pair, message in status_rows)
    lines.append("Install default models")
    lines.append("Esc Close")
    return lines


def build_active_modal_lines(state: WorkbenchState) -> list[str]:
    if state.active_modal is ModalSurface.SETTINGS:
        return build_settings_modal_lines(theme=state.theme, default_direction=state.default_direction)
    if state.active_modal is ModalSurface.MODELS:
        return build_models_modal_lines(state.model_status_rows)
    return []

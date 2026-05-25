from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol


class TranslationPhase(str, Enum):
    IDLE = "idle"
    TRANSLATING = "translating"
    SUCCESS = "success"
    ERROR = "error"


class ModalSurface(str, Enum):
    NONE = "none"
    SETTINGS = "settings"
    MODELS = "models"


class FocusTarget(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    SETTINGS_MODAL = "settings_modal"
    MODELS_MODAL = "models_modal"


class DebounceHandle(Protocol):
    def cancel(self) -> None: ...


class DebounceScheduler(Protocol):
    def __call__(self, delay_ms: int, callback: Callable[[], None]) -> DebounceHandle: ...


@dataclass
class WorkbenchState:
    input_text: str = ""
    output_text: str = ""
    theme: str = "default"
    default_direction: str = "auto"
    warmup_ready: bool = False
    phase: TranslationPhase = TranslationPhase.IDLE
    copy_status: str | None = None
    active_modal: ModalSurface = ModalSurface.NONE
    focus_target: FocusTarget = FocusTarget.INPUT
    last_main_focus_target: FocusTarget = FocusTarget.INPUT
    debounce_handle: DebounceHandle | None = None
    model_status_rows: list[tuple[str, str]] = field(default_factory=list)

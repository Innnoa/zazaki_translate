from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from trans_cli.tui2.state import WorkbenchState


def warmup_translator(translator, *, state: WorkbenchState | None = None) -> None:
    try:
        translator.translate("warmup", "en", "zh", fast_single_segment=True)
        translator.translate("预热", "zh", "en", fast_single_segment=True)
    except Exception:
        return
    if state is not None:
        state.warmup_ready = True


def create_debounce_scheduler(application_or_factory: Any):
    get_application = application_or_factory if callable(application_or_factory) else lambda: application_or_factory

    def debounce_scheduler(delay_ms: int, callback: Callable[[], None]):
        class DebounceTaskHandle:
            def __init__(self) -> None:
                self.cancelled = False
                self.task = None

            def cancel(self) -> None:
                self.cancelled = True
                if self.task is not None:
                    self.task.cancel()

        handle = DebounceTaskHandle()

        async def runner() -> None:
            try:
                await asyncio.sleep(delay_ms / 1000)
            except asyncio.CancelledError:
                return
            if handle.cancelled:
                return
            callback()

        application = get_application()
        create_background_task = getattr(application, "create_background_task")
        handle.task = create_background_task(runner())
        return handle

    return debounce_scheduler

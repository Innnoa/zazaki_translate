import asyncio

from trans_cli.tui2.runtime import create_debounce_scheduler, warmup_translator
from trans_cli.tui2.state import WorkbenchState


class FakeTask:
    def __init__(self, coroutine) -> None:
        self.coroutine = coroutine
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class FakeApplication:
    def __init__(self) -> None:
        self.tasks: list[FakeTask] = []

    def create_background_task(self, coroutine):
        task = FakeTask(coroutine)
        self.tasks.append(task)
        return task


class WarmupTranslator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, str | None, bool]] = []

    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        *,
        fast_single_segment: bool = False,
    ) -> str:
        self.calls.append((text, from_code, to_code, fast_single_segment))
        return "ok"


def test_warmup_translator_primes_both_default_translation_directions() -> None:
    translator = WarmupTranslator()

    warmup_translator(translator)

    assert translator.calls == [
        ("warmup", "en", "zh", True),
        ("预热", "zh", "en", True),
    ]


def test_create_debounce_scheduler_runs_callback_after_delay() -> None:
    app = FakeApplication()
    calls: list[str] = []
    scheduler = create_debounce_scheduler(app)

    original_sleep = asyncio.sleep

    async def immediate_sleep(_seconds: float) -> None:
        return None

    asyncio.sleep = immediate_sleep
    try:
        handle = scheduler(25, lambda: calls.append("ran"))
        asyncio.run(app.tasks[0].coroutine)
    finally:
        asyncio.sleep = original_sleep

    assert handle.cancelled is False
    assert calls == ["ran"]


def test_create_debounce_scheduler_does_not_run_callback_after_cancel() -> None:
    app = FakeApplication()
    calls: list[str] = []
    scheduler = create_debounce_scheduler(app)

    original_sleep = asyncio.sleep

    async def immediate_sleep(_seconds: float) -> None:
        return None

    asyncio.sleep = immediate_sleep
    try:
        handle = scheduler(25, lambda: calls.append("ran"))
        handle.cancel()
        asyncio.run(app.tasks[0].coroutine)
    finally:
        asyncio.sleep = original_sleep

    assert handle.cancelled is True
    assert app.tasks[0].cancelled is True
    assert calls == []


def test_create_debounce_scheduler_accepts_callable_application_factory() -> None:
    app = FakeApplication()
    calls: list[str] = []
    factory_calls: list[str] = []

    def application_factory() -> FakeApplication:
        factory_calls.append("called")
        return app

    scheduler = create_debounce_scheduler(application_factory)

    original_sleep = asyncio.sleep

    async def immediate_sleep(_seconds: float) -> None:
        return None

    asyncio.sleep = immediate_sleep
    try:
        handle = scheduler(25, lambda: calls.append("ran"))
        asyncio.run(app.tasks[0].coroutine)
    finally:
        asyncio.sleep = original_sleep

    assert handle.cancelled is False
    assert factory_calls == ["called"]
    assert calls == ["ran"]


def test_warmup_translator_marks_state_ready_when_it_finishes() -> None:
    translator = WarmupTranslator()
    state = WorkbenchState(warmup_ready=False)

    warmup_translator(translator, state=state)

    assert state.warmup_ready is True

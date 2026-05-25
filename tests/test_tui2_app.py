from trans_cli.tui2.app import (
    _allow_plain_quit,
    build_workbench_shell,
    build_workbench_state,
    build_workbench_text,
    run_tui,
)
from trans_cli.tui2.state import FocusTarget, ModalSurface, WorkbenchState


class FakeTranslator:
    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
    ) -> str:
        return f"translated:{text}:{from_code}:{to_code}"


class FakeShell:
    def __init__(self, result: int = 0) -> None:
        self.result = result
        self.ran = False

    def run(self) -> int:
        self.ran = True
        return self.result


def test_build_workbench_state_returns_workbench_state() -> None:
    assert isinstance(build_workbench_state(), WorkbenchState)


def test_run_tui_runs_workbench_shell_and_returns_exit_code() -> None:
    translator = FakeTranslator()
    shell = FakeShell(result=0)
    captured: dict[str, object] = {}

    def fake_shell_factory(*, state: WorkbenchState, translator: FakeTranslator) -> FakeShell:
        captured["state"] = state
        captured["translator"] = translator
        captured["text"] = build_workbench_text(state)
        return shell

    exit_code = run_tui(translator, shell_factory=fake_shell_factory)

    assert exit_code == 0
    assert shell.ran is True
    assert captured["translator"] is translator
    assert isinstance(captured["state"], WorkbenchState)
    assert "trans" in str(captured["text"])
    assert "Input" in str(captured["text"])
    assert "Result" in str(captured["text"])


def test_build_workbench_state_can_hold_preloaded_input() -> None:
    state = build_workbench_state()
    state.input_text = "hello"

    assert state.input_text == "hello"


def test_build_workbench_text_includes_modal_labels_when_modal_is_active() -> None:
    state = WorkbenchState(active_modal=ModalSurface.SETTINGS)

    text = build_workbench_text(state)

    assert "Settings" in text


def test_build_workbench_shell_returns_shell_object() -> None:
    state = build_workbench_state()

    shell = build_workbench_shell(state=state, translator=FakeTranslator())

    assert hasattr(shell, "run")


def test_build_workbench_shell_uses_clipboard_built_by_clipboard_builder(monkeypatch) -> None:
    state = build_workbench_state()
    sentinel_clipboard = object()
    captured: dict[str, object] = {}

    class FakeApplication:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def invalidate(self) -> None:
            return None

        def run(self) -> int:
            return 0

    def fake_import(name: str):
        if name == "prompt_toolkit.application":
            return type("M", (), {"Application": FakeApplication})
        return __import__(name, fromlist=["*"])

    monkeypatch.setattr("trans_cli.tui2.app.build_clipboard", lambda: sentinel_clipboard)
    monkeypatch.setattr("trans_cli.tui2.app.import_module", fake_import)

    build_workbench_shell(state=state, translator=FakeTranslator())

    assert captured["clipboard"] is sentinel_clipboard


def test_build_workbench_shell_wires_build_key_bindings_result_into_application(monkeypatch) -> None:
    state = build_workbench_state()
    sentinel_bindings = object()
    captured: dict[str, object] = {}

    class FakeApplication:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def invalidate(self) -> None:
            return None

        def run(self) -> int:
            return 0

    binding_builder_calls: list[dict[str, object]] = []

    def fake_build_key_bindings(**kwargs):
        binding_builder_calls.append(kwargs)
        return sentinel_bindings

    def fake_import(name: str):
        if name == "prompt_toolkit.application":
            return type("M", (), {"Application": FakeApplication})
        return __import__(name, fromlist=["*"])

    monkeypatch.setattr("trans_cli.tui2.app.build_key_bindings", fake_build_key_bindings)
    monkeypatch.setattr("trans_cli.tui2.app.import_module", fake_import)

    build_workbench_shell(state=state, translator=FakeTranslator())

    assert len(binding_builder_calls) == 1
    assert binding_builder_calls[0]["state"] is state
    assert callable(binding_builder_calls[0]["allow_plain_quit"])
    assert captured["key_bindings"] is sentinel_bindings


def test_allow_plain_quit_is_disabled_while_input_is_focused() -> None:
    assert _allow_plain_quit(WorkbenchState(focus_target=FocusTarget.INPUT)) is False
    assert _allow_plain_quit(WorkbenchState(focus_target=FocusTarget.OUTPUT)) is True


def test_run_tui_starts_background_warmup_without_blocking_shell(monkeypatch) -> None:
    translator = FakeTranslator()
    shell = FakeShell(result=0)
    started: list[tuple[object, tuple[object, ...], dict[str, object], bool]] = []

    class FakeThread:
        def __init__(self, *, target, args=(), kwargs=None, daemon=False) -> None:
            started.append((target, args, kwargs or {}, daemon))

        def start(self) -> None:
            return None

    def fake_shell_factory(*, state: WorkbenchState, translator: FakeTranslator) -> FakeShell:
        return shell

    monkeypatch.setattr("trans_cli.tui2.app.import_module", lambda name: __import__(name) if name != "threading" else type("T", (), {"Thread": FakeThread}))

    exit_code = run_tui(translator, shell_factory=fake_shell_factory)

    assert exit_code == 0
    assert shell.ran is True
    assert len(started) == 1
    assert started[0][1] == (translator,)
    state = started[0][2]["state"]
    assert isinstance(state, WorkbenchState)
    assert state.warmup_ready is False
    assert started[0][3] is True

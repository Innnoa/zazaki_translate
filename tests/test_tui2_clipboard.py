from trans_cli.tui2.clipboard import build_clipboard


class FakeClipboard:
    def __init__(self) -> None:
        self.values: list[str] = []

    def set_text(self, text: str) -> None:
        self.values.append(text)


def test_build_clipboard_returns_clipboard_instance() -> None:
    clipboard = build_clipboard()

    assert clipboard is not None


def test_build_clipboard_prefers_system_clipboard_when_available(monkeypatch) -> None:
    fake_clipboard = FakeClipboard()

    monkeypatch.setattr(
        "trans_cli.tui2.clipboard.import_module",
        lambda name: type("M", (), {"PyperclipClipboard": lambda: fake_clipboard})
        if name == "prompt_toolkit.clipboard.pyperclip"
        else __import__(name),
    )

    clipboard = build_clipboard()

    assert clipboard is fake_clipboard


def test_build_clipboard_falls_back_to_in_memory_when_system_clipboard_missing(monkeypatch) -> None:
    def fake_import(name: str):
        if name == "prompt_toolkit.clipboard.pyperclip":
            raise ModuleNotFoundError(name)
        return __import__(name, fromlist=["*"])

    monkeypatch.setattr("trans_cli.tui2.clipboard.import_module", fake_import)

    clipboard = build_clipboard()

    assert type(clipboard).__name__ == "InMemoryClipboard"


def test_build_clipboard_does_not_swallow_unexpected_constructor_errors(monkeypatch) -> None:
    def fake_import(name: str):
        if name == "prompt_toolkit.clipboard.pyperclip":
            class BrokenPyperclipClipboard:
                def __init__(self) -> None:
                    raise RuntimeError("unexpected clipboard failure")

            return type("M", (), {"PyperclipClipboard": BrokenPyperclipClipboard})
        return __import__(name, fromlist=["*"])

    monkeypatch.setattr("trans_cli.tui2.clipboard.import_module", fake_import)

    try:
        build_clipboard()
    except RuntimeError as exc:
        assert str(exc) == "unexpected clipboard failure"
    else:
        raise AssertionError("build_clipboard() unexpectedly swallowed RuntimeError")

from __future__ import annotations

from base64 import b64encode
from importlib import import_module
from typing import Protocol


class TextClipboard(Protocol):
    def set_text(self, text: str) -> None: ...


class TerminalOutput(Protocol):
    def write_raw(self, data: str) -> None: ...

    def flush(self) -> None: ...


def build_clipboard():
    try:
        pyperclip_module = import_module("prompt_toolkit.clipboard.pyperclip")
        return pyperclip_module.PyperclipClipboard()
    except ModuleNotFoundError:
        clipboard_module = import_module("prompt_toolkit.clipboard")
        return clipboard_module.InMemoryClipboard()


def copy_via_osc52(text: str, output: TerminalOutput) -> None:
    payload = b64encode(text.encode("utf-8")).decode("ascii")
    output.flush()
    output.write_raw(f"\x1b]52;c;{payload}\x07")
    output.flush()

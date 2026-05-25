from __future__ import annotations

from importlib import import_module
from typing import Protocol


class TextClipboard(Protocol):
    def set_text(self, text: str) -> None: ...


def build_clipboard():
    try:
        pyperclip_module = import_module("prompt_toolkit.clipboard.pyperclip")
        return pyperclip_module.PyperclipClipboard()
    except ModuleNotFoundError:
        clipboard_module = import_module("prompt_toolkit.clipboard")
        return clipboard_module.InMemoryClipboard()

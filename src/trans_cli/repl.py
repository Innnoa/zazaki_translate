import sys
from typing import TextIO

from trans_cli.backend import DependencyMissingError, ModelMissingError, TranslationRuntimeError
from trans_cli.core import SUPPORTED_LANGUAGES


def _opposite_language(language_code: str) -> str:
    return "en" if language_code == "zh" else "zh"


def _unsupported_language_message(language_code: str) -> str | None:
    if language_code in SUPPORTED_LANGUAGES:
        return None
    return f"Unsupported language: {language_code}. Use zh or en."


def handle_command(
    command: str,
    from_code: str | None,
    to_code: str | None,
    auto_mode: bool,
) -> tuple[str | None, str | None, bool, str | None, bool]:
    if command in {":q", ":quit", ":exit"}:
        return from_code, to_code, auto_mode, None, True
    if command == ":auto":
        return None, None, True, "Auto detection enabled.", False
    if command == ":swap":
        if auto_mode or (from_code, to_code) == ("en", "zh"):
            next_from, next_to = "zh", "en"
        else:
            next_from, next_to = "en", "zh"
        return next_from, next_to, False, f"Direction set to {next_from} -> {next_to}.", False
    if command.startswith(":from "):
        next_from = command.split(maxsplit=1)[1]
        if message := _unsupported_language_message(next_from):
            return from_code, to_code, auto_mode, message, False
        next_to = _opposite_language(next_from)
        return next_from, next_to, False, f"Direction set to {next_from} -> {next_to}.", False
    if command.startswith(":to "):
        next_to = command.split(maxsplit=1)[1]
        if message := _unsupported_language_message(next_to):
            return from_code, to_code, auto_mode, message, False
        next_from = _opposite_language(next_to)
        return next_from, next_to, False, f"Direction set to {next_from} -> {next_to}.", False
    return from_code, to_code, auto_mode, f"Unknown command: {command}", False


def run_repl(
    translator,
    from_code: str | None = None,
    to_code: str | None = None,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> int:
    current_from = from_code
    current_to = to_code
    auto_mode = from_code is None and to_code is None

    while True:
        try:
            line = stdin.readline()
        except KeyboardInterrupt:
            stdout.write("\n")
            return 130
        if not line:
            break

        text = line.strip()
        if not text:
            continue

        if text.startswith(":"):
            current_from, current_to, auto_mode, message, should_exit = handle_command(
                text,
                current_from,
                current_to,
                auto_mode,
            )
            if message:
                stdout.write(message + "\n")
            if should_exit:
                break
            continue

        if auto_mode:
            try:
                result = translator.translate(text)
            except KeyboardInterrupt:
                stdout.write("\n")
                return 130
            except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
                stdout.write(str(exc) + "\n")
                continue
        else:
            try:
                result = translator.translate(text, current_from, current_to)
            except KeyboardInterrupt:
                stdout.write("\n")
                return 130
            except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
                stdout.write(str(exc) + "\n")
                continue
        stdout.write(result + "\n")

    return 0

import argparse
import sys
from typing import Sequence, TextIO

from trans_cli.backend import (
    ArgosTranslator,
    DependencyMissingError,
    ModelMissingError,
    TranslationRuntimeError,
)
from trans_cli.repl import run_repl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trans")
    parser.add_argument("text", nargs="?")
    parser.add_argument("-f", "--from-lang", dest="from_lang", choices=["zh", "en"])
    parser.add_argument("-t", "--to-lang", dest="to_lang", choices=["zh", "en"])
    parser.add_argument("--install-models", action="store_true")
    parser.add_argument("--tui", action="store_true")
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
    translator=None,
    tui_runner=None,
) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    if translator is None:
        translator = ArgosTranslator()

    try:
        if args.install_models:
            translator.install_default_models()
            stdout.write("Installed zh <-> en models.\n")
            return 0

        if args.text:
            stdout.write(translator.translate(args.text, args.from_lang, args.to_lang) + "\n")
            return 0

        if args.tui or sys.stdin.isatty():
            if tui_runner is None:
                from trans_cli.tui2.app import run_tui

                tui_runner = run_tui
            return tui_runner(translator)

        return run_repl(translator, args.from_lang, args.to_lang, sys.stdin, stdout)
    except KeyboardInterrupt:
        stderr.write("\n")
        return 130
    except (DependencyMissingError, ModelMissingError, TranslationRuntimeError) as exc:
        stderr.write(str(exc) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

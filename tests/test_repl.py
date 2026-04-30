from io import StringIO

from trans_cli.repl import run_repl
from trans_cli.repl import handle_command


class FakeTranslator:
    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
    ) -> str:
        if from_code is None and to_code is None:
            from_code, to_code = ("zh", "en") if any("\u4e00" <= ch <= "\u9fff" for ch in text) else ("en", "zh")
        return f"{from_code}->{to_code}:{text}"


class InterruptingInput:
    def readline(self) -> str:
        raise KeyboardInterrupt


def test_repl_translates_input_and_exits() -> None:
    stdin = StringIO("hello\n:q\n")
    stdout = StringIO()

    exit_code = run_repl(FakeTranslator(), None, None, stdin, stdout)

    assert exit_code == 0
    assert "en->zh:hello" in stdout.getvalue()


def test_repl_swap_sets_manual_direction() -> None:
    stdin = StringIO(":swap\nhello\n:q\n")
    stdout = StringIO()

    run_repl(FakeTranslator(), None, None, stdin, stdout)

    output = stdout.getvalue()
    assert "Direction set to zh -> en." in output
    assert "zh->en:hello" in output


def test_handle_from_rejects_unsupported_language_without_changing_state() -> None:
    state = handle_command(":from ja", "en", "zh", False)

    assert state == (
        "en",
        "zh",
        False,
        "Unsupported language: ja. Use zh or en.",
        False,
    )


def test_handle_to_rejects_unsupported_language_without_changing_state() -> None:
    state = handle_command(":to ja", "zh", "en", False)

    assert state == (
        "zh",
        "en",
        False,
        "Unsupported language: ja. Use zh or en.",
        False,
    )


def test_repl_handles_keyboard_interrupt_without_traceback() -> None:
    stdout = StringIO()

    exit_code = run_repl(FakeTranslator(), None, None, InterruptingInput(), stdout)

    assert exit_code == 130
    assert stdout.getvalue() == "\n"


def test_repl_handles_keyboard_interrupt_during_translation_without_traceback() -> None:
    class InterruptingTranslator:
        def translate(
            self,
            text: str,
            from_code: str | None = None,
            to_code: str | None = None,
        ) -> str:
            raise KeyboardInterrupt

    stdin = StringIO("字符限制\n")
    stdout = StringIO()

    exit_code = run_repl(InterruptingTranslator(), None, None, stdin, stdout)

    assert exit_code == 130
    assert stdout.getvalue() == "\n"

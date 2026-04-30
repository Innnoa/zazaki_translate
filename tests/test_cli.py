from io import StringIO

from trans_cli.cli import build_parser, main


class FakeTranslator:
    def __init__(self) -> None:
        self.installed = False

    def install_default_models(self) -> None:
        self.installed = True

    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
    ) -> str:
        return f"{from_code or 'auto'}->{to_code or 'auto'}:{text}"


def test_parser_accepts_install_models_flag() -> None:
    args = build_parser().parse_args(["--install-models"])
    assert args.install_models is True


def test_parser_accepts_tui_flag() -> None:
    args = build_parser().parse_args(["--tui"])
    assert args.tui is True


def test_main_translates_single_input() -> None:
    stdout = StringIO()

    exit_code = main(["hello"], stdout=stdout, translator=FakeTranslator())

    assert exit_code == 0
    assert stdout.getvalue().strip() == "auto->auto:hello"


def test_main_launches_tui_with_injected_runner() -> None:
    launched = []

    def fake_tui_runner(translator) -> int:
        launched.append(translator)
        return 7

    translator = FakeTranslator()

    exit_code = main(["--tui"], translator=translator, tui_runner=fake_tui_runner)

    assert exit_code == 7
    assert launched == [translator]


def test_main_installs_models() -> None:
    stdout = StringIO()
    translator = FakeTranslator()

    exit_code = main(["--install-models"], stdout=stdout, translator=translator)

    assert exit_code == 0
    assert translator.installed is True
    assert "Installed zh <-> en models." in stdout.getvalue()


def test_main_handles_keyboard_interrupt_during_single_translation() -> None:
    class InterruptingTranslator(FakeTranslator):
        def translate(
            self,
            text: str,
            from_code: str | None = None,
            to_code: str | None = None,
        ) -> str:
            raise KeyboardInterrupt

    stdout = StringIO()
    stderr = StringIO()

    exit_code = main(["hello"], stdout=stdout, stderr=stderr, translator=InterruptingTranslator())

    assert exit_code == 130
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == "\n"

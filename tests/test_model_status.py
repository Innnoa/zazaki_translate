from trans_cli.backend import DependencyMissingError, ModelMissingError
from trans_cli.model_status import ModelPairStatus, get_model_statuses, install_default_models


class FakeLanguage:
    def __init__(self, code: str, translations: set[str] | None = None) -> None:
        self.code = code
        self.translations = translations or set()

    def get_translation(self, other: "FakeLanguage"):
        return object() if other.code in self.translations else None


class FakeTranslateModule:
    def __init__(self, languages: list[FakeLanguage]) -> None:
        self.languages = languages

    def get_installed_languages(self) -> list[FakeLanguage]:
        return self.languages


class FakeTranslator:
    def __init__(self, translate_module=None, error: Exception | None = None) -> None:
        self.translate_module = translate_module
        self.error = error
        self.installed = False

    def _load_modules(self):
        if self.error:
            raise self.error
        return object(), self.translate_module

    def install_default_models(self) -> None:
        self.installed = True


def test_get_model_statuses_reports_installed_and_missing_pairs() -> None:
    zh = FakeLanguage("zh", {"en"})
    en = FakeLanguage("en")
    translator = FakeTranslator(FakeTranslateModule([zh, en]))

    statuses = get_model_statuses(translator)

    assert statuses == [
        ModelPairStatus("zh", "en", "installed", ""),
        ModelPairStatus("en", "zh", "missing", "Run `trans --install-models` first."),
    ]


def test_get_model_statuses_reports_runtime_dependency_missing() -> None:
    translator = FakeTranslator(error=DependencyMissingError("missing runtime"))

    statuses = get_model_statuses(translator)

    assert statuses == [
        ModelPairStatus("zh", "en", "runtime-missing", "missing runtime"),
        ModelPairStatus("en", "zh", "runtime-missing", "missing runtime"),
    ]


def test_get_model_statuses_reports_backend_error() -> None:
    translator = FakeTranslator(error=ModelMissingError("boom"))

    statuses = get_model_statuses(translator)

    assert statuses[0].status == "error"
    assert statuses[0].message == "boom"


def test_install_default_models_delegates_to_translator() -> None:
    translator = FakeTranslator(FakeTranslateModule([]))

    install_default_models(translator)

    assert translator.installed is True

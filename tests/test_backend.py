import pytest

from trans_cli.backend import ArgosTranslator, DependencyMissingError, ModelMissingError


class FakeTranslation:
    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    def translate(self, text: str) -> str:
        return f"{self.prefix}:{text}"


class FakeLanguage:
    def __init__(self, code: str) -> None:
        self.code = code
        self.translations: dict[str, FakeTranslation] = {}

    def get_translation(self, other: "FakeLanguage") -> FakeTranslation | None:
        return self.translations.get(other.code)


class FakePackageRecord:
    def __init__(self, from_code: str, to_code: str, path: str) -> None:
        self.from_code = from_code
        self.to_code = to_code
        self.path = path

    def download(self) -> str:
        return self.path


class FakePackageModule:
    def __init__(self) -> None:
        self.updated = False
        self.installed_paths: list[str] = []
        self.available_packages = [
            FakePackageRecord("zh", "en", "/tmp/zh_en.argosmodel"),
            FakePackageRecord("en", "zh", "/tmp/en_zh.argosmodel"),
        ]

    def update_package_index(self) -> None:
        self.updated = True

    def get_available_packages(self) -> list[FakePackageRecord]:
        return self.available_packages

    def install_from_path(self, path: str) -> None:
        self.installed_paths.append(path)


class FakeTranslateModule:
    def __init__(self, languages: list[FakeLanguage]) -> None:
        self.languages = languages

    def get_installed_languages(self) -> list[FakeLanguage]:
        return self.languages


def test_argos_translator_uses_resolved_direction() -> None:
    zh = FakeLanguage("zh")
    en = FakeLanguage("en")
    en.translations["zh"] = FakeTranslation("en->zh")
    translator = ArgosTranslator(
        package_module=FakePackageModule(),
        translate_module=FakeTranslateModule([zh, en]),
    )

    assert translator.translate("hello") == "en->zh:hello"


def test_argos_translator_raises_install_hint_when_model_is_missing() -> None:
    zh = FakeLanguage("zh")
    en = FakeLanguage("en")
    translator = ArgosTranslator(
        package_module=FakePackageModule(),
        translate_module=FakeTranslateModule([zh, en]),
    )

    with pytest.raises(ModelMissingError, match="trans --install-models"):
        translator.translate("hello")


def test_argos_translator_dependency_hint_uses_shell_safe_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_argos_module(module_name: str):
        raise ModuleNotFoundError(module_name)

    monkeypatch.setattr("trans_cli.backend.import_module", missing_argos_module)
    translator = ArgosTranslator()

    with pytest.raises(DependencyMissingError, match=r"pip install --no-build-isolation -e '\.\[runtime\]'"):
        translator.translate("hello")


def test_install_default_models_installs_both_pairs() -> None:
    package_module = FakePackageModule()
    translator = ArgosTranslator(
        package_module=package_module,
        translate_module=FakeTranslateModule([]),
    )

    translator.install_default_models()

    assert package_module.updated is True
    assert package_module.installed_paths == [
        "/tmp/zh_en.argosmodel",
        "/tmp/en_zh.argosmodel",
    ]


def test_argos_translator_silences_stanza_warning_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    import logging

    class LoggingAwareTranslation:
        def __init__(self) -> None:
            self.disabled_during_call: bool | None = None

        def translate(self, text: str) -> str:
            self.disabled_during_call = logging.getLogger("stanza").disabled
            return text.upper()

    zh = FakeLanguage("zh")
    en = FakeLanguage("en")
    translation = LoggingAwareTranslation()
    en.translations["zh"] = translation

    stanza_logger = logging.getLogger("stanza")
    previous_disabled = stanza_logger.disabled
    stanza_logger.disabled = False

    translator = ArgosTranslator(
        package_module=FakePackageModule(),
        translate_module=FakeTranslateModule([zh, en]),
    )
    result = translator.translate("hello")

    assert result == "HELLO"
    assert translation.disabled_during_call is True
    assert stanza_logger.disabled is False
    stanza_logger.disabled = previous_disabled


def test_argos_translator_retries_with_single_segment_fallback_on_not_a_string() -> None:
    class FailingTranslation:
        def __init__(self) -> None:
            self.underlying = object()

        def translate(self, text: str) -> str:
            raise TypeError("not a string")

    class TrackingTranslator(ArgosTranslator):
        def __init__(self) -> None:
            super().__init__()
            self.fallback_calls: list[tuple[object, str]] = []

        def _find_translation(self, from_code: str, to_code: str):
            return FailingTranslation()

        def _translate_with_single_segment_fallback(self, translation, text: str) -> str:
            self.fallback_calls.append((translation, text))
            return "safe-result"

    translator = TrackingTranslator()

    assert translator.translate("参数比较") == "safe-result"
    assert translator.fallback_calls


def test_argos_translator_can_use_single_segment_fast_path() -> None:
    class TrackingTranslator(ArgosTranslator):
        def __init__(self) -> None:
            super().__init__()
            self.fallback_calls: list[tuple[object, str]] = []

        def _find_translation(self, from_code: str, to_code: str):
            return object()

        def _translate_with_single_segment_fallback(self, translation, text: str) -> str:
            self.fallback_calls.append((translation, text))
            return "fast-result"

    translator = TrackingTranslator()

    assert translator.translate("参数比较", fast_single_segment=True) == "fast-result"
    assert translator.fallback_calls


def test_argos_translator_retries_with_single_segment_fallback_on_stanza_ssl_error() -> None:
    class FakeStanzaSSLError(Exception):
        __module__ = "requests.exceptions"

    class FailingTranslation:
        def translate(self, text: str) -> str:
            raise FakeStanzaSSLError(
                "HTTPSConnectionPool(host='raw.githubusercontent.com', port=443): "
                "Max retries exceeded with url: "
                "/stanfordnlp/stanza-resources/main/resources_1.10.0.json",
            )

    class TrackingTranslator(ArgosTranslator):
        def __init__(self) -> None:
            super().__init__()
            self.fallback_calls: list[tuple[object, str]] = []

        def _find_translation(self, from_code: str, to_code: str):
            return FailingTranslation()

        def _translate_with_single_segment_fallback(self, translation, text: str) -> str:
            self.fallback_calls.append((translation, text))
            return "safe-result"

    translator = TrackingTranslator()

    assert translator.translate("参数比较") == "safe-result"
    assert translator.fallback_calls


def test_argos_translator_retries_with_single_segment_fallback_on_stanza_read_only_resource_error() -> None:
    class FailingTranslation:
        def translate(self, text: str) -> str:
            raise OSError(
                "[Errno 30] Read-only file system: "
                "'/home/user/.local/share/argos-translate/packages/translate-en_zh/stanza/tmpabc'",
            )

    class TrackingTranslator(ArgosTranslator):
        def __init__(self) -> None:
            super().__init__()
            self.fallback_calls: list[tuple[object, str]] = []

        def _find_translation(self, from_code: str, to_code: str):
            return FailingTranslation()

        def _translate_with_single_segment_fallback(self, translation, text: str) -> str:
            self.fallback_calls.append((translation, text))
            return "safe-result"

    translator = TrackingTranslator()

    assert translator.translate("hello") == "safe-result"
    assert translator.fallback_calls


def test_argos_translator_reraises_other_type_errors() -> None:
    class FailingTranslation:
        def translate(self, text: str) -> str:
            raise TypeError("boom")

    class TrackingTranslator(ArgosTranslator):
        def _find_translation(self, from_code: str, to_code: str):
            return FailingTranslation()

    translator = TrackingTranslator()

    with pytest.raises(TypeError, match="boom"):
        translator.translate("参数比较")

from importlib import import_module
from contextlib import contextmanager

from trans_cli.core import resolve_direction


_SENTENCE_BOUNDARY_RESOURCE_MARKERS = (
    "stanza-resources",
    "argos-translate/packages",
    "raw.githubusercontent.com",
    "Read-only file system",
    "resources.json",
    "resources_1.",
)


class DependencyMissingError(RuntimeError):
    """Raised when optional runtime dependencies are not installed."""


class ModelMissingError(RuntimeError):
    """Raised when a required translation model is not installed."""

    def with_install_hint(self) -> "ModelMissingError":
        return ModelMissingError(f"{self.args[0]} Run `trans --install-models` first.")


class TranslationRuntimeError(RuntimeError):
    """Raised when the translation backend fails unexpectedly."""


class ArgosTranslator:
    def __init__(self, package_module=None, translate_module=None) -> None:
        self._package_module = package_module
        self._translate_module = translate_module

    def _load_modules(self) -> tuple[object, object]:
        if self._package_module is None or self._translate_module is None:
            try:
                package_module = import_module("argostranslate.package")
                translate_module = import_module("argostranslate.translate")
            except ModuleNotFoundError as exc:
                raise DependencyMissingError(
                    "Missing runtime dependency `argostranslate`. "
                    "Run `pip install --no-build-isolation -e '.[runtime]'` first.",
                ) from exc
            self._package_module = package_module
            self._translate_module = translate_module
        return self._package_module, self._translate_module

    @contextmanager
    def _silence_stanza_logging(self):
        logging_module = import_module("logging")
        logger_names = ("stanza", "stanza.resources.common")
        previous_states = []

        for logger_name in logger_names:
            logger = logging_module.getLogger(logger_name)
            previous_states.append((logger, logger.disabled))
            logger.disabled = True

        try:
            yield
        finally:
            for logger, previous_disabled in previous_states:
                logger.disabled = previous_disabled

    def _find_translation(self, from_code: str, to_code: str):
        _, translate_module = self._load_modules()
        languages = translate_module.get_installed_languages()
        from_language = next((language for language in languages if language.code == from_code), None)
        to_language = next((language for language in languages if language.code == to_code), None)

        if from_language is None or to_language is None:
            raise ModelMissingError(f"Missing translation model for {from_code} -> {to_code}.").with_install_hint()

        translation = from_language.get_translation(to_language)
        if translation is None:
            raise ModelMissingError(f"Missing translation model for {from_code} -> {to_code}.").with_install_hint()
        return translation

    def _translate_with_single_segment_fallback(self, translation, text: str) -> str:
        package_translation = getattr(translation, "underlying", translation)
        translator = getattr(package_translation, "translator", None)

        if translator is None and hasattr(package_translation, "pkg"):
            ctranslate2_module = import_module("ctranslate2")
            settings_module = import_module("argostranslate.settings")
            model_path = str(package_translation.pkg.package_path / "model")
            translator = ctranslate2_module.Translator(
                model_path,
                device=settings_module.device,
                inter_threads=settings_module.inter_threads,
                intra_threads=settings_module.intra_threads,
                compute_type=settings_module.compute_type,
            )
            package_translation.translator = translator

        package = getattr(package_translation, "pkg", None)
        tokenizer = getattr(package, "tokenizer", None)
        if translator is None or tokenizer is None:
            raise TranslationRuntimeError(
                "Translation backend failed unexpectedly and fallback is unavailable.",
            )

        tokenized = [tokenizer.encode(text)]
        translated_batches = translator.translate_batch(
            tokenized,
            target_prefix=[[package.target_prefix]] if getattr(package, "target_prefix", "") else None,
            replace_unknowns=True,
            max_batch_size=1,
            batch_type="tokens",
            beam_size=1,
            num_hypotheses=1,
            length_penalty=0.2,
            return_scores=True,
        )

        first_hypothesis = translated_batches[0].hypotheses[0]
        return tokenizer.decode(first_hypothesis)

    def _iter_exception_chain(self, exc: Exception):
        seen_ids: set[int] = set()
        current: Exception | None = exc

        while current is not None and id(current) not in seen_ids:
            yield current
            seen_ids.add(id(current))
            current = current.__cause__ if current.__cause__ is not None else current.__context__

    def _should_retry_with_single_segment_fallback(self, exc: Exception) -> bool:
        if isinstance(exc, TypeError):
            return str(exc) == "not a string"

        for candidate in self._iter_exception_chain(exc):
            module_name = type(candidate).__module__
            if module_name.startswith(("requests.", "urllib3.")):
                return True
            if type(candidate).__name__ == "ResourcesFileNotFoundError":
                return True
            if any(marker in str(candidate) for marker in _SENTENCE_BOUNDARY_RESOURCE_MARKERS):
                return True

        return False

    def translate(
        self,
        text: str,
        from_code: str | None = None,
        to_code: str | None = None,
        *,
        fast_single_segment: bool = False,
    ) -> str:
        actual_from, actual_to = resolve_direction(text, from_code, to_code)
        translation = self._find_translation(actual_from, actual_to)
        if fast_single_segment:
            try:
                return self._translate_with_single_segment_fallback(translation, text)
            except TranslationRuntimeError:
                pass
        with self._silence_stanza_logging():
            try:
                return translation.translate(text)
            except Exception as exc:
                if not self._should_retry_with_single_segment_fallback(exc):
                    raise
                return self._translate_with_single_segment_fallback(translation, text)

    def _install_pair(self, package_module, available_packages, from_code: str, to_code: str) -> None:
        package = next(
            (
                candidate
                for candidate in available_packages
                if candidate.from_code == from_code and candidate.to_code == to_code
            ),
            None,
        )
        if package is None:
            raise ModelMissingError(f"No downloadable package found for {from_code} -> {to_code}.")
        package_module.install_from_path(package.download())

    def install_default_models(self) -> None:
        package_module, _ = self._load_modules()
        package_module.update_package_index()
        available_packages = package_module.get_available_packages()
        self._install_pair(package_module, available_packages, "zh", "en")
        self._install_pair(package_module, available_packages, "en", "zh")

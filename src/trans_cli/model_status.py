from __future__ import annotations

from dataclasses import dataclass

from trans_cli.backend import DependencyMissingError


MODEL_PAIRS = (("zh", "en"), ("en", "zh"))


@dataclass(frozen=True)
class ModelPairStatus:
    from_code: str
    to_code: str
    status: str
    message: str


def _has_translation(languages, from_code: str, to_code: str) -> bool:
    from_language = next((language for language in languages if language.code == from_code), None)
    to_language = next((language for language in languages if language.code == to_code), None)
    if from_language is None or to_language is None:
        return False
    return from_language.get_translation(to_language) is not None


def get_model_statuses(translator) -> list[ModelPairStatus]:
    try:
        _, translate_module = translator._load_modules()
        languages = translate_module.get_installed_languages()
    except DependencyMissingError as exc:
        return [
            ModelPairStatus(from_code, to_code, "runtime-missing", str(exc))
            for from_code, to_code in MODEL_PAIRS
        ]
    except Exception as exc:
        return [
            ModelPairStatus(from_code, to_code, "error", str(exc))
            for from_code, to_code in MODEL_PAIRS
        ]

    return [
        ModelPairStatus(
            from_code,
            to_code,
            "installed" if _has_translation(languages, from_code, to_code) else "missing",
            "" if _has_translation(languages, from_code, to_code) else "Run `trans --install-models` first.",
        )
        for from_code, to_code in MODEL_PAIRS
    ]


def install_default_models(translator) -> None:
    translator.install_default_models()

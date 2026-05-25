from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


THEMES = {"latte", "frappe", "macchiato", "mocha"}
DIRECTIONS = {"auto", "zh-en", "en-zh"}
STARTUP_PAGES = {"translate"}


@dataclass(frozen=True)
class TransConfig:
    theme: str = "mocha"
    default_direction: str = "auto"
    save_history: bool = True
    startup_page: str = "translate"


def default_config_path() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "trans" / "config.toml"
    return Path.home() / ".config" / "trans" / "config.toml"


def _validated_string(data: dict[str, Any], key: str, allowed: set[str], default: str) -> str:
    value = data.get(key, default)
    if isinstance(value, str) and value in allowed:
        return value
    return default


def load_config(path: Path | None = None) -> TransConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return TransConfig()

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return TransConfig()

    save_history = data.get("save_history", True)
    if not isinstance(save_history, bool):
        save_history = True

    return TransConfig(
        theme=_validated_string(data, "theme", THEMES, "mocha"),
        default_direction=_validated_string(data, "default_direction", DIRECTIONS, "auto"),
        save_history=save_history,
        startup_page=_validated_string(data, "startup_page", STARTUP_PAGES, "translate"),
    )


def save_config(config: TransConfig, path: Path | None = None) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "\n".join(
            [
                f'theme = "{config.theme}"',
                f'default_direction = "{config.default_direction}"',
                f"save_history = {str(config.save_history).lower()}",
                f'startup_page = "{config.startup_page}"',
                "",
            ],
        ),
        encoding="utf-8",
    )

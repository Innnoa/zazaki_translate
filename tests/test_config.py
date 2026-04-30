from pathlib import Path

from trans_cli.config import TransConfig, default_config_path, load_config, save_config


def test_load_config_returns_defaults_when_file_is_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.toml")

    assert config == TransConfig()


def test_load_config_uses_valid_values_and_ignores_invalid_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                'theme = "latte"',
                'default_direction = "ja-en"',
                "save_history = false",
                'startup_page = "models"',
            ],
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.theme == "latte"
    assert config.default_direction == "auto"
    assert config.save_history is False
    assert config.startup_page == "models"


def test_save_config_round_trips_values(tmp_path: Path) -> None:
    config_path = tmp_path / "nested" / "config.toml"
    expected = TransConfig(
        theme="macchiato",
        default_direction="zh-en",
        save_history=False,
        startup_page="history",
    )

    save_config(expected, config_path)

    assert load_config(config_path) == expected


def test_default_config_path_uses_xdg_config_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert default_config_path() == tmp_path / "trans" / "config.toml"

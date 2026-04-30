from trans_cli.tui.theme import CATPPUCCIN_FLAVORS, REQUIRED_TOKENS, build_css, get_palette


def test_all_catppuccin_flavors_are_available() -> None:
    assert set(CATPPUCCIN_FLAVORS) == {"latte", "frappe", "macchiato", "mocha"}


def test_each_flavor_has_required_tokens() -> None:
    for flavor in CATPPUCCIN_FLAVORS:
        palette = get_palette(flavor)
        assert REQUIRED_TOKENS <= set(palette)


def test_unknown_flavor_falls_back_to_mocha() -> None:
    assert get_palette("unknown") == get_palette("mocha")


def test_build_css_uses_palette_colors() -> None:
    css = build_css("mocha")

    assert "#1e1e2e" in css
    assert "Screen" in css
    assert "#89b4fa" in css

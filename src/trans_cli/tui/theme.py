from __future__ import annotations


REQUIRED_TOKENS = {
    "base",
    "mantle",
    "crust",
    "surface0",
    "surface1",
    "text",
    "subtext0",
    "blue",
    "mauve",
    "green",
    "yellow",
    "red",
    "peach",
}


CATPPUCCIN_FLAVORS: dict[str, dict[str, str]] = {
    "latte": {
        "base": "#eff1f5",
        "mantle": "#e6e9ef",
        "crust": "#dce0e8",
        "surface0": "#ccd0da",
        "surface1": "#bcc0cc",
        "text": "#4c4f69",
        "subtext0": "#6c6f85",
        "blue": "#1e66f5",
        "mauve": "#8839ef",
        "green": "#40a02b",
        "yellow": "#df8e1d",
        "red": "#d20f39",
        "peach": "#fe640b",
    },
    "frappe": {
        "base": "#303446",
        "mantle": "#292c3c",
        "crust": "#232634",
        "surface0": "#414559",
        "surface1": "#51576d",
        "text": "#c6d0f5",
        "subtext0": "#a5adce",
        "blue": "#8caaee",
        "mauve": "#ca9ee6",
        "green": "#a6d189",
        "yellow": "#e5c890",
        "red": "#e78284",
        "peach": "#ef9f76",
    },
    "macchiato": {
        "base": "#24273a",
        "mantle": "#1e2030",
        "crust": "#181926",
        "surface0": "#363a4f",
        "surface1": "#494d64",
        "text": "#cad3f5",
        "subtext0": "#a5adcb",
        "blue": "#8aadf4",
        "mauve": "#c6a0f6",
        "green": "#a6da95",
        "yellow": "#eed49f",
        "red": "#ed8796",
        "peach": "#f5a97f",
    },
    "mocha": {
        "base": "#1e1e2e",
        "mantle": "#181825",
        "crust": "#11111b",
        "surface0": "#313244",
        "surface1": "#45475a",
        "text": "#cdd6f4",
        "subtext0": "#a6adc8",
        "blue": "#89b4fa",
        "mauve": "#cba6f7",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "red": "#f38ba8",
        "peach": "#fab387",
    },
}


def get_palette(flavor: str) -> dict[str, str]:
    return CATPPUCCIN_FLAVORS.get(flavor, CATPPUCCIN_FLAVORS["mocha"])


def build_css(flavor: str) -> str:
    """构建 CSS 样式"""
    palette = get_palette(flavor)
    return f"""
/* 全局样式 */
Screen {{
    background: {palette["base"]};
    color: {palette["text"]};
}}

/* 应用布局 */
#app-shell {{
    layout: horizontal;
    height: 100%;
}}

/* 侧边栏 */
#sidebar {{
    width: 20;
    background: {palette["crust"]};
    border-right: solid {palette["surface0"]};
    padding: 1;
}}

.sidebar-title {{
    color: {palette["blue"]};
    text-style: bold;
    margin-bottom: 1;
}}

.sidebar-hint {{
    color: {palette["subtext0"]};
    margin-top: 1;
}}

/* 导航按钮 */
.nav-button {{
    width: 100%;
    margin-bottom: 1;
    background: {palette["mantle"]};
    border: none;
    padding: 0 1;
}}

.nav-button:hover {{
    background: {palette["surface0"]};
}}

.nav-active {{
    background: {palette["surface0"]};
    color: {palette["mauve"]};
    text-style: bold;
}}

/* 主区域 */
#main {{
    width: 1fr;
    padding: 1 2;
}}

/* 页面 */
.page {{
    display: none;
    height: 100%;
}}

.page-active {{
    display: block;
}}

/* 状态栏 */
.status-bar {{
    background: {palette["mantle"]};
    color: {palette["subtext0"]};
    padding: 0 1;
    margin-bottom: 1;
    border: solid {palette["surface0"]};
}}

/* 面板 */
.panel {{
    background: {palette["mantle"]};
    border: solid {palette["surface1"]};
    padding: 1 2;
}}

/* 视图标题 */
.view-title {{
    color: {palette["blue"]};
    text-style: bold;
    margin-bottom: 1;
}}

/* 翻译面板 */
.translate-panels {{
    height: 1fr;
    margin-bottom: 1;
}}

.source-panel,
.output-panel {{
    width: 1fr;
    height: 100%;
    margin-right: 1;
}}

.source-panel {{
    margin-right: 1;
}}

.panel-title {{
    color: {palette["subtext0"]};
    margin-bottom: 1;
}}

/* 操作按钮 */
.translate-actions {{
    height: 3;
    align: center middle;
}}

.action-button {{
    margin: 0 1;
    background: {palette["surface0"]};
    border: solid {palette["surface1"]};
}}

.action-button:hover {{
    background: {palette["surface1"]};
}}

/* 历史记录 */
.history-item {{
    background: {palette["mantle"]};
    border: solid {palette["surface0"]};
    padding: 1;
    margin-bottom: 1;
}}

.history-item-header {{
    margin-bottom: 1;
}}

.history-time {{
    color: {palette["subtext0"]};
    margin-right: 2;
}}

.history-lang {{
    color: {palette["mauve"]};
}}

.history-item-content {{
    height: auto;
}}

.history-source {{
    width: 1fr;
    margin-right: 1;
}}

.history-arrow {{
    color: {palette["subtext0"]};
    margin-right: 1;
}}

.history-translation {{
    width: 1fr;
}}

/* 设置 */
.setting-label {{
    color: {palette["subtext0"]};
    margin-top: 1;
    margin-bottom: 1;
}}

/* 命令面板 */
.command-palette {{
    width: 60;
    height: auto;
    max-height: 30;
    background: {palette["mantle"]};
    border: solid {palette["surface1"]};
    padding: 1;
    align: center top;
    overlay: screen;
}}

/* 强调色 */
.accent {{
    color: {palette["blue"]};
}}

.success {{
    color: {palette["green"]};
}}

.warning {{
    color: {palette["yellow"]};
}}

.error {{
    color: {palette["red"]};
}}

/* 翻译状态 */
.translate-status {{
    color: {palette["subtext0"]};
    margin-top: 1;
    height: 1;
}}

.status-translating {{
    color: {palette["yellow"]};
}}

.status-success {{
    color: {palette["green"]};
}}

.status-error {{
    color: {palette["red"]};
}}
"""

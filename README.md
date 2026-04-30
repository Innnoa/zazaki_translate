# trans

适用于 `WSL / Linux` 的离线中英命令行翻译。

## 功能

- 默认交互模式
- 支持 `中文 -> 英文`、`英文 -> 中文`
- 默认自动识别中英
- 支持 `-f`、`-t` 强制指定方向
- 首次下载模型，之后离线运行

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install --no-build-isolation -e '.[runtime]'
```

如果你也要跑测试：

```bash
pip install --no-build-isolation -e '.[dev]'
```

如果你要使用 TUI：

```bash
pip install --no-build-isolation -e '.[runtime,tui]'
```

## 说明

`Argos Translate` 的运行时依赖会比较大，首次安装可能会拉取 `torch` 等包，耗时和体积都明显高于普通 CLI 工具。

## 初始化模型

```bash
trans --install-models
```

这一步会下载：

- `zh -> en`
- `en -> zh`

下载完成后，就可以离线使用。

## 用法

进入交互模式：

```bash
trans
```

进入 TUI：

```bash
trans --tui
```

一次性翻译：

```bash
trans "你好，今天怎么样？"
trans "How are you today?"
```

强制方向：

```bash
trans -f zh -t en
trans -f en -t zh "hello"
```

## 交互命令

- `:q` 退出
- `:swap` 切换 `zh -> en` 和 `en -> zh`
- `:from zh` 指定源语言
- `:to en` 指定目标语言
- `:auto` 回到自动识别

## TUI

`trans --tui` 使用 `Textual` 实现，默认使用 `Catppuccin Mocha` 配色，并内置 `Latte / Frappe / Macchiato / Mocha` 四套官方 palette。

第一版 TUI 包含：

- `Translate`：输入、输出、方向切换、翻译
- `History`：本地历史记录与搜索
- `Models`：查看 `zh -> en` / `en -> zh` 模型状态，触发模型安装
- `Settings`：主题、默认方向、历史开关、启动页配置

TUI 支持类 Vim normal-mode 控制：

- `h` / `l`：切换到上一个 / 下一个页面
- `j` / `k`：焦点下移 / 上移
- `i`：聚焦当前页面的输入框
- `Esc`：回到 normal mode
- `Enter`：执行当前页面主动作；在 `Translate` 页执行翻译
- `r`：刷新当前页面
- `s`：交换翻译方向
- `c`：清空输入和输出
- `y`：复制提示
- `q`：退出

本地配置默认路径：

```bash
~/.config/trans/config.toml
```

本地历史默认路径：

```bash
~/.local/state/trans/history.jsonl
```

Arch / zsh 下安装时注意给 extras 加引号：

```bash
pip install --no-build-isolation -e '.[runtime,tui]'
```

## 不安装 console script 时的直接运行方式

```bash
PYTHONPATH=src python -m trans_cli.cli
```

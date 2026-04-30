# CURRENT_TASK

- 日期：2026-04-28
- 状态：已新增 `trans --tui` 基础实现，保留 Textual 运行时安装验证残留

## 目标

创建一个适用于 `WSL Arch` 的离线命令行中英互译工具，默认提供交互式使用体验，并支持单次翻译。

## 范围

- 使用 `Python`
- 使用 `Argos Translate`
- 支持 `zh -> en` 与 `en -> zh`
- 支持自动识别和手动覆盖方向
- 支持首次联网下载模型，之后离线运行

## 验收标准

- 默认交互模式可连续翻译句子
- 单次翻译命令可用
- 方向切换命令可用
- 模型缺失时提示清晰

## 相关文件

- `docs/requirements/2026-04-13-offline-cli-translator.md`
- `docs/plans/2026-04-13-offline-cli-translator-plan.md`
- `pyproject.toml`
- `README.md`
- `src/trans_cli/`
- `tests/`

## 当前状态

- 已完成需求冻结和执行计划
- 已完成 CLI、REPL、方向解析与 Argos 后端包装
- 已完成自动化测试与命令行帮助验证
- 已确认未安装 `runtime` 依赖时，CLI 会给出明确提示
- 已修复 REPL 中 `:from` / `:to` 接受不支持语言码的问题
- 已将缺失 `runtime` 依赖提示改为和 README 一致的 shell-safe 安装命令
- 已完成 Textual + Catppuccin TUI 设计文档与执行计划
- 已新增配置、历史、模型状态、Catppuccin 主题和 `--tui` 懒加载入口
- 已尝试在 `.venv` 安装 `.[dev,tui]` 做真实 TUI 启动验证，但本机代理 `127.0.0.1:7890` 超时，未能下载依赖
- 用户完成 `.venv` 依赖安装后，已确认 `textual 6.12.0` 与 `argostranslate 1.11.0` 可用
- 已修复 `stanza` 首次资源初始化遇到只读模型目录时未进入单段翻译兜底的问题
- 已确认 `.venv` 下 `trans_cli.cli "hello"` 可返回翻译结果，TUI 可通过 Textual `run_test()` 启动
- 已修复 TUI 翻译成功后历史写入只读路径导致动作崩溃/界面卡住的问题
- 已为 TUI 增加 `zh/en` 短句翻译 fast path，绕过 `stanza` 分句初始化以降低中译英交互延迟
- 已将 TUI 翻译动作移入 Textual thread worker，并用 timer 轮询 worker 完成状态，避免主界面在翻译期间卡住
- 已将 TUI 改为真正四页显隐切换，并加入类 Vim normal-mode 控制：`h/l/j/k/i/Esc/Enter/r/s/c/y/q`
- 曾尝试真实安装 `argostranslate`，但其依赖链体积很大，已停止安装进程

## 下一步

- 用户若要在本机直接使用翻译能力，执行 `pip install --no-build-isolation -e '.[runtime]'`
- 用户若要使用 TUI，执行 `pip install --no-build-isolation -e '.[runtime,tui]'`
- 然后执行 `trans --install-models`
- 若需要，我可以继续帮你做 `pacman/AUR` 级别的安装脚本或 shell alias

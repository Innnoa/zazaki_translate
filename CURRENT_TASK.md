# CURRENT_TASK

- 日期：2026-05-22
- 状态：在 `terminal-workbench-replatform` worktree 中已完成 `tui2` 结构清理收尾，旧 `Textual` `tui/` 代码与测试已删除；`app.py` 已收敛为入口与 shell 装配层，聚焦回归与类型检查已通过

## 目标

为 `trans` 设计并执行一套新的终端内翻译工作台，放弃当前 `Textual` 多页 TUI，改为更极简、更专业的单页工作台产品形态。

当前直接目标：

- 维持 `prompt_toolkit + Rich` 单页 `tui2` workbench 作为当前终端工作台实现
- 保持 `app.py` 只承担入口与 shell 装配职责，其余控制、运行时、剪贴板与按键绑定逻辑留在专属模块
- 以聚焦测试、CLI 回归、PTY smoke 与 focused pyright 结果作为本轮结构清理完成证据

## 范围

- 保持终端内工具形态
- 使用 `prompt_toolkit + Rich`
- 实现真实可交互的单页 workbench，而不只是 state/helpers
- 去掉 `Ctrl+P` 命令面板控制模型
- 将状态栏提示收敛为只显示 `Ctrl+Y Copy Result`
- 保留 `Settings` / `Models` 内部能力，但先不在状态栏暴露
- 在 runtime 可用后，再切 `CLI` 并退场旧 `Textual`
- 本轮允许修改 `terminal-workbench-replatform` worktree 下的 `tui2`、依赖声明、测试，以及必要的主仓状态文件

## 验收标准

- 新 `tui2` 不只是静态 viewer，而是可输入、可自动翻译、可复制结果的工作台
- 状态栏不再显示 `F2/F3/Ctrl+R/Ctrl+D` 提示
- 状态栏只保留 `Ctrl+Y Copy Result`
- `Ctrl+Y` 优先写入系统剪贴板桥接；当无内容或复制失败时，状态栏给出轻量可见反馈
- `CLI` 只在新 runtime 真正可用后才切换过去
- 旧 `Textual` 只在新 runtime 与 CLI cutover 都验证通过后才退场
- 修订后的 plan 与 spec 一致

## 相关文件

- `docs/superpowers/specs/2026-05-22-terminal-workbench-replatform-design.md`
- `docs/superpowers/plans/2026-05-22-terminal-workbench-replatform.md`
- `docs/superpowers/plans/2026-05-22-tui2-structure-cleanup.md`
- `/home/zazaki/Projects/trans/.worktrees/terminal-workbench-replatform`

## 当前状态

- 已确认用户希望保留终端内形态，不转桌面 GUI 或 Web UI
- 已确认主界面为单页工作台，视觉语言为 `极简专业`
- 已确认放弃 `Ctrl+P` 命令面板
- 已确认新底层方向为 `prompt_toolkit + Rich`
- 已确认 `Settings` 与 `Models` 能力暂时保留，但不再暴露在状态栏提示中
- 已确认状态栏只保留一个提示：`Ctrl+Y Copy Result`
- 已完成可交互 `tui2` runtime、自动翻译、模态切换、后台 warmup 与 `warming up / ready` 显示
- 已完成 `tui2` 结构清理：`app.py` 现仅负责 entrypoint + shell assembly
- 已拆出 `controller.py`、`runtime.py`、`clipboard.py`、`bindings.py`，分别承接控制流、warmup/debounce、剪贴板桥接与按键绑定职责
- 已定位 `Ctrl+Y` 根因：默认 `Application().clipboard` 为 `InMemoryClipboard`；系统命令 `wl-copy/xclip/xsel/pbcopy` 缺失；此前环境缺少依赖声明导致未稳定接入系统剪贴板桥
- 当前 worktree 已补 `clipboard.py::build_clipboard()`：优先 `PyperclipClipboard`，失败时仅在缺少系统剪贴板模块时回退 `InMemoryClipboard`
- 当前 `.venv` 已安装 `pyperclip 1.11.0`，且 `pyperclip.determine_clipboard()` 返回 WSL 剪贴板后端
- 已补 `Ctrl+Y` 复制结果的可见反馈：`copied` / `nothing to copy` / `clipboard unavailable`
- 已将 `pyperclip>=1.11,<2` 加入 `pyproject.toml` 的 `dev` 与 `tui` extras
- 已验证 `prompt_toolkit.clipboard.pyperclip.PyperclipClipboard` 可经 `pyperclip` 真实写入当前环境可用的剪贴板桥接
- 已完成 PTY smoke：确认渲染出翻译结果、显示 `copied` 状态、系统剪贴板读回结果，且进程以 `0` 退出

## 已完成验证

- `PYTHONDONTWRITEBYTECODE=1 "/home/zazaki/Projects/trans/.venv/bin/python" -m pytest tests/test_tui2_app.py tests/test_tui2_render.py tests/test_tui2_actions.py -q` → `43 passed`
- `PYTHONDONTWRITEBYTECODE=1 "/home/zazaki/Projects/trans/.venv/bin/python" -m pytest tests/test_tui2_app.py tests/test_tui2_state.py tests/test_tui2_actions.py tests/test_tui2_render.py tests/test_tui2_controller.py tests/test_tui2_runtime.py tests/test_tui2_clipboard.py tests/test_tui2_bindings.py -q` → `61 passed`
- `PYTHONDONTWRITEBYTECODE=1 "/home/zazaki/Projects/trans/.venv/bin/python" -m pytest tests/test_cli.py -q` → `7 passed`
- `PYTHONDONTWRITEBYTECODE=1 "/home/zazaki/Projects/trans/.venv/bin/python" -m pytest tests/test_tui2_app.py tests/test_tui2_state.py tests/test_tui2_actions.py tests/test_tui2_render.py tests/test_tui2_controller.py tests/test_tui2_runtime.py tests/test_tui2_clipboard.py tests/test_tui2_bindings.py tests/test_cli.py -q` → `68 passed`
- `"/home/zazaki/Projects/trans/.venv/bin/python" - <<'PY' ... PyperclipClipboard ... pyperclip.paste() ... PY` → 成功读回 `tui2-copy-check-你好`
- `pyright src/trans_cli/tui2/app.py src/trans_cli/tui2/controller.py src/trans_cli/tui2/runtime.py src/trans_cli/tui2/clipboard.py src/trans_cli/tui2/bindings.py` → `0 errors, 0 warnings, 0 informations`
- `ruff / mypy` 仍未在当前环境提供可运行命令；本轮未取得这两项额外检查证据

## 下一步

- `tui2` 结构清理已全部完成
- 旧 `Textual` `tui/` 代码与测试已从文件系统和 git index 中删除
- `src/trans.egg-info/*` 仍为旧构建产物，建议在做任何提交前先执行 `pip install -e '.[dev,tui]'` 重新生成
- 若准备公开提交，需先整理暂存区（当前 `tui2/` 文件仍为 untracked）并补 `repo-audit`

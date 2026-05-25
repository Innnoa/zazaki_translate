# DECISIONS

## 2026-04-13: 离线翻译方案选用 Python CLI + Argos Translate

- 结论：命令行工具使用 `Python` 实现，运行时翻译引擎使用 `Argos Translate`
- 原因：
  - 用户目标是 `WSL Arch` 下可直接使用的离线中英互译
  - 需求重点是“整句可用”和“交互式命令行”，不是最高精度
  - `Argos Translate` 已有现成模型安装与本地推理路径，适合快速落地
- 影响：
  - 首次运行前需要额外安装 `runtime` 依赖并下载模型
  - 翻译质量以日常句子够用为主，不追求在线服务级别效果

## 2026-04-13: 自动识别只覆盖中英二选一

- 结论：自动识别规则保持简单，只判断“是否包含明显中文字符”
- 原因：
  - 当前功能范围仅覆盖 `zh <-> en`
  - 引入完整语言检测会增加依赖和复杂度，但对当前目标收益有限
- 影响：
  - 混合语言输入可能需要手动使用 `-f`、`-t` 或交互命令覆盖

## 2026-04-13: Argos 作为可选 runtime extra 暴露

- 结论：`argostranslate` 不放在基础依赖中，而是放到 `.[runtime]`
- 原因：
  - 实测其依赖链会拉取较大的运行时组件，默认安装成本过高
  - 基础项目结构、测试和 CLI 壳层不应被重型运行时依赖阻塞
- 影响：
  - 用户实际使用翻译能力前，需要执行 `pip install --no-build-isolation -e '.[runtime]'`
  - 未安装 runtime 时，CLI 会输出明确提示

## 2026-04-20: `stanza` 分句资源下载失败时退回单段翻译

- 结论：当 `Argos -> stanza` 在首次分句时因 `requests/urllib3` 资源下载错误失败，后端不再把异常直接抛到 CLI，而是退回现有单段翻译兜底
- 原因：
  - 当前工具目标包含“模型下载完成后尽量离线可用”
  - `stanza` 会在缺少本地 `resources.json` 时额外访问 `raw.githubusercontent.com`，这不应让普通翻译直接崩溃
- 影响：
  - 遇到这类网络/资源初始化问题时，短句和普通交互仍可继续翻译
  - 多句长文本在兜底路径下可能少了分句优化，但可用性优先
  - 若 `stanza` 尝试在只读模型目录下创建临时资源目录失败，也进入同一单段翻译兜底

## 2026-04-28: TUI 采用 Textual + Catppuccin 官方 palette

- 结论：TUI 作为 `trans --tui` 增强入口提供，使用 `Textual` 实现，默认主题为 `Catppuccin Mocha`
- 原因：
  - 用户希望 Arch 工具链视觉主题统一
  - 完整 TUI 需要页面、快捷键、布局和状态反馈，`Textual` 比手写 curses 更适合维护
  - 现有 CLI / REPL 已可用，不应被 TUI 风险影响
- 影响：
  - `textual` 放在可选 `.[tui]` extra 中，普通 CLI 安装不增加依赖
  - TUI 颜色集中在主题模块，页面不得自行乱配主色
  - 使用 TUI 需要执行 `pip install --no-build-isolation -e '.[runtime,tui]'`
  - 历史写入失败只显示状态提示，不阻断翻译结果展示
  - TUI 短句翻译默认使用单段 fast path，减少 `stanza` 分句初始化带来的中译英延迟；普通 CLI/REPL 保持原路径
  - TUI 翻译动作必须在 Textual thread worker 中执行，不能阻塞主界面消息循环
  - TUI 采用类 Vim normal-mode 控制，页面用 `h/l` 切换，编辑输入用 `i` 进入焦点、`Esc` 返回 normal mode

## 2026-05-22: 新终端工作台改为 `prompt_toolkit + Rich` 单页 `tui2`

- 结论：新的终端工作台不再沿用 `Textual` 多页架构，改为基于 `prompt_toolkit + Rich` 的单页 `tui2` workbench；`Settings` / `Models` 保留为轻量 modal surface，`Ctrl+P` 命令面板不再保留为主控制模型
- 原因：
  - 当前产品目标是“终端内、极简专业、以输入和结果为中心”的翻译工作台，旧 `Textual` 页面化结构和侧边栏导航过重
  - `prompt_toolkit` 更贴合文本输入、焦点控制、按键绑定和 debounce 调度；`Rich` 更适合紧凑输出与状态表现
  - 迁移期采用并行 `tui2` 模块族，能在不立即破坏现有 CLI/REPL 路径的前提下验证真实 runtime 与交互体验
- 影响：
  - `src/trans_cli/tui2/` 成为新 TUI 的主实现面，职责边界按 `app/state/actions/render/modals/theme` 拆分
  - `--tui` 路径已切到 `trans_cli.tui2.app.run_tui`
  - `tui` extra 需要显式包含 `prompt_toolkit`、`rich`，以及用于系统剪贴板桥接的 `pyperclip`
  - 旧 `Textual` 实现与相关测试只在新 runtime 完整验证后再退场，不在本决策点同步删除
  - 2026-05-25 更新：新 `tui2` runtime 已完整验证（全量 pytest 101 passed、PTY smoke 通过、pyright 清洁），旧 `Textual` `tui/` 代码与测试已正式删除

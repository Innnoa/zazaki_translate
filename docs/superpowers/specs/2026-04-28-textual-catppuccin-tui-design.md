# Textual Catppuccin TUI Design

- 日期：2026-04-28
- 状态：待用户审核

## 目标

为现有 `trans` 离线中英翻译工具新增一个完整 TUI 入口：`trans --tui`。现有单次翻译和纯文本 REPL 保持不变，TUI 作为增强界面提供统一的 Catppuccin 视觉风格、翻译工作区、历史记录、模型管理和设置页。

## 用户选择

- 启动方式：新增 `trans --tui`
- TUI 方向：完整应用形态，左侧导航，主区域切换页面
- 框架：`Textual`
- 默认主题：`Catppuccin Mocha`
- 主题一致性：使用 Catppuccin 官方 palette token，不临时拼色
- 第一版功能范围：翻译、历史、模型、设置全部包含，但每个模块保持 MVP 可用范围

## 非目标

- 不替换现有 CLI 和 REPL
- 不引入在线翻译服务
- 不实现复杂插件系统
- 不自动解析用户全局终端、Neovim、Kitty、Alacritty 配置
- 不在第一版实现多语言扩展，仍只支持 `zh` 和 `en`

## 架构

新增 TUI 层位于 `src/trans_cli/tui/`，复用现有 `ArgosTranslator` 和方向解析逻辑。TUI 不直接操作 Argos 内部对象，只通过翻译服务接口调用现有后端。这样可以保留当前测试稳定性，也避免 TUI 代码和翻译引擎耦合。

建议模块边界：

- `src/trans_cli/tui/app.py`：Textual 应用入口、页面切换、全局快捷键
- `src/trans_cli/tui/theme.py`：Catppuccin palette 和 Textual CSS token
- `src/trans_cli/tui/screens.py` 或 `widgets/`：Translate、History、Models、Settings 页面组件
- `src/trans_cli/history.py`：本地 JSONL 历史记录读写与搜索
- `src/trans_cli/config.py`：本地 TOML 配置读写
- `src/trans_cli/model_status.py`：模型状态检查与安装动作封装

## TUI 页面

### Translate

主工作区使用输入/输出双栏。顶部显示当前方向、自动识别状态、模型状态和主题名。支持：

- 输入文本
- 执行翻译
- 自动识别或手动 `zh -> en` / `en -> zh`
- 交换方向
- 清空输入
- 复制输出
- 成功翻译后写入历史

### History

历史页读取本地 JSONL 文件，显示翻译时间、方向、输入摘要和输出摘要。支持：

- 搜索历史
- 选中历史项后回填到 Translate 页
- 清空历史需要二次确认

历史文件建议放在用户配置目录下，例如 `~/.local/state/trans/history.jsonl`。如果环境变量不可用，退回到 `~/.trans/history.jsonl`。

### Models

模型页展示 `zh -> en` 和 `en -> zh` 的状态。第一版只做清晰状态与现有安装流程触发：

- installed
- missing
- runtime dependency missing
- install failed with message

执行安装时复用 `ArgosTranslator.install_default_models()`，并在 TUI 里显示进度消息。真实下载仍然需要联网。

### Settings

设置页写入本地 TOML 配置。第一版支持：

- 默认主题 flavor：`latte`、`frappe`、`macchiato`、`mocha`
- 默认方向：`auto`、`zh-en`、`en-zh`
- 是否保存历史
- 启动时默认打开页面：`translate`、`history`、`models`、`settings`

配置文件建议放在 `~/.config/trans/config.toml`。缺失配置时使用内置默认值，不报错。

## Catppuccin 主题

默认 flavor 为 `Mocha`。实现时把颜色集中在 `theme.py`，通过 token 暴露给 Textual CSS：

- `base`
- `mantle`
- `crust`
- `surface0`
- `surface1`
- `text`
- `subtext0`
- `blue`
- `mauve`
- `green`
- `yellow`
- `red`
- `peach`

所有页面必须复用这些 token。错误、警告、成功、选中态分别使用 `red`、`yellow`、`green`、`mauve/blue`，避免局部页面自行定义额外主色。

## 快捷键

第一版建议：

- `Ctrl+Enter`：翻译
- `Ctrl+L`：清空输入
- `Ctrl+S`：交换方向
- `Ctrl+C`：复制输出
- `F1`：帮助
- `F2`：Translate
- `F3`：History
- `F4`：Models
- `F5`：Settings
- `q`：退出

如果 `Ctrl+C` 与终端中断行为冲突，保留终端默认中断，复制输出改为 `y`。

## 数据流

1. `cli.py` 解析 `--tui`
2. 创建 `ArgosTranslator`
3. 启动 `TransTuiApp`
4. Translate 页调用翻译服务
5. 翻译成功后写入历史
6. Settings 页更新配置文件
7. Theme 模块根据配置提供 Catppuccin CSS

## 错误处理

- 缺少 `argostranslate`：在 TUI 顶部状态和 Models 页显示安装命令
- 缺少模型：提示执行 `trans --install-models` 或在 Models 页安装
- 安装失败：显示异常摘要，不吞掉错误
- 历史或配置写入失败：显示状态提示，但不阻断翻译
- 翻译异常：复用现有后端异常类型并展示用户可读消息

## 测试策略

- 保留现有 CLI / REPL 测试
- 为 `history.py` 添加 JSONL 读写、搜索、损坏行跳过测试
- 为 `config.py` 添加默认值、读取、写入、无效值回退测试
- 为 `theme.py` 添加 Catppuccin flavor token 完整性测试
- 为 `cli.py` 添加 `--tui` 分支测试，使用假 TUI runner 避免启动真实终端 UI
- TUI 组件测试以轻量 smoke 为主，不要求第一版覆盖所有键盘交互

## 验收标准

- `trans --tui` 可启动完整 TUI
- 默认主题是 Catppuccin Mocha
- 设置页可切换 Catppuccin flavor，并持久化
- Translate 页可执行中英翻译，保留现有模型缺失提示
- History 页可查看和搜索历史
- Models 页可显示模型缺失/已安装状态，并能触发安装流程
- Settings 页可保存默认方向、主题、历史开关和启动页
- 现有 `trans "hello"`、`trans`、`trans --install-models` 行为不回退
- 自动化测试通过

## 残留风险

- `Textual` 会新增运行时依赖，安装体积比当前基础 CLI 更大
- TUI 复制到剪贴板在不同终端环境下可能不稳定，第一版可先降级为选中文本复制或状态提示
- Argos 模型安装耗时长，TUI 只能显示进度和状态，不能让下载本身变快
- `Ctrl+Enter` 在部分终端中可能不发送可区分按键，需要实现替代快捷键

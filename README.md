# Trans

Offline Chinese-English command-line translator with modern TUI interface.

## Features

- Fast offline translation using Argos Translate
- Single-page terminal workbench for input and results
- Modal settings and model management from the workbench
- Catppuccin themes and quick keyboard shortcuts

## Installation

```bash
pip install -e '.[tui,runtime]'
```

> **Note:** Argos Translate runtime pulls large dependencies (e.g. `torch`). First install may take a while.

### Initialize models

```bash
trans --install-models
```

Downloads `zh -> en` and `en -> zh` models. After that, everything works offline.

## Usage

### TUI Mode

```bash
trans --tui
```

The TUI is a single-page translation workbench: type in the input pane, review results in the output pane, and open settings or model status without leaving the main screen.

### CLI Mode

```bash
# Interactive mode
trans

# One-shot translation
trans "Hello world"
trans "你好，今天怎么样？"

# Force direction
trans -f en -t zh "Hello"
trans -f zh -t en "你好"
```

### Interactive Commands

| Command | Description |
|---------|-------------|
| `:q` | Quit |
| `:swap` | Swap `zh -> en` / `en -> zh` |
| `:from zh` | Set source language |
| `:to en` | Set target language |
| `:auto` | Return to auto-detect |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F2` | Open settings modal |
| `F3` | Open models modal |
| `Tab` | Toggle focus between input and output |
| `Ctrl+R` | Retry translation for current input |
| `Ctrl+D` | Clear input and output |
| `Esc` | Close the active modal |
| `q` | Quit |

## Themes

Supports all Catppuccin flavors:

- **Latte** (light)
- **Frappe** (medium)
- **Macchiato** (dark)
- **Mocha** (darkest, default)

Switch themes via the settings modal.

## Configuration

Config file: `~/.config/trans/config.toml`
History file: `~/.local/state/trans/history.jsonl`

## Development

```bash
# Install dev dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Run with coverage
pytest --cov=trans_cli
```

## License

MIT

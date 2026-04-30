# Trans

Offline Chinese-English command-line translator with modern TUI interface.

## Features

- Fast offline translation using Argos Translate
- Modern TUI interface with Catppuccin themes
- Vim-style keyboard navigation
- Translation history with search
- Easy model management

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

### Global

| Key | Action |
|-----|--------|
| `h` / `l` | Previous / Next page |
| `j` / `k` | Focus down / up |
| `Ctrl+P` | Command palette |
| `q` | Quit |

### Translate Page

| Key | Action |
|-----|--------|
| `Ctrl+Enter` | Translate |
| `s` | Swap language direction |
| `c` | Clear input |
| `y` | Copy output |
| `Tab` | Toggle focus between input/output |

### History Page

| Key | Action |
|-----|--------|
| `/` | Search |
| `r` | Refresh |

### Models Page

| Key | Action |
|-----|--------|
| `r` | Refresh |
| `i` | Install models |

### Settings Page

| Key | Action |
|-----|--------|
| `s` | Save settings |

## Themes

Supports all Catppuccin flavors:

- **Latte** (light)
- **Frappe** (medium)
- **Macchiato** (dark)
- **Mocha** (darkest, default)

Switch themes via the Settings page or the command palette.

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

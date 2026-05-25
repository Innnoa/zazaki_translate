#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV_PATH:-$SCRIPT_DIR/.venv}"
PYTHON="${PYTHON:-python3}"
BIN_DIR="${HOME}/.local/bin"
TRANS_CMD="${BIN_DIR}/trans"

info() { printf '\033[1;34m→\033[0m %s\n' "$1"; }
err()  { printf '\033[1;31m✗\033[0m %s\n' "$1" >&2; exit 1; }
ok()   { printf '\033[1;32m✓\033[0m %s\n' "$1"; }

# --- check python version ---
info "Checking Python version..."
PY_VER=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo "$PY_VER" | cut -d. -f1)
MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]; }; then
    err "Python >=3.11 required, found $PY_VER"
fi
ok "Python $PY_VER"

# --- create virtual environment ---
if [ ! -d "$VENV" ]; then
    info "Creating virtual environment at $VENV ..."
    "$PYTHON" -m venv "$VENV"
fi
ok "Virtual environment ready"

# --- install package ---
info "Installing zazaki_trans with TUI dependencies..."
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -e "$SCRIPT_DIR[tui]"

# --- verify runtime ---
info "Verifying runtime import..."
if ! "$VENV/bin/python" -c 'import trans_cli.cli' 2>/dev/null; then
    "$VENV/bin/pip" install -e "$SCRIPT_DIR[runtime]"
fi
ok "Package installed"

# --- global command ---
mkdir -p "$BIN_DIR"
rm -f "$TRANS_CMD"

cat > "$TRANS_CMD" <<'SCRIPT'
#!/usr/bin/env bash
exec _TRANS_VENV_/bin/trans "$@"
SCRIPT
sed -i "s|_TRANS_VENV_|$VENV|g" "$TRANS_CMD"
chmod +x "$TRANS_CMD"

# --- ensure ~/.local/bin is in PATH ---
RC_FILE=""
if [ -n "${ZSH_VERSION-}" ] || [ -f "$HOME/.zshrc" ]; then
    RC_FILE="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    RC_FILE="$HOME/.bashrc"
elif [ -f "$HOME/.profile" ]; then
    RC_FILE="$HOME/.profile"
fi

if [ -n "$RC_FILE" ] && ! grep -qF "$BIN_DIR" "$RC_FILE" 2>/dev/null; then
    printf '\n# added by zazaki_trans install\n' >>"$RC_FILE"
    printf 'export PATH="%s:$PATH"\n' "$BIN_DIR" >>"$RC_FILE"
    ok "Added $BIN_DIR to $RC_FILE"
elif echo "$PATH" | grep -qF "$BIN_DIR"; then
    ok "$BIN_DIR already in PATH"
else
    info "Add $BIN_DIR to your PATH manually to use 'trans' globally:"
    printf '    export PATH="%s:$PATH"\n' "$BIN_DIR"
fi

ok "'trans' command ready"
echo ""
echo "──────────────────────────────────────────"
echo "Usage:"
echo "  trans --tui          launch the workbench"
echo "  trans --help          show all options"
echo "  trans 'hello world'   quick translate"
echo "──────────────────────────────────────────"

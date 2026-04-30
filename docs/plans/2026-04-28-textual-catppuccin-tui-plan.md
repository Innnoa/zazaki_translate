# Textual Catppuccin TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `trans --tui`, a Textual-based full TUI for the offline Chinese-English translator with Catppuccin theme, history, model status, and settings.

**Architecture:** Keep the existing CLI, REPL, and Argos backend stable. Add focused support modules for config, history, model status, and Catppuccin tokens, then add a Textual app that consumes those modules. Make Textual an optional `tui` extra and keep automated tests runnable without importing Textual unless the TUI extra is installed.

**Tech Stack:** Python 3.14, argparse, pytest, Textual, Argos Translate, JSONL, TOML via `tomllib` plus lightweight manual writer.

---

**Source Spec:** `docs/superpowers/specs/2026-04-28-textual-catppuccin-tui-design.md`

**Execution Grade:** `L`

**Repository Note:** This workspace is not a git repository, so commit steps are intentionally omitted.

**Verification Commands:**

- `python -m pytest -q`
- `PYTHONPATH=src python -m trans_cli.cli --help`
- `PYTHONPATH=src python -m trans_cli.cli "hello"`
- `PYTHONPATH=src python -m trans_cli.cli --tui` after installing `.[tui]`

**Task 1: Config module**

Files:

- Create: `src/trans_cli/config.py`
- Create: `tests/test_config.py`

Steps:

- [ ] Write tests for default settings, missing config, invalid values, read/write round trip, and XDG path fallback.
- [ ] Implement `TransConfig`, `default_config_path()`, `load_config()`, and `save_config()`.
- [ ] Run `python -m pytest tests/test_config.py -q`.

**Task 2: History module**

Files:

- Create: `src/trans_cli/history.py`
- Create: `tests/test_history.py`

Steps:

- [ ] Write tests for append, newest-first load, search, disabled history, and corrupt JSONL line skipping.
- [ ] Implement `HistoryEntry`, `default_history_path()`, `append_history()`, `load_history()`, `search_history()`, and `clear_history()`.
- [ ] Run `python -m pytest tests/test_history.py -q`.

**Task 3: Catppuccin theme module**

Files:

- Create: `src/trans_cli/tui/__init__.py`
- Create: `src/trans_cli/tui/theme.py`
- Create: `tests/test_theme.py`

Steps:

- [ ] Write tests for all four flavor names and required token completeness.
- [ ] Implement official Catppuccin token dictionaries for `latte`, `frappe`, `macchiato`, and `mocha`.
- [ ] Generate Textual CSS from token dictionaries.
- [ ] Run `python -m pytest tests/test_theme.py -q`.

**Task 4: Model status module**

Files:

- Create: `src/trans_cli/model_status.py`
- Create: `tests/test_model_status.py`

Steps:

- [ ] Write tests for dependency missing, model missing, installed, and install delegation.
- [ ] Implement `ModelPairStatus`, `get_model_statuses()`, and `install_default_models()`.
- [ ] Run `python -m pytest tests/test_model_status.py -q`.

**Task 5: TUI app shell**

Files:

- Create: `src/trans_cli/tui/app.py`
- Create: `tests/test_tui_imports.py`

Steps:

- [ ] Write tests that importing `trans_cli.tui.app` without Textual raises a user-facing optional dependency error.
- [ ] Implement `TransTuiApp` with lazy Textual imports, Catppuccin CSS, navigation placeholders, Translate/History/Models/Settings panels, and core actions.
- [ ] Run `python -m pytest tests/test_tui_imports.py -q`.

**Task 6: CLI integration**

Files:

- Modify: `src/trans_cli/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `pyproject.toml`

Steps:

- [ ] Add tests for `--tui` invoking a fake runner and preserving existing single-shot/REPL behavior.
- [ ] Add `tui = ["textual>=6,<7"]` optional dependency and include it in `dev`.
- [ ] Add `--tui` parser flag and lazy TUI runner hook.
- [ ] Run `python -m pytest tests/test_cli.py -q`.

**Task 7: Documentation and state**

Files:

- Modify: `README.md`
- Modify: `CURRENT_TASK.md`
- Modify: `DECISIONS.md`

Steps:

- [ ] Document Arch install commands for runtime and TUI extras.
- [ ] Document `trans --tui`, Catppuccin flavors, and local config/history paths.
- [ ] Update task state and durable decision log.
- [ ] Run full verification.

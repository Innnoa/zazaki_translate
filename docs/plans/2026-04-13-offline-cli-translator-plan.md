# Offline CLI Translator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python command-line translator for Chinese and English that defaults to an interactive REPL, works offline after model installation, and uses Argos Translate as the local engine.

**Architecture:** Package the tool as a small Python project with a `trans` console script. Keep pure direction/command logic separate from the Argos backend so tests can run without downloading models, then layer CLI and REPL behavior on top of that backend.

**Tech Stack:** Python 3.14, argparse, pytest, Argos Translate

---

**Execution Grade:** `M`

**Repository Note:** This workspace is not a git repository as of 2026-04-13, so commit steps are intentionally omitted.

**Verification Commands:**
- `python -m pytest -q`
- `python -m trans_cli.cli --help`
- `PYTHONPATH=src python -m trans_cli.cli "你好"`

**Rollback Plan:**
- Remove newly added project files if packaging or CLI shape proves wrong.
- Keep Argos-specific code isolated in `src/trans_cli/backend.py` so it can be replaced without rewriting tests.

**Cleanup Expectation:**
- Leave only source, tests, docs, and runtime receipts.
- Do not leave temporary model downloads inside the repository.

### File Map

- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/trans_cli/__init__.py`
- Create: `src/trans_cli/backend.py`
- Create: `src/trans_cli/cli.py`
- Create: `src/trans_cli/core.py`
- Create: `src/trans_cli/repl.py`
- Create: `tests/test_core.py`
- Create: `tests/test_cli.py`
- Create: `tests/test_repl.py`

### Task 1: Scaffold the package and lock pure translation rules with tests

**Files:**
- Create: `pyproject.toml`
- Create: `src/trans_cli/__init__.py`
- Create: `src/trans_cli/core.py`
- Create: `tests/test_core.py`

- [ ] **Step 1: Write the failing core tests**

```python
from trans_cli.core import contains_chinese, resolve_direction


def test_contains_chinese_detects_cjk_text() -> None:
    assert contains_chinese("你好 world") is True
    assert contains_chinese("hello world") is False


def test_resolve_direction_uses_auto_detection() -> None:
    assert resolve_direction("你好", None, None) == ("zh", "en")
    assert resolve_direction("hello", None, None) == ("en", "zh")


def test_resolve_direction_prefers_explicit_flags() -> None:
    assert resolve_direction("hello", "zh", "en") == ("zh", "en")
```

- [ ] **Step 2: Run the core test file and verify it fails**

Run: `python -m pytest tests/test_core.py -q`
Expected: FAIL with `ModuleNotFoundError` or missing symbol errors because the package is not implemented yet

- [ ] **Step 3: Add minimal packaging and core logic**

```toml
[project]
name = "trans"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["argostranslate>=1.11,<2"]
```

```python
SUPPORTED_LANGUAGES = {"zh", "en"}


def contains_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def resolve_direction(text: str, from_code: str | None, to_code: str | None) -> tuple[str, str]:
    if from_code and to_code:
        return from_code, to_code
    if from_code:
        return from_code, "en" if from_code == "zh" else "zh"
    if to_code:
        return "zh" if to_code == "en" else "en", to_code
    return ("zh", "en") if contains_chinese(text) else ("en", "zh")
```

- [ ] **Step 4: Run the core tests again**

Run: `python -m pytest tests/test_core.py -q`
Expected: PASS

### Task 2: Drive REPL commands and single-shot CLI behavior from tests

**Files:**
- Create: `src/trans_cli/repl.py`
- Create: `src/trans_cli/cli.py`
- Create: `tests/test_repl.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing REPL and CLI tests**

```python
from io import StringIO

from trans_cli.cli import build_parser
from trans_cli.repl import run_repl


class FakeTranslator:
    def translate(self, text: str, from_code: str | None = None, to_code: str | None = None) -> str:
        return f"{from_code or 'auto'}->{to_code or 'auto'}:{text}"


def test_repl_translates_input_and_exits() -> None:
    stdin = StringIO("hello\n:q\n")
    stdout = StringIO()
    run_repl(FakeTranslator(), None, None, stdin, stdout)
    assert "en->zh:hello" in stdout.getvalue()


def test_parser_accepts_install_models_flag() -> None:
    args = build_parser().parse_args(["--install-models"])
    assert args.install_models is True
```

- [ ] **Step 2: Run REPL and CLI tests to verify they fail**

Run: `python -m pytest tests/test_repl.py tests/test_cli.py -q`
Expected: FAIL because the REPL and CLI modules do not exist yet

- [ ] **Step 3: Implement the REPL loop and CLI parser**

```python
def run_repl(translator, from_code=None, to_code=None, stdin=sys.stdin, stdout=sys.stdout):
    current_from, current_to, auto_mode = from_code, to_code, from_code is None and to_code is None
    while True:
        line = stdin.readline()
        if not line:
            break
        text = line.strip()
        if text == ":q":
            break
        if text == ":auto":
            current_from, current_to, auto_mode = None, None, True
            continue
        result = translator.translate(text, None if auto_mode else current_from, None if auto_mode else current_to)
        stdout.write(result + "\n")
```

```python
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="trans")
    parser.add_argument("text", nargs="?")
    parser.add_argument("-f", "--from-lang", dest="from_lang", choices=["zh", "en"])
    parser.add_argument("-t", "--to-lang", dest="to_lang", choices=["zh", "en"])
    parser.add_argument("--install-models", action="store_true")
    return parser
```

- [ ] **Step 4: Re-run REPL and CLI tests**

Run: `python -m pytest tests/test_repl.py tests/test_cli.py -q`
Expected: PASS

### Task 3: Implement the Argos backend, model installation path, and user-facing docs

**Files:**
- Create: `src/trans_cli/backend.py`
- Modify: `src/trans_cli/cli.py`
- Modify: `src/trans_cli/repl.py`
- Create: `README.md`

- [ ] **Step 1: Write failing tests for model-missing errors and manual direction commands**

```python
import pytest

from trans_cli.backend import ModelMissingError
from trans_cli.repl import handle_command


def test_handle_swap_turns_auto_into_manual_mode() -> None:
    state = handle_command(":swap", None, None, True)
    assert state == ("zh", "en", False, "Direction set to zh -> en.")


def test_model_missing_error_has_install_hint() -> None:
    error = ModelMissingError("Missing translation model for zh -> en.")
    assert "trans --install-models" in str(error.with_install_hint())
```

- [ ] **Step 2: Run the full test suite and verify the new tests fail**

Run: `python -m pytest -q`
Expected: FAIL because backend exceptions and command handling are incomplete

- [ ] **Step 3: Implement the backend and final CLI flow**

```python
class ModelMissingError(RuntimeError):
    def with_install_hint(self) -> "ModelMissingError":
        return ModelMissingError(f"{self.args[0]} Run `trans --install-models` first.")


class ArgosTranslator:
    def install_default_models(self) -> None:
        for from_code, to_code in (("zh", "en"), ("en", "zh")):
            self._install_pair(from_code, to_code)

    def translate(self, text: str, from_code: str | None = None, to_code: str | None = None) -> str:
        actual_from, actual_to = resolve_direction(text, from_code, to_code)
        if not self.has_pair(actual_from, actual_to):
            raise ModelMissingError(f"Missing translation model for {actual_from} -> {actual_to}.").with_install_hint()
        return self._argos_translate(text, actual_from, actual_to)
```

```python
if args.install_models:
    translator.install_default_models()
    print("Installed zh <-> en models.")
    return 0
if args.text:
    print(translator.translate(args.text, args.from_lang, args.to_lang))
    return 0
return run_repl(translator, args.from_lang, args.to_lang)
```

- [ ] **Step 4: Document setup and usage**

```markdown
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
trans --install-models
trans
```

- [ ] **Step 5: Run verification commands**

Run: `python -m pytest -q`
Expected: PASS

Run: `PYTHONPATH=src python -m trans_cli.cli --help`
Expected: usage text including `--install-models`

Run: `PYTHONPATH=src python -m trans_cli.cli "hello"`
Expected: a clear model-missing error if models are not installed yet, or a translated string if they are installed

### Self-Review

- Spec coverage: the plan covers REPL mode, single-shot mode, auto-detection, manual overrides, model installation, and missing-model guidance.
- Placeholder scan: no `TODO`, `TBD`, or vague “handle later” steps remain.
- Type consistency: `from_lang` and `to_lang` stay aligned across core, CLI, backend, and tests.

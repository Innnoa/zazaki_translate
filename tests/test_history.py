from pathlib import Path

from trans_cli.history import HistoryEntry, append_history, clear_history, load_history, search_history


def test_append_and_load_history_newest_first(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    first = HistoryEntry(
        input_text="hello",
        output_text="你好",
        from_code="en",
        to_code="zh",
        created_at="2026-04-28T10:00:00Z",
    )
    second = HistoryEntry(
        input_text="参数",
        output_text="parameter",
        from_code="zh",
        to_code="en",
        created_at="2026-04-28T10:01:00Z",
    )

    append_history(first, history_path)
    append_history(second, history_path)

    assert load_history(history_path) == [second, first]


def test_append_history_respects_disabled_flag(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    entry = HistoryEntry("hello", "你好", "en", "zh", "2026-04-28T10:00:00Z")

    append_history(entry, history_path, enabled=False)

    assert not history_path.exists()


def test_load_history_skips_corrupt_lines(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    history_path.write_text(
        '{"input_text":"hello","output_text":"你好","from_code":"en","to_code":"zh","created_at":"2026"}\n'
        "not json\n",
        encoding="utf-8",
    )

    entries = load_history(history_path)

    assert len(entries) == 1
    assert entries[0].input_text == "hello"


def test_search_history_matches_input_and_output(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history(HistoryEntry("hello", "你好", "en", "zh", "2026"), history_path)
    append_history(HistoryEntry("offline model", "离线模型", "en", "zh", "2026"), history_path)

    assert [entry.input_text for entry in search_history("模型", history_path)] == ["offline model"]


def test_clear_history_removes_file(tmp_path: Path) -> None:
    history_path = tmp_path / "history.jsonl"
    append_history(HistoryEntry("hello", "你好", "en", "zh", "2026"), history_path)

    clear_history(history_path)

    assert not history_path.exists()

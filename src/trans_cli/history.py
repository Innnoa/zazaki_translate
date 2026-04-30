from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class HistoryEntry:
    input_text: str
    output_text: str
    from_code: str
    to_code: str
    created_at: str


def default_history_path() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / "trans" / "history.jsonl"
    return Path.home() / ".local" / "state" / "trans" / "history.jsonl"


def append_history(entry: HistoryEntry, path: Path | None = None, *, enabled: bool = True) -> None:
    if not enabled:
        return
    history_path = path or default_history_path()
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")


def _entry_from_json_line(line: str) -> HistoryEntry | None:
    try:
        data = json.loads(line)
        return HistoryEntry(
            input_text=str(data["input_text"]),
            output_text=str(data["output_text"]),
            from_code=str(data["from_code"]),
            to_code=str(data["to_code"]),
            created_at=str(data["created_at"]),
        )
    except (KeyError, TypeError, json.JSONDecodeError):
        return None


def load_history(path: Path | None = None, *, limit: int | None = None) -> list[HistoryEntry]:
    history_path = path or default_history_path()
    if not history_path.exists():
        return []

    entries = [
        entry
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if (entry := _entry_from_json_line(line)) is not None
    ]
    newest_first = list(reversed(entries))
    return newest_first[:limit] if limit is not None else newest_first


def search_history(query: str, path: Path | None = None, *, limit: int | None = None) -> list[HistoryEntry]:
    normalized_query = query.casefold()
    entries = [
        entry
        for entry in load_history(path)
        if normalized_query in entry.input_text.casefold()
        or normalized_query in entry.output_text.casefold()
    ]
    return entries[:limit] if limit is not None else entries


def clear_history(path: Path | None = None) -> None:
    history_path = path or default_history_path()
    try:
        history_path.unlink()
    except FileNotFoundError:
        return

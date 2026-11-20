"""Local top-10 board. The file survives restarts."""

from __future__ import annotations

import json
from pathlib import Path


def board_path() -> Path:
    folder = Path.home() / ".dao-den-long"
    folder.mkdir(exist_ok=True)
    return folder / "leaderboard.json"


def valid_name(name: str) -> bool:
    if not 3 <= len(name) <= 12:
        return False
    for char in name:
        if char.isascii() and (char.isalnum() or char == "_"):
            continue
        if char.isalpha():
            continue
        return False
    return True


def load_entries(path: Path | None = None) -> list[dict]:
    file = path or board_path()
    if not file.exists():
        return []
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    entries = data.get("entries", data if isinstance(data, list) else [])
    if not isinstance(entries, list):
        return []
    clean = [item for item in entries if isinstance(item, dict) and "name" in item and "score" in item]
    return rank(clean)


def rank(entries: list[dict]) -> list[dict]:
    ordered = sorted(entries, key=lambda item: (-int(item["score"]), str(item.get("achieved_at", ""))))
    return ordered[:10]


def add_entry(entry: dict, path: Path | None = None) -> list[dict]:
    file = path or board_path()
    entries = load_entries(file)
    entries.append(entry)
    entries = rank(entries)
    file.parent.mkdir(exist_ok=True)
    file.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entries


def export_payload(path: Path | None = None) -> dict:
    return {"entries": load_entries(path)}

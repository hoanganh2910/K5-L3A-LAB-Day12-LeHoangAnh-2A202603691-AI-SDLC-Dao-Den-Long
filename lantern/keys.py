"""Saved key bindings. One key per action."""

from __future__ import annotations

DEFAULT_KEYS = {
    "forward": "w",
    "back": "s",
    "left": "a",
    "right": "d",
    "jump": "space",
    "dash": "left shift",
    "interact": "e",
    "pulse": "f",
    "pause": "escape",
}

LABELS = {
    "forward": "Đi tới",
    "back": "Đi lùi",
    "left": "Đi trái",
    "right": "Đi phải",
    "jump": "Nhảy",
    "dash": "Lướt",
    "interact": "Tương tác",
    "pulse": "Tỏa sáng",
    "pause": "Tạm dừng",
}


def clean_keys(raw: object) -> dict:
    keys = dict(DEFAULT_KEYS)
    if not isinstance(raw, dict):
        return keys
    for action, key in raw.items():
        if action in keys and isinstance(key, str) and key:
            keys[action] = key
    seen: dict[str, str] = {}
    for action, key in list(keys.items()):
        if key in seen:
            keys[action] = DEFAULT_KEYS[action]
        else:
            seen[key] = action
    seen = {}
    for action, key in list(keys.items()):
        if key in seen:
            keys[action] = DEFAULT_KEYS[action]
        seen[key] = action
    return keys


def assign_key(keys: dict, action: str, key: str) -> tuple[dict | None, str | None]:
    if action not in DEFAULT_KEYS:
        return None, "Hành động không có trong danh sách"
    if not key or key in ("mouse1", "mouse2", "mouse3", "scroll up", "scroll down"):
        return None, "Phím này không gán được"
    owner = next((name for name, bound in keys.items() if bound == key and name != action), None)
    if owner is not None:
        return None, f"Phím đã dùng cho {LABELS[owner]}"
    updated = dict(keys)
    updated[action] = key
    return updated, None

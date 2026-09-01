from __future__ import annotations

from typing import Any


CEC_ACTIONS = (
    "focus_next",
    "focus_previous",
    "activate",
    "back",
    "admin",
)

DEFAULT_CEC_KEYMAP: dict[str, list[str]] = {
    "focus_next": ["down", "right"],
    "focus_previous": ["up", "left"],
    "activate": ["select", "enter"],
    "back": ["exit", "return", "backward"],
    "admin": ["root menu", "setup menu", "contents menu", "home"],
}


def normalize_key(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def normalize_keymap(value: Any) -> dict[str, list[str]]:
    if value in (None, ""):
        return {action: list(keys) for action, keys in DEFAULT_CEC_KEYMAP.items()}
    if not isinstance(value, dict):
        raise ValueError("Mappatura telecomando non valida")
    result: dict[str, list[str]] = {}
    assigned: dict[str, str] = {}
    for action in CEC_ACTIONS:
        raw_keys = value.get(action, DEFAULT_CEC_KEYMAP[action])
        if isinstance(raw_keys, str):
            raw_keys = raw_keys.split(",")
        if not isinstance(raw_keys, list):
            raise ValueError(f"Mappatura {action} non valida")
        keys: list[str] = []
        for raw_key in raw_keys:
            key = normalize_key(str(raw_key))
            if key and key not in keys:
                keys.append(key)
        if len(keys) > 20:
            raise ValueError(f"Troppi tasti associati a {action}")
        for key in keys:
            if key in assigned:
                raise ValueError(f"Tasto “{key}” associato sia a {assigned[key]} sia a {action}")
            assigned[key] = action
        result[action] = keys
    return result


def action_for_key(key: str, keymap: dict[str, list[str]]) -> str | None:
    normalized = normalize_key(key)
    for action in CEC_ACTIONS:
        if normalized in keymap.get(action, []):
            return action
    return None

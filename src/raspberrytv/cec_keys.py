from __future__ import annotations

from typing import Any


CEC_ACTIONS = (
    "up",
    "down",
    "left",
    "right",
    "activate",
    "back",
    "admin",
    "color_red",
    "color_green",
    "color_yellow",
    "color_blue",
)

DEFAULT_CEC_KEYMAP: dict[str, list[str]] = {
    "up": ["up"],
    "down": ["down"],
    "left": ["left"],
    "right": ["right"],
    "activate": ["select", "enter"],
    "back": ["exit", "return", "backward"],
    "admin": ["root menu", "setup menu", "contents menu", "home"],
    # HDMI-CEC assigns F1=blue, F2=red, F3=green and F4=yellow.
    # Keep colour aliases too because libCEC/TV vendors do not all print the
    # decoded key name in exactly the same form.
    "color_red": ["f2 (red)", "f2", "red"],
    "color_green": ["f3 (green)", "f3", "green"],
    "color_yellow": ["f4 (yellow)", "f4", "yellow"],
    "color_blue": ["f1 (blue)", "f1", "blue"],
}

CEC_INPUT_MODES = {"focus", "pointer"}
CEC_COLOR_ACTIONS = {"red", "green", "yellow", "blue"}
CEC_SHORTCUTS = {"none", "admin", "site", "back", "reload"}
DEFAULT_CEC_COLOR_ACTIONS = {
    "red": "admin",
    "green": "site",
    "yellow": "reload",
    "blue": "back",
}


def normalize_key(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").split())


def normalize_keymap(value: Any) -> dict[str, list[str]]:
    if value in (None, ""):
        return {action: list(keys) for action, keys in DEFAULT_CEC_KEYMAP.items()}
    if not isinstance(value, dict):
        raise ValueError("Mappatura telecomando non valida")
    value = _migrate_legacy_keymap(value)
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


def _migrate_legacy_keymap(value: dict[str, Any]) -> dict[str, Any]:
    if "focus_next" not in value and "focus_previous" not in value:
        return value
    migrated = dict(value)
    next_keys = migrated.pop("focus_next", [])
    previous_keys = migrated.pop("focus_previous", [])
    if isinstance(next_keys, str):
        next_keys = next_keys.split(",")
    if isinstance(previous_keys, str):
        previous_keys = previous_keys.split(",")
    if isinstance(next_keys, list):
        normalized = [normalize_key(str(key)) for key in next_keys if normalize_key(str(key))]
        migrated.setdefault("down", normalized[:1] or DEFAULT_CEC_KEYMAP["down"])
        migrated.setdefault("right", normalized[1:] or DEFAULT_CEC_KEYMAP["right"])
    if isinstance(previous_keys, list):
        normalized = [normalize_key(str(key)) for key in previous_keys if normalize_key(str(key))]
        migrated.setdefault("up", normalized[:1] or DEFAULT_CEC_KEYMAP["up"])
        migrated.setdefault("left", normalized[1:] or DEFAULT_CEC_KEYMAP["left"])
    return migrated


def normalize_input_mode(value: Any) -> str:
    mode = str(value or "focus").strip().lower()
    if mode not in CEC_INPUT_MODES:
        raise ValueError("Modalità telecomando non valida")
    return mode


def normalize_color_actions(value: Any) -> dict[str, str]:
    if value in (None, ""):
        return dict(DEFAULT_CEC_COLOR_ACTIONS)
    if not isinstance(value, dict):
        raise ValueError("Scorciatoie colorate non valide")
    result: dict[str, str] = {}
    for color in CEC_COLOR_ACTIONS:
        shortcut = str(value.get(color, DEFAULT_CEC_COLOR_ACTIONS[color])).strip().lower()
        if shortcut not in CEC_SHORTCUTS:
            raise ValueError(f"Funzione del tasto {color} non valida")
        result[color] = shortcut
    return result


def action_for_key(key: str, keymap: dict[str, list[str]]) -> str | None:
    normalized = normalize_key(key)
    for action in CEC_ACTIONS:
        if normalized in keymap.get(action, []):
            return action
    return None


def operation_for_key(key: str, keymap: dict[str, list[str]], input_mode: str) -> str | None:
    action = action_for_key(key, keymap)
    mode = normalize_input_mode(input_mode)
    if mode == "focus" and action in {"down", "right"}:
        return "focus_next"
    if mode == "focus" and action in {"up", "left"}:
        return "focus_previous"
    if mode == "pointer" and action in {"up", "down", "left", "right"}:
        return f"pointer_{action}"
    if mode == "pointer" and action == "activate":
        return "pointer_click"
    return action

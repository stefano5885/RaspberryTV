#!/usr/bin/python3
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path


PROFILE = Path(os.getenv(
    "RASPBERRYTV_BROWSER_PREFERENCES",
    "/var/lib/raspberrytv/browser-profile/Default/Preferences",
))


def nested(data: dict, *keys: str) -> dict:
    current = data
    for key in keys:
        value = current.get(key)
        if not isinstance(value, dict):
            value = {}
            current[key] = value
        current = value
    return current


def main() -> None:
    try:
        preferences = json.loads(PROFILE.read_text(encoding="utf-8"))
        if not isinstance(preferences, dict):
            preferences = {}
    except (FileNotFoundError, json.JSONDecodeError):
        preferences = {}

    brave = nested(preferences, "brave")
    brave["ad_default"] = True
    brave["cosmetic_filtering_migration"] = True

    exceptions = nested(preferences, "profile", "content_settings", "exceptions")
    cosmetic = nested(exceptions, "cosmeticFilteringV2")
    cosmetic["*,*"] = {
        "expiration": "0",
        "last_modified": str(int((time.time() + 11644473600) * 1_000_000)),
        "model": 0,
        "setting": {"cosmeticFilteringV2": 1},
    }

    PROFILE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".Preferences.", dir=PROFILE.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(preferences, stream, ensure_ascii=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, PROFILE)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()

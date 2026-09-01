from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import JsonFile


DEFAULT_CEC_DIAGNOSTICS: dict[str, Any] = {
    "status": "unknown",
    "message": "Bridge CEC non ancora avviato",
    "sequence": 0,
    "last_key": "",
    "last_action": "",
    "updated_at": None,
    "events": [],
}


class CecDiagnostics:
    def __init__(self, state_dir: Path, limit: int = 100):
        self.file = JsonFile(state_dir / "cec-diagnostics.json", DEFAULT_CEC_DIAGNOSTICS, mode=0o644)
        self.limit = limit
        self._lock = threading.RLock()

    def read(self) -> dict[str, Any]:
        return self.file.read()

    def record(
        self,
        kind: str,
        message: str,
        *,
        status: str | None = None,
        key: str = "",
        action: str = "",
        level: str = "info",
    ) -> dict[str, Any]:
        with self._lock:
            data = self.file.read()
            sequence = int(data.get("sequence", 0)) + 1
            now = datetime.now(timezone.utc).isoformat()
            event = {
                "sequence": sequence,
                "at": now,
                "kind": str(kind)[:32],
                "level": level if level in {"info", "warning", "error"} else "info",
                "message": " ".join(str(message).split())[:400],
            }
            if key:
                event["key"] = str(key)[:100]
                data["last_key"] = str(key)[:100]
            if action:
                event["action"] = str(action)[:40]
                data["last_action"] = str(action)[:40]
            events = data.get("events", [])
            if not isinstance(events, list):
                events = []
            data.update(sequence=sequence, updated_at=now, message=event["message"])
            if status:
                data["status"] = status
            data["events"] = [*events, event][-self.limit :]
            self.file.write(data)
            return data

    def clear(self) -> None:
        with self._lock:
            data = self.file.read()
            data["events"] = []
            self.file.write(data)

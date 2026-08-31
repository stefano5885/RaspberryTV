from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from .config import JsonFile


class SystemController:
    def __init__(self, state_dir: Path, helper: str | None = None):
        self.state_dir = state_dir
        self.helper = helper or os.getenv("RASPBERRYTV_CONTROL", "/usr/local/sbin/raspberrytv-control")

    def _invoke(self, action: str) -> None:
        command = [self.helper, action]
        if os.geteuid() != 0:
            command.insert(0, "sudo")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"Comando di sistema non disponibile: {action}") from exc
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or f"Errore {action}").strip())

    def set_browser_target(self, target: str) -> None:
        if target not in {"site", "admin"}:
            raise ValueError("Destinazione browser non valida")
        JsonFile(self.state_dir / "state.json", {}).update(browser_target=target)
        self._invoke("browser-restart")

    def request_wifi(self, ssid: str, password: str) -> None:
        ssid = ssid.strip()
        if not ssid or len(ssid) > 32 or "\x00" in ssid:
            raise ValueError("SSID non valido")
        if len(password) < 8 or len(password) > 63:
            raise ValueError("La password Wi-Fi deve contenere da 8 a 63 caratteri")
        JsonFile(self.state_dir / "wifi-request.json", {}).write({"ssid": ssid, "password": password})
        self._invoke("wifi-apply")

    def request_update(self, action: str, tag: str = "") -> None:
        if action not in {"update", "rollback"}:
            raise ValueError("Azione update non valida")
        if tag and StableTag.fullmatch(tag) is None:
            raise ValueError("Tag release non valido")
        JsonFile(self.state_dir / "update-request.json", {}).write({"action": action, "tag": tag})
        JsonFile(self.state_dir / "update-status.json", {}).write({
            "status": "queued",
            "message": "Aggiornamento in coda" if action == "update" else "Rollback in coda",
            "tag": tag,
        })
        JsonFile(self.state_dir / "state.json", {}).update(browser_target="update")
        self._invoke("browser-update")
        self._invoke("update-start")

    def reboot(self) -> None:
        self._invoke("reboot")


class _StableTag:
    def fullmatch(self, value: str):
        import re
        return re.fullmatch(r"v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value)


StableTag = _StableTag()

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

from .config import ConfigStore, JsonFile
from .update import StableVersion, latest_stable


LOGGER = logging.getLogger("raspberrytv.update")


class ReleaseManager:
    def __init__(self, store: ConfigStore | None = None, code_root: Path | None = None):
        self.store = store or ConfigStore()
        self.code_root = code_root or Path(os.getenv("RASPBERRYTV_CODE_ROOT", "/opt/raspberrytv"))
        self.mirror = self.code_root / "repository.git"
        self.releases = self.code_root / "releases"
        self.current = self.code_root / "current"
        self.status_file = self.store.update_file
        self.request_file = JsonFile(self.store.state_dir / "update-request.json", {})
        self.release_state = JsonFile(self.store.state_dir / "release-state.json", {})

    def _status(self, status: str, message: str = "", **extra) -> None:
        self.status_file.write({
            "status": status,
            "message": message,
            "at": datetime.now(timezone.utc).isoformat(),
            **extra,
        })

    def _git_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        deploy_key = Path("/etc/raspberrytv-git/deploy_key")
        if deploy_key.is_file():
            known_hosts = self.store.state_dir / "git-known-hosts"
            env["GIT_SSH_COMMAND"] = (
                f"ssh -i {deploy_key} -o IdentitiesOnly=yes "
                f"-o UserKnownHostsFile={known_hosts} "
                "-o StrictHostKeyChecking=accept-new -o BatchMode=yes"
            )
        return env

    def _run(self, command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=self._git_env(),
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"Comando fallito: {command[0]} ({detail[-500:]})")
        return result

    def _prepare_mirror(self, repository_url: str) -> None:
        self.code_root.mkdir(parents=True, exist_ok=True)
        self.releases.mkdir(parents=True, exist_ok=True)
        if not self.mirror.exists():
            self._run(["git", "clone", "--mirror", repository_url, str(self.mirror)], timeout=300)
        else:
            self._run(["git", "--git-dir", str(self.mirror), "remote", "set-url", "origin", repository_url])
            self._run(["git", "--git-dir", str(self.mirror), "fetch", "--prune", "--tags", "origin"], timeout=300)

    def _tags(self) -> list[str]:
        output = self._run(
            ["git", "--git-dir", str(self.mirror), "tag", "--list"], timeout=30
        ).stdout
        return [line.strip() for line in output.splitlines() if line.strip()]

    def _release_for_tag(self, tag: str) -> Path:
        version = StableVersion.parse(tag)
        if version is None:
            raise ValueError("Sono installabili solo tag SemVer stabili")
        release = self.releases / f"v{version.major}.{version.minor}.{version.patch}"
        if not release.exists():
            self._run(
                [
                    "git", "--git-dir", str(self.mirror), "worktree", "add", "--detach",
                    str(release), tag,
                ],
                timeout=180,
            )
        if not (release / "VERSION").is_file() or not (release / "src" / "raspberrytv").is_dir():
            raise RuntimeError("La release non contiene un'applicazione RaspberryTV valida")
        return release.resolve()

    def _switch(self, release: Path) -> Path | None:
        previous = self.current.resolve() if self.current.exists() else None
        temporary = self.code_root / ".current.next"
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(release, target_is_directory=True)
        os.replace(temporary, self.current)
        return previous

    def _restart(self) -> None:
        self._run(["systemctl", "restart", "raspberrytv-web.service"], timeout=30)
        self._run(["systemctl", "try-restart", "raspberrytv-kiosk.service"], timeout=30)
        self._run(["systemctl", "try-restart", "raspberrytv-cec.service"], timeout=30)

    def _healthy(self, timeout: int = 45, expected_version: str = "") -> bool:
        config = self.store.config_file.read()
        port = int(config.get("port", 8080))
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                version_ok = not expected_version or str(payload.get("version")) == expected_version.removeprefix("v")
                if response.status == 200 and payload.get("ok") and version_ok:
                    return True
            except Exception:
                time.sleep(2)
        return False

    def update(self, requested_tag: str = "") -> None:
        config = self.store.config_file.read()
        repository_url = str(config.get("repository_url", "")).strip()
        if not repository_url:
            raise ValueError("Repository Git non configurato")
        self._status("preparing", "Download metadati Git")
        self._prepare_mirror(repository_url)
        available = latest_stable(self._tags())
        if available is None:
            raise RuntimeError("Nessun tag SemVer stabile disponibile")
        tag = requested_tag or available.tag
        if requested_tag:
            requested = StableVersion.parse(requested_tag)
            if requested is None or requested.tag not in self._tags():
                raise ValueError("Tag richiesto non disponibile")
        release = self._release_for_tag(tag)
        previous = self._switch(release)
        self.release_state.write({
            "active_release": str(release),
            "previous_release": str(previous) if previous else "",
        })
        self._status("activating", f"Attivazione {tag}", tag=tag)
        self._restart()
        if not self._healthy(expected_version=tag):
            if previous and previous.is_dir():
                self._switch(previous)
                self._restart()
                previous_version = (previous / "VERSION").read_text(encoding="utf-8").strip() if (previous / "VERSION").is_file() else ""
                self._healthy(timeout=30, expected_version=previous_version)
                self.release_state.write({
                    "active_release": str(previous),
                    "previous_release": str(release),
                })
            raise RuntimeError("Health check fallito; versione precedente ripristinata")
        self._status("success", f"Release {tag} installata", tag=tag)

    def rollback(self) -> None:
        state = self.release_state.read()
        previous_text = str(state.get("previous_release", ""))
        if not previous_text:
            raise RuntimeError("Nessuna release precedente disponibile")
        previous = Path(previous_text).resolve()
        if self.releases.resolve() not in previous.parents or not previous.is_dir():
            raise RuntimeError("Percorso della release precedente non valido")
        active = self.current.resolve() if self.current.exists() else None
        self._status("rolling_back", f"Ripristino {previous.name}")
        self._switch(previous)
        self.release_state.write({
            "active_release": str(previous),
            "previous_release": str(active) if active else "",
        })
        self._restart()
        expected = (previous / "VERSION").read_text(encoding="utf-8").strip() if (previous / "VERSION").is_file() else ""
        if not self._healthy(expected_version=expected):
            if active and active.is_dir():
                self._switch(active)
                self._restart()
            raise RuntimeError("Il rollback non ha superato l'health check")
        self._status("rolled_back", f"Ripristinata {previous.name}")

    def run_request(self) -> None:
        request = self.request_file.read()
        action = request.get("action")
        if action == "update":
            self.update(str(request.get("tag", "")))
        elif action == "rollback":
            self.rollback()
        else:
            raise ValueError("Nessuna richiesta update valida")


def main() -> None:
    import fcntl

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    manager = ReleaseManager()
    lock_path = manager.store.state_dir / "update.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            manager._status("busy", "Un altro aggiornamento è già in corso")
            raise SystemExit(2)
        try:
            manager.run_request()
        except Exception as exc:
            LOGGER.exception("Aggiornamento fallito")
            manager._status("failed", str(exc))
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

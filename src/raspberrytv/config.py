from __future__ import annotations

import json
import os
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


DEFAULT_CONFIG: dict[str, Any] = {
    "url": "",
    "repository_url": "",
    "bind_host": "0.0.0.0",
    "port": 8080,
    "telegram_chat_id": "",
    "telegram_topic_id": "",
    "telegram_poll_minutes": 0,
}

DEFAULT_STATE: dict[str, Any] = {
    "telegram_offset": 0,
    "last_url_update": None,
    "last_url_previous": "",
    "last_telegram_result": None,
    "browser_target": "site",
}


def validate_url(value: str) -> str:
    value = (value or "").strip()
    if not value or len(value) > 2048 or any(ord(char) < 32 for char in value):
        raise ValueError("URL mancante o non valido")
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"}:
        raise ValueError("Sono ammessi solo URL HTTP o HTTPS")
    if not parts.hostname or parts.username or parts.password:
        raise ValueError("L'URL deve avere un host e non deve contenere credenziali")
    try:
        _ = parts.port
    except ValueError as exc:
        raise ValueError("Porta URL non valida") from exc
    normalized = parts._replace(scheme=parts.scheme.lower(), fragment="")
    return urlunsplit(normalized)


class JsonFile:
    def __init__(self, path: Path, defaults: dict[str, Any] | None = None, mode: int = 0o600):
        self.path = path
        self.defaults = defaults or {}
        self.mode = mode
        self._lock = threading.RLock()

    def read(self) -> dict[str, Any]:
        with self._lock:
            data = deepcopy(self.defaults)
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data.update(loaded)
            except FileNotFoundError:
                pass
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Impossibile leggere {self.path}: {exc}") from exc
            return data

    def write(self, data: dict[str, Any]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            handle, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, self.mode)
                os.replace(temporary, self.path)
            finally:
                try:
                    os.unlink(temporary)
                except FileNotFoundError:
                    pass

    def update(self, **values: Any) -> dict[str, Any]:
        with self._lock:
            data = self.read()
            data.update(values)
            self.write(data)
            return data


class ConfigStore:
    def __init__(self, config_dir: Path | None = None, state_dir: Path | None = None):
        self.config_dir = config_dir or Path(os.getenv("RASPBERRYTV_CONFIG_DIR", "/etc/raspberrytv"))
        self.state_dir = state_dir or Path(os.getenv("RASPBERRYTV_STATE_DIR", "/var/lib/raspberrytv"))
        self.config_file = JsonFile(self.config_dir / "config.json", DEFAULT_CONFIG)
        self.secrets_file = JsonFile(self.config_dir / "secrets.json", {})
        self.state_file = JsonFile(self.state_dir / "state.json", DEFAULT_STATE)
        self.update_file = JsonFile(self.state_dir / "update-status.json", {"status": "idle"})
        self.release_file = JsonFile(self.state_dir / "release-state.json", {})

    def public_config(self) -> dict[str, Any]:
        config = self.config_file.read()
        secrets = self.secrets_file.read()
        config["telegram_token_configured"] = bool(secrets.get("telegram_bot_token"))
        return config

    def telegram_credentials(self) -> tuple[str, str, str]:
        config = self.config_file.read()
        secrets = self.secrets_file.read()
        return (
            str(secrets.get("telegram_bot_token", "")),
            str(config.get("telegram_chat_id", "")),
            str(config.get("telegram_topic_id", "")),
        )

    def set_url(self, value: str) -> tuple[str, str]:
        normalized = validate_url(value)
        config = self.config_file.read()
        previous = str(config.get("url", ""))
        config["url"] = normalized
        self.config_file.write(config)
        return previous, normalized

    def set_telegram(self, token: str | None, chat_id: str, topic_id: str = "") -> None:
        chat_id = str(chat_id).strip()
        topic_id = str(topic_id).strip()
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID è obbligatorio")
        if topic_id and not topic_id.lstrip("-").isdigit():
            raise ValueError("TELEGRAM_TOPIC_ID non valido")
        config = self.config_file.read()
        config.update(telegram_chat_id=chat_id, telegram_topic_id=topic_id)
        self.config_file.write(config)
        if token is not None and token.strip():
            secrets = self.secrets_file.read()
            secrets["telegram_bot_token"] = token.strip()
            self.secrets_file.write(secrets)

from __future__ import annotations

import json
import logging
import mimetypes
import os
import socket
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from . import __version__
from .config import ConfigStore
from .network import network_status
from .system_control import SystemController
from .system_metrics import SystemMetrics
from .telegram_client import TelegramClient, select_latest_url
from .update import UpdateInspector


LOGGER = logging.getLogger("raspberrytv")
ASSET_ROOT = Path(__file__).with_name("web")


class Application:
    def __init__(self, store: ConfigStore | None = None):
        self.store = store or ConfigStore()
        self.system = SystemController(self.store.state_dir)
        self.metrics = SystemMetrics()
        self.updates = UpdateInspector()

    def status(self) -> dict[str, Any]:
        release = self.store.release_file.read()
        return {
            "hostname": socket.gethostname(),
            "version": __version__,
            "config": self.store.public_config(),
            "state": self.store.state_file.read(),
            "update": self.store.update_file.read(),
            "release": {
                "active": Path(str(release.get("active_release", ""))).name,
                "previous": Path(str(release.get("previous_release", ""))).name,
            },
            "network": network_status(),
            "system": self.metrics.read(),
        }

    def refresh_telegram(self) -> dict[str, Any]:
        token, chat_id, topic_id = self.store.telegram_credentials()
        if not token or not chat_id:
            raise ValueError("Configurazione Telegram incompleta")
        state = self.store.state_file.read()
        offset = int(state.get("telegram_offset", 0))
        updates = TelegramClient(token).get_updates(offset=offset)
        selection = select_latest_url(updates, chat_id, topic_id)
        if selection.newest_update_id:
            state["telegram_offset"] = selection.newest_update_id + 1
        now = datetime.now(timezone.utc).isoformat()
        if not selection.url:
            state["last_telegram_result"] = {"at": now, "status": "no_valid_url"}
            self.store.state_file.write(state)
            return {"changed": False, "message": "Nessun nuovo URL valido trovato"}
        previous, current = self.store.set_url(selection.url)
        state.update(
            last_url_update=now,
            last_url_previous=previous,
            last_telegram_result={
                "at": now,
                "status": "updated",
                "message_id": selection.message_id,
                "message_date": selection.message_date,
            },
        )
        self.store.state_file.write(state)
        LOGGER.info("URL aggiornato da Telegram (message_id=%s)", selection.message_id)
        return {"changed": previous != current, "previous": previous, "current": current}


class Handler(BaseHTTPRequestHandler):
    server_version = "RaspberryTV"

    @property
    def application(self) -> Application:
        return self.server.application  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)

    def _json(self, payload: Any, status: int = 200, cors: bool = False) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _text(self, value: str, status: int = 200) -> None:
        body = value.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _asset(self, relative: str) -> None:
        target = (ASSET_ROOT / relative).resolve()
        if ASSET_ROOT.resolve() not in target.parents or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Content-Length non valido") from exc
        if length < 0 or length > 65_536:
            raise ValueError("Richiesta troppo grande")
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as exc:
            raise ValueError("JSON non valido") from exc
        if not isinstance(data, dict):
            raise ValueError("Il corpo deve essere un oggetto JSON")
        return data

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        try:
            return urlsplit(origin).netloc.lower() == self.headers.get("Host", "").lower()
        except ValueError:
            return False

    def do_GET(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        try:
            if path == "/":
                self._asset("index.html")
            elif path == "/loading":
                self._asset("loading.html")
            elif path.startswith("/static/"):
                self._asset(path.removeprefix("/static/"))
            elif path == "/api/health":
                self._json({"ok": True, "version": __version__}, cors=True)
            elif path == "/api/status":
                self._json(self.application.status())
            elif path == "/api/kiosk-target":
                if self.client_address[0] not in {"127.0.0.1", "::1"}:
                    self._json({"error": "Solo accesso locale"}, HTTPStatus.FORBIDDEN)
                    return
                state = self.application.store.state_file.read()
                config = self.application.store.config_file.read()
                target = "http://127.0.0.1:8080/"
                if state.get("browser_target") == "site" and config.get("url"):
                    target = str(config["url"])
                self._text(target)
            elif path == "/api/update/check":
                config = self.application.store.config_file.read()
                self._json(self.application.updates.check(str(config.get("repository_url", "")), __version__))
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, RuntimeError) as exc:
            LOGGER.warning("GET %s: %s", path, exc)
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            LOGGER.exception("Errore GET %s", path)
            self._json({"error": "Errore interno"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if not self._same_origin():
            self._json({"error": "Origine richiesta non consentita"}, HTTPStatus.FORBIDDEN)
            return
        try:
            body = self._body()
            if path == "/api/config/url":
                previous, current = self.application.store.set_url(str(body.get("url", "")))
                self._json({"ok": True, "previous": previous, "current": current})
            elif path == "/api/config/telegram":
                token = body.get("token")
                self.application.store.set_telegram(
                    str(token) if token is not None else None,
                    str(body.get("chat_id", "")),
                    str(body.get("topic_id", "")),
                )
                self._json({"ok": True})
            elif path == "/api/config/repository":
                repository_url = str(body.get("repository_url", "")).strip()
                if not repository_url or len(repository_url) > 2048 or "\x00" in repository_url:
                    raise ValueError("Repository URL non valido")
                self.application.store.config_file.update(repository_url=repository_url)
                self._json({"ok": True})
            elif path == "/api/config/wifi":
                self.application.system.request_wifi(str(body.get("ssid", "")), str(body.get("password", "")))
                self._json({"ok": True, "message": "Configurazione Wi-Fi applicata"})
            elif path == "/api/telegram/refresh":
                self._json({"ok": True, **self.application.refresh_telegram()})
            elif path == "/api/browser/site":
                self.application.system.set_browser_target("site")
                self._json({"ok": True})
            elif path == "/api/browser/admin":
                self.application.system.set_browser_target("admin")
                self._json({"ok": True})
            elif path == "/api/system/reboot":
                self.application.system.reboot()
                self._json({"ok": True})
            elif path == "/api/update/apply":
                self.application.system.request_update("update", str(body.get("tag", "")))
                self._json({"ok": True, "message": "Aggiornamento avviato"}, HTTPStatus.ACCEPTED)
            elif path == "/api/update/rollback":
                self.application.system.request_update("rollback")
                self._json({"ok": True, "message": "Rollback avviato"}, HTTPStatus.ACCEPTED)
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, RuntimeError) as exc:
            LOGGER.warning("POST %s: %s", path, exc)
            self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception:
            LOGGER.exception("Errore POST %s", path)
            self._json({"error": "Errore interno"}, HTTPStatus.INTERNAL_SERVER_ERROR)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], application: Application):
        self.application = application
        super().__init__(address, Handler)


def main() -> None:
    logging.basicConfig(level=os.getenv("RASPBERRYTV_LOG_LEVEL", "INFO"), format="%(levelname)s %(name)s: %(message)s")
    application = Application()
    config = application.store.config_file.read()
    host = str(config.get("bind_host", "0.0.0.0"))
    port = int(config.get("port", 8080))
    server = Server((host, port), application)
    LOGGER.info("RaspberryTV %s in ascolto su %s:%s", __version__, host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

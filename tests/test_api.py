import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from raspberrytv.app import Application, Server
from raspberrytv.config import ConfigStore


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.store = ConfigStore(root / "etc", root / "state")
        self.app = Application(self.store)
        self.server = Server(("127.0.0.1", 0), self.app)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary.cleanup()

    def call(self, path, method="GET", payload=None, headers=None):
        data = json.dumps(payload or {}).encode() if method == "POST" else None
        request = Request(self.base + path, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})})
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())

    def test_health_and_url_api(self):
        status, health = self.call("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["ok"])
        _, system_status = self.call("/api/status")
        self.assertIn("system", system_status)
        self.assertIn("ram", system_status["system"])
        status, saved = self.call("/api/config/url", "POST", {"url": "https://example.com"})
        self.assertEqual(status, 200)
        self.assertEqual(saved["current"], "https://example.com")

    def test_telegram_token_is_not_returned(self):
        self.call("/api/config/telegram", "POST", {"token": "123:secret", "chat_id": "42"})
        _, status = self.call("/api/status")
        serialized = json.dumps(status)
        self.assertNotIn("123:secret", serialized)
        self.assertTrue(status["config"]["telegram_token_configured"])

    def test_rejects_cross_origin_mutation(self):
        with self.assertRaises(HTTPError) as caught:
            self.call("/api/config/url", "POST", {"url": "https://example.com"}, {"Origin": "http://evil.invalid"})
        self.assertEqual(caught.exception.code, 403)
        caught.exception.close()

    def test_status_survives_unreadable_update_metadata(self):
        with (
            patch.object(self.store.release_file, "read", side_effect=RuntimeError("permission denied")),
            patch.object(self.store.update_file, "read", side_effect=RuntimeError("permission denied")),
        ):
            status, payload = self.call("/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(payload["update"]["status"], "unavailable")
        self.assertEqual(payload["release"]["active"], "")

    def test_cec_diagnostics_and_mapping_api(self):
        self.app.cec.record("key", "Tasto select", key="select", action="activate", status="listening")
        status, payload = self.call("/api/cec")
        self.assertEqual(status, 200)
        self.assertEqual(payload["last_key"], "select")
        keymap = payload["keymap"]
        keymap["activate"] = ["ok button"]
        status, saved = self.call("/api/config/cec", "POST", {"keymap": keymap})
        self.assertEqual(status, 200)
        self.assertEqual(saved["keymap"]["activate"], ["ok button"])
        self.call("/api/cec/clear", "POST")
        _, cleared = self.call("/api/cec")
        self.assertEqual(cleared["events"], [])


if __name__ == "__main__":
    unittest.main()

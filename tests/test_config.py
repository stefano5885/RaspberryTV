import os
import stat
import tempfile
import unittest
from pathlib import Path

from raspberrytv.config import ConfigStore, JsonFile, validate_url


class UrlValidationTests(unittest.TestCase):
    def test_accepts_http_and_removes_fragment(self):
        self.assertEqual(validate_url(" HTTPS://Example.com/a#secret "), "https://Example.com/a")

    def test_rejects_credentials_and_other_schemes(self):
        for value in ("ftp://example.com", "https://user:pass@example.com", "javascript:alert(1)", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_url(value)


class PersistenceTests(unittest.TestCase):
    def test_atomic_json_and_secret_redaction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = ConfigStore(root / "etc", root / "state")
            store.set_url("https://example.com/path")
            store.set_telegram("123:secret", "-100123", "7")
            public = store.public_config()
            self.assertTrue(public["telegram_token_configured"])
            self.assertNotIn("telegram_bot_token", public)
            self.assertNotIn("123:secret", str(public))
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(store.secrets_file.path.stat().st_mode), 0o600)

    def test_corrupt_json_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                JsonFile(path).read()


if __name__ == "__main__":
    unittest.main()

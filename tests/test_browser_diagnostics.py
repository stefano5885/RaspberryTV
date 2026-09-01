import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "browser-diagnostics-worker.py"
SPEC = importlib.util.spec_from_file_location("browser_diagnostics_worker", SCRIPT)
assert SPEC and SPEC.loader
WORKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORKER)


class BrowserDiagnosticsWorkerTests(unittest.TestCase):
    def test_consumes_only_allowlisted_internal_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / "request.json"
            with patch.object(WORKER, "REQUEST", request):
                request.write_text(json.dumps({"test": "gpu"}), encoding="utf-8")
                self.assertEqual(WORKER.consume_request(), "gpu")
                self.assertFalse(request.exists())

                request.write_text(json.dumps({"test": "flags"}), encoding="utf-8")
                self.assertEqual(WORKER.consume_request(), "")
                self.assertFalse(request.exists())


if __name__ == "__main__":
    unittest.main()

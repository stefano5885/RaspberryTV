import tempfile
import unittest
from pathlib import Path

from raspberrytv.cec_diagnostics import CecDiagnostics
from raspberrytv.cec_keys import action_for_key, normalize_keymap


class CecKeymapTests(unittest.TestCase):
    def test_default_and_custom_key_mapping(self):
        defaults = normalize_keymap({})
        self.assertEqual(action_for_key("Select", defaults), "activate")
        custom = normalize_keymap({**defaults, "activate": ["ok button"]})
        self.assertEqual(action_for_key("OK_BUTTON", custom), "activate")
        self.assertIsNone(action_for_key("select", custom))

    def test_rejects_ambiguous_mapping(self):
        with self.assertRaises(ValueError):
            normalize_keymap({"focus_next": ["select"], "activate": ["select"]})


class CecDiagnosticsTests(unittest.TestCase):
    def test_records_a_bounded_structured_log(self):
        with tempfile.TemporaryDirectory() as directory:
            diagnostics = CecDiagnostics(Path(directory), limit=2)
            diagnostics.record("bridge", "Avvio", status="starting")
            diagnostics.record("key", "Tasto select", key="select", action="activate")
            data = diagnostics.record("power", "Display acceso", status="listening")
            self.assertEqual(data["status"], "listening")
            self.assertEqual(data["last_key"], "select")
            self.assertEqual(len(data["events"]), 2)
            self.assertEqual(data["events"][-2]["action"], "activate")


if __name__ == "__main__":
    unittest.main()

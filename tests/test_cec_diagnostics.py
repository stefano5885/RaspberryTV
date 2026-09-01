import tempfile
import unittest
from pathlib import Path

from raspberrytv.cec_diagnostics import CecDiagnostics
from raspberrytv.cec_keys import action_for_key, normalize_color_actions, normalize_keymap, operation_for_key


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

    def test_focus_and_pointer_modes(self):
        keymap = normalize_keymap({})
        self.assertEqual(operation_for_key("down", keymap, "focus"), "focus_next")
        self.assertEqual(operation_for_key("down", keymap, "pointer"), "pointer_down")
        self.assertEqual(operation_for_key("select", keymap, "pointer"), "pointer_click")

    def test_coloured_keys_follow_cec_f1_to_f4_mapping(self):
        keymap = normalize_keymap({})
        self.assertEqual(operation_for_key("F1", keymap, "focus"), "color_blue")
        self.assertEqual(operation_for_key("F2", keymap, "focus"), "color_red")
        self.assertEqual(normalize_color_actions({})["red"], "admin")
        with self.assertRaises(ValueError):
            normalize_color_actions({"red": "shell-command"})

    def test_single_legacy_direction_does_not_create_a_duplicate(self):
        migrated = normalize_keymap({"focus_next": ["right"], "focus_previous": ["up"]})
        self.assertEqual(migrated["down"], ["right"])
        self.assertEqual(migrated["right"], [])
        self.assertEqual(migrated["up"], ["up"])
        self.assertEqual(migrated["left"], [])


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

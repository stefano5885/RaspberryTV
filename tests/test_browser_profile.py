import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class BrowserProfileTests(unittest.TestCase):
    def test_enforces_aggressive_brave_shields(self):
        with tempfile.TemporaryDirectory() as directory:
            preferences = Path(directory) / "Default" / "Preferences"
            script = Path(__file__).resolve().parents[1] / "scripts" / "configure-browser-profile.py"
            with patch.dict(os.environ, {"RASPBERRYTV_BROWSER_PREFERENCES": str(preferences)}):
                namespace = runpy.run_path(str(script))
                namespace["main"]()
            data = json.loads(preferences.read_text(encoding="utf-8"))
            self.assertTrue(data["brave"]["ad_default"])
            setting = data["profile"]["content_settings"]["exceptions"]["cosmeticFilteringV2"]["*,*"]
            self.assertEqual(setting["setting"]["cosmeticFilteringV2"], 1)

    def test_managed_policy_disables_p3a_and_forces_adblock(self):
        policy_path = Path(__file__).resolve().parents[1] / "config" / "brave-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertFalse(policy["BraveP3AEnabled"])
        self.assertFalse(policy["BraveStatsPingEnabled"])
        self.assertEqual(policy["DefaultBraveAdblockSetting"], 2)


if __name__ == "__main__":
    unittest.main()

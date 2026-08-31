import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeploymentTests(unittest.TestCase):
    def test_kiosk_does_not_depend_on_git_executable_bits(self):
        unit = (ROOT / "systemd" / "raspberrytv-kiosk.service").read_text(encoding="utf-8")
        start_x = (ROOT / "scripts" / "start-x-kiosk.sh").read_text(encoding="utf-8")
        run_kiosk = (ROOT / "scripts" / "run-kiosk.sh").read_text(encoding="utf-8")
        self.assertIn("ExecStart=/bin/sh ", unit)
        self.assertIn("xinit /bin/sh ", start_x)
        self.assertIn("/usr/bin/python3 ", run_kiosk)

    def test_boot_splash_has_raspberry_pi_kernel_format(self):
        header = (ROOT / "assets" / "boot-splash.tga").read_bytes()[:18]
        self.assertEqual(header[2], 2)  # Uncompressed true-colour TGA.
        width, height = struct.unpack("<HH", header[12:16])
        self.assertEqual((width, height, header[16]), (1920, 1080, 24))

    def test_kiosk_applies_custom_splash_and_disables_standard_layers(self):
        unit = (ROOT / "systemd" / "raspberrytv-kiosk.service").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "configure-boot-splash.sh").read_text(encoding="utf-8")
        self.assertIn("ExecStartPre=+/bin/sh /opt/raspberrytv/current/scripts/configure-boot-splash.sh", unit)
        self.assertIn("configure-splash", script)
        self.assertIn("do_boot_splash 1", script)
        self.assertIn("disable_splash=1", script)
        self.assertIn("systemd.show_status=false", script)
        self.assertIn("consoleblank=0", script)
        self.assertIn('boot_args quiet loglevel=3', script)

    def test_brave_keeps_aggressive_shields_without_domain_interstitial(self):
        script = (ROOT / "scripts" / "run-kiosk.sh").read_text(encoding="utf-8")
        policy = (ROOT / "config" / "brave-policy.json").read_text(encoding="utf-8")
        self.assertIn("BraveDomainBlock", script)
        self.assertIn('"DefaultBraveAdblockSetting": 2', policy)


if __name__ == "__main__":
    unittest.main()

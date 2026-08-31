import unittest

from raspberrytv.cec_power import TvPowerController, parse_tv_power


class CecPowerParsingTests(unittest.TestCase):
    def test_binary_power_reports(self):
        self.assertTrue(parse_tv_power("TRAFFIC: >> 0f:90:00"))
        self.assertTrue(parse_tv_power("TRAFFIC: >> 04:90:00"))
        self.assertFalse(parse_tv_power("TRAFFIC: >> 0f:90:01"))
        self.assertTrue(parse_tv_power("TRAFFIC: >> 0f:90:02"))
        self.assertFalse(parse_tv_power("TRAFFIC: >> 0f:90:03"))
        self.assertFalse(parse_tv_power("TRAFFIC: >> 0f:36"))

    def test_text_power_reports(self):
        self.assertTrue(parse_tv_power("power status: on"))
        self.assertFalse(parse_tv_power("power status: standby"))
        self.assertIsNone(parse_tv_power("key pressed: select"))

    def test_each_power_transition_is_applied_once(self):
        actions = []
        controller = TvPowerController(
            turn_on=lambda: actions.append("on"),
            turn_off=lambda: actions.append("off"),
        )
        controller.observe(True)
        controller.observe(True)
        controller.observe(False)
        controller.observe(False)
        self.assertEqual(actions, ["on", "off"])


if __name__ == "__main__":
    unittest.main()

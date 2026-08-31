import subprocess
import unittest

from raspberrytv.network import network_status


class NetworkStatusTests(unittest.TestCase):
    def test_parses_ethernet_and_wifi(self):
        def runner(command):
            if command[0] == "nmcli":
                return subprocess.CompletedProcess(command, 0, "eth0:ethernet:connected:Wired\nwlan0:wifi:connected:Casa\n", "")
            return subprocess.CompletedProcess(command, 0, "2: eth0    inet 192.168.1.5/24 scope global eth0\n3: wlan0    inet 192.168.1.6/24 scope global wlan0\n", "")

        result = network_status(runner)
        self.assertTrue(result["online"])
        self.assertEqual(result["ethernet"][0]["address"], "192.168.1.5/24")
        self.assertEqual(result["wifi"][0]["connection"], "Casa")


if __name__ == "__main__":
    unittest.main()

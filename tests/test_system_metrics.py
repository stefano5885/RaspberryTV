import tempfile
import unittest
from pathlib import Path

from raspberrytv.system_metrics import CpuSampler, _memory


class SystemMetricsTests(unittest.TestCase):
    def test_cpu_delta(self):
        with tempfile.TemporaryDirectory() as directory:
            stat = Path(directory) / "stat"
            stat.write_text("cpu  100 0 100 800 0 0 0 0\n", encoding="utf-8")

            def advance(_seconds):
                stat.write_text("cpu  150 0 150 850 0 0 0 0\n", encoding="utf-8")

            value = CpuSampler(stat, advance).percent()
            self.assertEqual(value, 66.7)

    def test_memory_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            meminfo = Path(directory) / "meminfo"
            meminfo.write_text("MemTotal: 1000 kB\nMemAvailable: 250 kB\n", encoding="utf-8")
            result = _memory(meminfo)
            self.assertEqual(result["used_bytes"], 750 * 1024)
            self.assertEqual(result["percent"], 75.0)


if __name__ == "__main__":
    unittest.main()

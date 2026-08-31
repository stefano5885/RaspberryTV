from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Callable


class CpuSampler:
    def __init__(self, stat_path: Path = Path("/proc/stat"), sleeper: Callable[[float], None] = time.sleep):
        self.stat_path = stat_path
        self.sleeper = sleeper
        self._previous: tuple[int, int] | None = None
        self._lock = threading.Lock()

    def _read(self) -> tuple[int, int]:
        fields = self.stat_path.read_text(encoding="utf-8").splitlines()[0].split()[1:]
        values = [int(value) for value in fields]
        total = sum(values)
        idle = values[3] + (values[4] if len(values) > 4 else 0)
        return total, idle

    def percent(self) -> float | None:
        with self._lock:
            try:
                current = self._read()
                if self._previous is None:
                    self.sleeper(0.08)
                    self._previous = current
                    current = self._read()
                previous = self._previous
                self._previous = current
                total_delta = current[0] - previous[0]
                idle_delta = current[1] - previous[1]
                if total_delta <= 0:
                    return 0.0
                return round(max(0.0, min(100.0, 100.0 * (total_delta - idle_delta) / total_delta)), 1)
            except (OSError, ValueError, IndexError):
                return None


def _memory(meminfo_path: Path = Path("/proc/meminfo")) -> dict:
    try:
        values: dict[str, int] = {}
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0]) * 1024
        total = values["MemTotal"]
        available = values.get("MemAvailable", values.get("MemFree", 0))
        used = max(0, total - available)
        percent = round(100.0 * used / total, 1) if total else 0.0
        return {"total_bytes": total, "used_bytes": used, "available_bytes": available, "percent": percent}
    except (OSError, ValueError, KeyError):
        return {"total_bytes": None, "used_bytes": None, "available_bytes": None, "percent": None}


def _temperature(path: Path = Path("/sys/class/thermal/thermal_zone0/temp")) -> float | None:
    try:
        return round(int(path.read_text(encoding="utf-8").strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def _uptime(path: Path = Path("/proc/uptime")) -> int | None:
    try:
        return int(float(path.read_text(encoding="utf-8").split()[0]))
    except (OSError, ValueError, IndexError):
        return None


class SystemMetrics:
    def __init__(self, cpu: CpuSampler | None = None):
        self.cpu = cpu or CpuSampler()

    def read(self) -> dict:
        try:
            load = round(os.getloadavg()[0], 2)
        except (AttributeError, OSError):
            load = None
        return {
            "cpu_percent": self.cpu.percent(),
            "cpu_temperature_c": _temperature(),
            "load_1m": load,
            "ram": _memory(),
            "uptime_seconds": _uptime(),
        }

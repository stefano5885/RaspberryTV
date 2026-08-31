from __future__ import annotations

import re
from collections.abc import Callable


_REPORT_POWER = re.compile(r">>\s*0[0-9a-fA-F]:90:0([0-3])(?:\s|$)")
_TV_STANDBY = re.compile(r">>\s*0[fF]:36(?:\s|$)")


def parse_tv_power(line: str) -> bool | None:
    """Return the TV power state reported by libCEC, when present."""
    traffic = _REPORT_POWER.search(line)
    if traffic:
        # CEC: 0=on, 1=standby, 2=standby->on, 3=on->standby.
        return traffic.group(1) in {"0", "2"}
    if _TV_STANDBY.search(line):
        return False

    normalized = " ".join(line.lower().replace("'", "").split())
    if "power status" not in normalized:
        return None
    if any(value in normalized for value in ("standby to on", "power status: on", "power status on")):
        return True
    if any(value in normalized for value in ("on to standby", "power status: standby", "power status standby")):
        return False
    return None


class TvPowerController:
    """Apply TV power changes without repeatedly stealing the active HDMI input."""

    def __init__(self, turn_on: Callable[[], None], turn_off: Callable[[], None]):
        self.turn_on = turn_on
        self.turn_off = turn_off
        self.last_state: bool | None = None

    def observe(self, powered_on: bool) -> None:
        if powered_on == self.last_state:
            return
        if powered_on:
            self.turn_on()
        else:
            self.turn_off()
        self.last_state = powered_on

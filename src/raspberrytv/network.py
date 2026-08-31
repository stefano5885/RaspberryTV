from __future__ import annotations

import ipaddress
import subprocess
from dataclasses import dataclass, asdict
from typing import Callable


@dataclass
class InterfaceStatus:
    name: str
    kind: str
    connected: bool
    connection: str = ""
    address: str = ""


def _run(command: list[str], timeout: int = 8) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def network_status(runner: Callable[..., subprocess.CompletedProcess[str]] = _run) -> dict:
    try:
        devices = runner(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"])
        addresses = runner(["ip", "-o", "-4", "addr", "show", "scope", "global"])
    except (OSError, subprocess.SubprocessError):
        return {"available": False, "ethernet": [], "wifi": [], "online": False}

    address_map: dict[str, str] = {}
    for line in addresses.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 4:
            try:
                address_map[fields[1]] = str(ipaddress.ip_interface(fields[3]))
            except ValueError:
                pass

    result = {"available": devices.returncode == 0, "ethernet": [], "wifi": [], "online": False}
    for line in devices.stdout.splitlines():
        fields = line.split(":", 3)
        if len(fields) != 4 or fields[1] not in {"ethernet", "wifi"}:
            continue
        item = InterfaceStatus(
            name=fields[0],
            kind=fields[1],
            connected=fields[2] == "connected",
            connection=fields[3] if fields[3] != "--" else "",
            address=address_map.get(fields[0], ""),
        )
        result[fields[1]].append(asdict(item))
        result["online"] = result["online"] or item.connected
    return result

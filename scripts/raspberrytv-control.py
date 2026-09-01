#!/usr/bin/python3
from __future__ import annotations

import json
import os
import pwd
import subprocess
import sys
import tempfile
from pathlib import Path


STATE_DIR = Path("/var/lib/raspberrytv")
STATE_FILE = STATE_DIR / "state.json"
APP_USER = "raspberrytv"


def run(command: list[str]) -> None:
    result = subprocess.run(command, timeout=40, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def write_state(**changes) -> None:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.update(changes)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=".state.", dir=STATE_DIR)
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    account = pwd.getpwnam(APP_USER)
    os.chown(temporary, account.pw_uid, account.pw_gid)
    os.chmod(temporary, 0o600)
    os.replace(temporary, STATE_FILE)


def wifi_apply() -> None:
    request = STATE_DIR / "wifi-request.json"
    try:
        data = json.loads(request.read_text(encoding="utf-8"))
        ssid = str(data["ssid"])
        password = str(data["password"])
        run(["nmcli", "radio", "wifi", "on"])
        run(["nmcli", "--wait", "30", "device", "wifi", "connect", ssid, "password", password])
    finally:
        request.unlink(missing_ok=True)


def main() -> None:
    if os.geteuid() != 0 or len(sys.argv) != 2:
        raise SystemExit("Uso riservato a root: raspberrytv-control <azione>")
    action = sys.argv[1]
    if action == "browser-restart":
        run(["systemctl", "restart", "raspberrytv-kiosk.service"])
    elif action == "browser-admin":
        write_state(browser_target="admin")
        run(["systemctl", "restart", "raspberrytv-kiosk.service"])
    elif action == "browser-site":
        write_state(browser_target="site")
        run(["systemctl", "restart", "raspberrytv-kiosk.service"])
    elif action == "browser-update":
        run(["systemctl", "try-restart", "raspberrytv-kiosk.service"])
    elif action == "tv-on":
        write_state(tv_power="on")
        run(["systemctl", "start", "raspberrytv-kiosk.service"])
    elif action == "tv-off":
        write_state(tv_power="standby")
        run(["systemctl", "stop", "raspberrytv-kiosk.service"])
    elif action == "wifi-apply":
        wifi_apply()
    elif action == "cec-restart":
        run(["systemctl", "restart", "raspberrytv-cec.service"])
    elif action == "update-start":
        run(["systemctl", "start", "--no-block", "raspberrytv-update.service"])
    elif action == "reboot":
        run(["systemctl", "reboot"])
    else:
        raise SystemExit("Azione non consentita")


if __name__ == "__main__":
    main()

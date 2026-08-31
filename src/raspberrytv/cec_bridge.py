from __future__ import annotations

import fcntl
import logging
import os
import re
import struct
import subprocess
import threading
import time
from pathlib import Path

from .cec_power import TvPowerController, parse_tv_power


LOGGER = logging.getLogger("raspberrytv.cec")

EV_SYN = 0
EV_KEY = 1
SYN_REPORT = 0
BUS_USB = 0x03
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

KEY_TAB = 15
KEY_ENTER = 28
KEY_LEFTSHIFT = 42
KEY_LEFTALT = 56
KEY_LEFT = 105
KEY_ESC = 1

KEY_LINE = re.compile(r"key pressed:\s*([^\(]+)", re.IGNORECASE)


class VirtualKeyboard:
    def __init__(self, device: str = "/dev/uinput"):
        self.handle = os.open(device, os.O_WRONLY | os.O_NONBLOCK)
        fcntl.ioctl(self.handle, UI_SET_EVBIT, EV_KEY)
        for code in {KEY_TAB, KEY_ENTER, KEY_LEFTSHIFT, KEY_LEFTALT, KEY_LEFT, KEY_ESC}:
            fcntl.ioctl(self.handle, UI_SET_KEYBIT, code)
        name = b"RaspberryTV CEC Remote"
        descriptor = struct.pack(
            "80sHHHHi" + "i" * (64 * 4),
            name,
            BUS_USB,
            0x1209,
            0x0001,
            1,
            0,
            *([0] * (64 * 4)),
        )
        os.write(self.handle, descriptor)
        fcntl.ioctl(self.handle, UI_DEV_CREATE)
        time.sleep(0.3)

    def close(self) -> None:
        try:
            fcntl.ioctl(self.handle, UI_DEV_DESTROY)
        finally:
            os.close(self.handle)

    def _event(self, event_type: int, code: int, value: int) -> None:
        os.write(self.handle, struct.pack("llHHI", 0, 0, event_type, code, value))

    def chord(self, *codes: int) -> None:
        for code in codes:
            self._event(EV_KEY, code, 1)
        for code in reversed(codes):
            self._event(EV_KEY, code, 0)
        self._event(EV_SYN, SYN_REPORT, 0)


def normalize_key(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def dispatch(keyboard: VirtualKeyboard, key: str, helper: str = "/usr/local/sbin/raspberrytv-control") -> None:
    key = normalize_key(key)
    if key in {"down", "right"}:
        keyboard.chord(KEY_TAB)
    elif key in {"up", "left"}:
        keyboard.chord(KEY_LEFTSHIFT, KEY_TAB)
    elif key in {"select", "enter"}:
        keyboard.chord(KEY_ENTER)
    elif key in {"exit", "return", "backward"}:
        keyboard.chord(KEY_LEFTALT, KEY_LEFT)
    elif key in {"root menu", "setup menu", "contents menu", "home"}:
        subprocess.run([helper, "browser-admin"], timeout=10, check=False)


def run_client(
    keyboard: VirtualKeyboard,
    helper: str = "/usr/local/sbin/raspberrytv-control",
) -> None:
    process = subprocess.Popen(
        ["cec-client", "-d", "8", "-t", "p", "-o", "RaspberryTV"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    stop_queries = threading.Event()
    write_lock = threading.Lock()

    def send(command: str) -> None:
        with write_lock:
            process.stdin.write(command + "\n")
            process.stdin.flush()

    def tv_on() -> None:
        subprocess.run([helper, "tv-on"], timeout=30, check=False)
        try:
            send("as")
        except (BrokenPipeError, OSError):
            pass

    def tv_off() -> None:
        subprocess.run([helper, "tv-off"], timeout=30, check=False)

    power_controller = TvPowerController(turn_on=tv_on, turn_off=tv_off)

    def query_power() -> None:
        while not stop_queries.wait(2):
            try:
                send("pow 0")
            except (BrokenPipeError, OSError):
                return
            if stop_queries.wait(13):
                return

    query_thread = threading.Thread(target=query_power, name="cec-power-query", daemon=True)
    query_thread.start()
    for line in process.stdout:
        powered_on = parse_tv_power(line)
        if powered_on is not None:
            LOGGER.info("Stato alimentazione TV: %s", "accesa" if powered_on else "spenta")
            power_controller.observe(powered_on)
        match = KEY_LINE.search(line)
        if match:
            key = normalize_key(match.group(1))
            LOGGER.info("Tasto CEC: %s", key)
            dispatch(keyboard, key)
    stop_queries.set()
    return_code = process.wait()
    raise RuntimeError(f"cec-client terminato con codice {return_code}")


def main() -> None:
    logging.basicConfig(level=os.getenv("RASPBERRYTV_LOG_LEVEL", "INFO"), format="%(levelname)s %(name)s: %(message)s")
    keyboard = VirtualKeyboard()
    try:
        while True:
            try:
                run_client(keyboard)
            except Exception as exc:
                LOGGER.warning("CEC non disponibile: %s; nuovo tentativo tra 5 secondi", exc)
                time.sleep(5)
    finally:
        keyboard.close()


if __name__ == "__main__":
    main()

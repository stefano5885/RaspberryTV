from __future__ import annotations

import fcntl
import logging
import os
import re
import struct
import subprocess
import threading
import time

from .cec_diagnostics import CecDiagnostics
from .cec_keys import normalize_color_actions, normalize_input_mode, normalize_key, normalize_keymap, operation_for_key
from .config import ConfigStore
from .cec_power import TvPowerController, parse_tv_power


LOGGER = logging.getLogger("raspberrytv.cec")

EV_SYN = 0
EV_KEY = 1
EV_REL = 2
SYN_REPORT = 0
BUS_USB = 0x03
UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_SET_RELBIT = 0x40045566
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502

KEY_TAB = 15
KEY_ENTER = 28
KEY_R = 19
KEY_LEFTCTRL = 29
KEY_LEFTSHIFT = 42
KEY_LEFTALT = 56
KEY_LEFT = 105
KEY_ESC = 1
BTN_LEFT = 272
REL_X = 0
REL_Y = 1
POINTER_STEP = 48

KEY_LINE = re.compile(r"key pressed:\s*([^\(]+)", re.IGNORECASE)


class VirtualRemote:
    def __init__(self, device: str = "/dev/uinput"):
        self.handle = os.open(device, os.O_WRONLY | os.O_NONBLOCK)
        fcntl.ioctl(self.handle, UI_SET_EVBIT, EV_KEY)
        fcntl.ioctl(self.handle, UI_SET_EVBIT, EV_REL)
        fcntl.ioctl(self.handle, UI_SET_RELBIT, REL_X)
        fcntl.ioctl(self.handle, UI_SET_RELBIT, REL_Y)
        for code in {KEY_TAB, KEY_ENTER, KEY_R, KEY_LEFTCTRL, KEY_LEFTSHIFT, KEY_LEFTALT, KEY_LEFT, KEY_ESC, BTN_LEFT}:
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
        os.write(self.handle, struct.pack("llHHi", 0, 0, event_type, code, value))

    def chord(self, *codes: int) -> None:
        for code in codes:
            self._event(EV_KEY, code, 1)
        for code in reversed(codes):
            self._event(EV_KEY, code, 0)
        self._event(EV_SYN, SYN_REPORT, 0)

    def move(self, x: int, y: int) -> None:
        if x:
            self._event(EV_REL, REL_X, x)
        if y:
            self._event(EV_REL, REL_Y, y)
        self._event(EV_SYN, SYN_REPORT, 0)

    def click(self) -> None:
        self.chord(BTN_LEFT)


def dispatch(
    remote: VirtualRemote,
    key: str,
    keymap: dict[str, list[str]],
    input_mode: str = "focus",
    color_actions: dict[str, str] | None = None,
    helper: str = "/usr/local/sbin/raspberrytv-control",
) -> str | None:
    executed = operation_for_key(key, keymap, input_mode)
    if executed and executed.startswith("color_"):
        executed = normalize_color_actions(color_actions).get(executed.removeprefix("color_"), "none")
    if executed == "focus_next":
        remote.chord(KEY_TAB)
    elif executed == "focus_previous":
        remote.chord(KEY_LEFTSHIFT, KEY_TAB)
    elif executed == "pointer_up":
        remote.move(0, -POINTER_STEP)
    elif executed == "pointer_down":
        remote.move(0, POINTER_STEP)
    elif executed == "pointer_left":
        remote.move(-POINTER_STEP, 0)
    elif executed == "pointer_right":
        remote.move(POINTER_STEP, 0)
    elif executed == "pointer_click":
        remote.click()
    elif executed == "activate":
        remote.chord(KEY_ENTER)
    elif executed == "back":
        remote.chord(KEY_LEFTALT, KEY_LEFT)
    elif executed == "admin":
        subprocess.run([helper, "browser-admin"], timeout=10, check=False)
    elif executed == "site":
        subprocess.run([helper, "browser-site"], timeout=10, check=False)
    elif executed == "reload":
        remote.chord(KEY_LEFTCTRL, KEY_R)
    return executed


def run_client(
    remote: VirtualRemote,
    store: ConfigStore,
    diagnostics: CecDiagnostics,
    helper: str = "/usr/local/sbin/raspberrytv-control",
) -> None:
    process = subprocess.Popen(
        # 31 include DEBUG: libCEC pubblica "key pressed: ..." a quel livello.
        # Con il solo livello TRAFFIC (8) i pacchetti arrivano ma non vengono
        # decodificati nel nome tasto atteso da KEY_LINE.
        ["cec-client", "-d", "31", "-t", "p", "-o", "RaspberryTV"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    diagnostics.record("bridge", "cec-client avviato; attendo eventi HDMI-CEC", status="listening")
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
    last_powered_on: bool | None = None
    for line in process.stdout:
        powered_on = parse_tv_power(line)
        if powered_on is not None:
            if powered_on != last_powered_on:
                power_label = "accesa" if powered_on else "spenta"
                LOGGER.info("Stato alimentazione TV: %s", power_label)
                diagnostics.record("power", f"Display rilevato come {power_label}")
                last_powered_on = powered_on
            power_controller.observe(powered_on)
        match = KEY_LINE.search(line)
        if match:
            key = normalize_key(match.group(1))
            LOGGER.info("Tasto CEC: %s", key)
            config = store.config_file.read()
            keymap = normalize_keymap(config.get("cec_keymap"))
            input_mode = normalize_input_mode(config.get("cec_input_mode"))
            color_actions = normalize_color_actions(config.get("cec_color_actions"))
            action = dispatch(remote, key, keymap, input_mode, color_actions)
            diagnostics.record(
                "key",
                f"Tasto “{key}” → {action or 'non associato'}",
                key=key,
                action=action or "unmapped",
            )
        elif re.search(r"error|warning|failed|unable|connection opened|cec client registered", line, re.IGNORECASE):
            diagnostics.record("adapter", line, level="warning" if re.search(r"error|failed|unable", line, re.IGNORECASE) else "info")
    stop_queries.set()
    return_code = process.wait()
    raise RuntimeError(f"cec-client terminato con codice {return_code}")


def main() -> None:
    logging.basicConfig(level=os.getenv("RASPBERRYTV_LOG_LEVEL", "INFO"), format="%(levelname)s %(name)s: %(message)s")
    store = ConfigStore()
    diagnostics = CecDiagnostics(store.state_dir)
    while True:
        remote: VirtualRemote | None = None
        try:
            diagnostics.record("bridge", "Inizializzazione telecomando virtuale e adattatore CEC", status="starting")
            remote = VirtualRemote()
            run_client(remote, store, diagnostics)
        except Exception as exc:
            LOGGER.warning("CEC non disponibile: %s; nuovo tentativo tra 5 secondi", exc)
            diagnostics.record("error", f"CEC non disponibile: {exc}; nuovo tentativo tra 5 secondi", status="retrying", level="error")
            time.sleep(5)
        finally:
            if remote is not None:
                remote.close()


if __name__ == "__main__":
    main()

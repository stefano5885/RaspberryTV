#!/usr/bin/python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


REQUEST = Path("/var/lib/raspberrytv/browser-diagnostic-request.json")
PROFILE = "/var/lib/raspberrytv/browser-profile"
ALLOWED = {"gpu", "media-internals", "version"}


def consume_request() -> str:
    try:
        data = json.loads(REQUEST.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return ""
    try:
        REQUEST.unlink()
    except OSError:
        return ""
    page = str(data.get("test", ""))
    return page if page in ALLOWED else ""


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Uso: browser-diagnostics-worker.py <browser>")
    browser = sys.argv[1]
    scheme = "brave" if Path(browser).name.startswith("brave") else "chrome"
    while True:
        page = consume_request()
        if page:
            try:
                subprocess.run(
                    [browser, f"--user-data-dir={PROFILE}", "--new-tab", f"{scheme}://{page}"],
                    timeout=20,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"Impossibile aprire {scheme}://{page}: {exc}", file=sys.stderr, flush=True)
        time.sleep(0.5)


if __name__ == "__main__":
    main()

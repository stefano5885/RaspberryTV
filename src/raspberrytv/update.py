from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SEMVER_TAG = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


@dataclass(frozen=True, order=True)
class StableVersion:
    major: int
    minor: int
    patch: int
    tag: str

    @classmethod
    def parse(cls, tag: str) -> "StableVersion | None":
        match = SEMVER_TAG.fullmatch(tag.strip())
        if not match:
            return None
        return cls(int(match[1]), int(match[2]), int(match[3]), tag.strip())


def latest_stable(tags: list[str]) -> StableVersion | None:
    versions = [version for tag in tags if (version := StableVersion.parse(tag))]
    return max(versions, default=None)


def parse_ls_remote(output: str) -> list[str]:
    tags: list[str] = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1].startswith("refs/tags/") and not fields[1].endswith("^{}"):
            tags.append(fields[1].removeprefix("refs/tags/"))
    return tags


class UpdateInspector:
    def __init__(
        self,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        deploy_key: Path = Path("/etc/raspberrytv-git/deploy_key"),
        known_hosts: Path = Path("/var/lib/raspberrytv/git-known-hosts"),
    ):
        self.runner = runner
        self.deploy_key = deploy_key
        self.known_hosts = known_hosts

    def check(self, repository_url: str, installed: str) -> dict:
        if not repository_url:
            return {"configured": False, "installed": installed, "available": None, "update_available": False}
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        if self.deploy_key.is_file():
            env["GIT_SSH_COMMAND"] = (
                f"ssh -i {self.deploy_key} -o IdentitiesOnly=yes "
                f"-o UserKnownHostsFile={self.known_hosts} "
                "-o StrictHostKeyChecking=accept-new -o BatchMode=yes"
            )
        result = self.runner(
            ["git", "ls-remote", "--tags", "--refs", repository_url],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError("Impossibile interrogare il repository Git")
        available = latest_stable(parse_ls_remote(result.stdout))
        current = StableVersion.parse(installed)
        return {
            "configured": True,
            "installed": installed,
            "available": available.tag if available else None,
            "update_available": bool(available and (current is None or available > current)),
        }

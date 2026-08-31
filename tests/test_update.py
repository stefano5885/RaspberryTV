import tempfile
import unittest
from pathlib import Path

from raspberrytv.config import ConfigStore
from raspberrytv.update import StableVersion, latest_stable, parse_ls_remote
from raspberrytv.update_worker import ReleaseManager


class VersionTests(unittest.TestCase):
    def test_only_stable_semver_tags(self):
        version = latest_stable(["v1.2.3", "v2.0.0-rc1", "latest", "1.9.9"])
        self.assertIsNotNone(version)
        self.assertEqual((version.major, version.minor, version.patch), (1, 9, 9))
        self.assertIsNone(StableVersion.parse("v1.0.0-beta"))

    def test_parse_remote_tags(self):
        output = "a refs/tags/v1.0.0\nb refs/tags/v1.1.0\nc refs/heads/main\n"
        self.assertEqual(parse_ls_remote(output), ["v1.0.0", "v1.1.0"])


class FailingUpdateManager(ReleaseManager):
    def __init__(self, store, root, release, previous):
        super().__init__(store, root)
        self.release = release
        self.previous = previous
        self.switches = []
        self.restarts = 0

    def _prepare_mirror(self, repository_url):
        pass

    def _tags(self):
        return ["v1.0.0"]

    def _release_for_tag(self, tag):
        return self.release

    def _switch(self, release):
        self.switches.append(release)
        return self.previous if len(self.switches) == 1 else self.release

    def _restart(self):
        self.restarts += 1

    def _healthy(self, timeout=45, expected_version=""):
        return False


class RollbackTests(unittest.TestCase):
    def test_failed_health_check_switches_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = ConfigStore(root / "etc", root / "state")
            store.config_file.write({"repository_url": "https://example.invalid/repo.git"})
            release = root / "code" / "releases" / "v1.0.0"
            previous = root / "code" / "releases" / "v0.9.0"
            release.mkdir(parents=True)
            previous.mkdir(parents=True)
            manager = FailingUpdateManager(store, root / "code", release, previous)
            with self.assertRaisesRegex(RuntimeError, "Health check"):
                manager.update("v1.0.0")
            self.assertEqual(manager.switches, [release, previous])
            self.assertEqual(manager.restarts, 2)


if __name__ == "__main__":
    unittest.main()

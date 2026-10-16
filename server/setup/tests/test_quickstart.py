"""Exercise public entry points with local download fixtures, never sudo/network."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[3] / "tools"
STARTERS = {
    "install-t95-dashboard.sh": ["dashboard", "install"],
    "uninstall-t95-dashboard.sh": ["dashboard", "remove"],
    "install-t95-bluetooth.sh": ["bluetooth", "install"],
    "uninstall-t95-bluetooth.sh": ["bluetooth", "remove", "--remove-packages"],
}
STUB = '#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n'


class QuickstartTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="t95-quickstart-")
        self.task_dir = Path(self.temp.name)
        self.fake_bin = self.task_dir / "bin"
        self.fake_bin.mkdir()
        self.download = self.task_dir / "download"
        self.log = self.task_dir / "curl-args"
        (self.fake_bin / "curl").write_text('''#!/usr/bin/env bash
set -eu
printf '%s\n' "$@" >> "$T95_TEST_LOG"
cp -- "$T95_TEST_DOWNLOAD" "${@: -1}"
''')
        (self.fake_bin / "sudo").write_text('#!/usr/bin/env bash\nexec "$@"\n')
        for p in self.fake_bin.iterdir():
            p.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.fake_bin) + ":" + os.environ["PATH"],
                        T95_TEST_DOWNLOAD=str(self.download), T95_TEST_LOG=str(self.log),
                        T95_SETUP_REF="test-branch")

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, script, *args, input=None):
        return subprocess.run(["bash", str(script), *args], env=self.env, input=input,
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)

    def test_separate_local_starters_have_fixed_actions_and_forward_options(self):
        local = self.task_dir / "local"
        local.mkdir()
        (local / "t95-setup.sh").write_text(STUB)
        for name, expected in STARTERS.items():
            with self.subTest(starter=name):
                shutil.copy2(TOOLS / name, local / name)
                result = self.execute(local / name, "--user", "fixture-user")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), expected + ["--user", "fixture-user"])
                self.assertFalse(self.log.exists())

    def test_separate_download_starters_use_same_ref_and_clean_temporary_file(self):
        remote = self.task_dir / "remote"
        remote.mkdir()
        self.download.write_text(STUB)
        for name, expected in STARTERS.items():
            with self.subTest(starter=name):
                self.log.unlink(missing_ok=True)
                shutil.copy2(TOOLS / name, remote / name)
                result = self.execute(remote / name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), expected)
                lines = self.log.read_text().splitlines()
                urls = [line for line in lines if line.startswith("https://")]
                self.assertEqual(len(urls), 1)
                self.assertTrue(urls[0].endswith("/test-branch/tools/t95-setup.sh"))
                self.assertFalse(Path(lines[-1]).exists())

    def archive(self, fail_first=False):
        manager = self.task_dir / "repo/server/setup/t95_setup.py"
        manager.parent.mkdir(parents=True)
        manager.write_text('import json, sys\nprint("ARGS:" + json.dumps(sys.argv[1:]))\n' +
                           ('sys.exit(9) if sys.argv[1] == "dashboard" else None\n' if fail_first else ''))
        with tarfile.open(self.download, "w:gz") as output:
            output.add(self.task_dir / "repo", arcname="repo")

    def test_combined_install_and_menu_use_one_archive_for_both_components(self):
        self.archive()
        for args, text in [(["all", "install"], None), ([], "0\n")]:
            with self.subTest(args=args):
                self.log.unlink(missing_ok=True)
                result = self.execute(TOOLS / "t95-setup.sh", *args, input=text)
                self.assertEqual(result.returncode, 0, result.stderr)
                calls = [json.loads(line.removeprefix("ARGS:")) for line in result.stdout.splitlines()
                         if line.startswith("ARGS:")]
                self.assertEqual([c[:2] for c in calls], [["dashboard", "install"], ["bluetooth", "install"]])
                urls = [line for line in self.log.read_text().splitlines() if line.startswith("https://")]
                self.assertEqual(len(urls), 1)
                self.assertTrue(urls[0].endswith("/tar.gz/test-branch"))

    def test_combined_install_stops_after_first_component_failure(self):
        self.archive(fail_first=True)
        result = self.execute(TOOLS / "t95-setup.sh", "all", "install")
        self.assertEqual(result.returncode, 9)
        calls = [json.loads(line.removeprefix("ARGS:")) for line in result.stdout.splitlines()
                 if line.startswith("ARGS:")]
        self.assertEqual([c[:2] for c in calls], [["dashboard", "install"]])


if __name__ == "__main__":
    unittest.main()

"""Installer effects are simulated inside a temporary filesystem."""
from copy import deepcopy
import contextlib
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

LIB = Path(__file__).resolve().parents[1] / "lib"
sys.path.insert(0, str(LIB))
import t95_usb as usb
import t95_install as install


class InstallSystem(usb.System):
    def __init__(self, root, user):
        super().__init__(runner=self.run, root=root)
        self.user, self.calls = user, []
        self.states = {(False, name): {"enabled": "enabled", "active": True} for name in
                       ("smbd.service", "nmbd.service", "udisks2.service", "polkit.service")}
        self.states[(True, "udiskie.service")] = {"enabled": "enabled", "active": True}
        self.fail_restart = False
        self.fail_apt = False
        self.known_group = True
        self.reconcile_callback = None
        self.ignore_stop = False
        self.package_callback = None
        proc = self.path("/proc/999/status")
        proc.parent.mkdir(parents=True)
        proc.write_text(f"Groups:\t{user.gid}\n")

    def check_tools(self, names):
        self.calls.append(["check-tools", *names])

    def service(self, user, args, check=True):
        return self.run(["userctl", *args], check=check)

    def as_user(self, user, args, **kwargs):
        self.calls.append(["as-user", *args])
        if args[-1:] == ["reconcile"] and self.reconcile_callback:
            self.reconcile_callback()
        return subprocess.CompletedProcess(args, 0, "", "")

    def interactive(self, args):
        self.calls.append(["interactive", *args])

    def run(self, args, check=True, timeout=30):
        self.calls.append(args)
        output, rc = "", 0
        if args[0] == "testparm":
            output = self.path("/etc/samba/smb.conf").read_text()
        elif args[:2] == ["getent", "group"]:
            output = f"sambashare:x:{self.user.gid}:{self.user.name}\n"
        elif args[:2] == ["apt-get", "update"]:
            if not list(self.path("/var/lib/t95-samba").glob("*/state.json")):
                raise AssertionError("APT started before backup journal")
            if self.fail_apt:
                raise usb.CommandError("simulated APT failure")
        elif args[:2] == ["apt-get", "install"] and self.package_callback:
            self.package_callback()
        elif args[0] == "systemd-tmpfiles":
            runtime = self.path("/run/t95-usb")
            for name in ("", "locks", "guards", "operations"):
                p = runtime / name
                p.mkdir(parents=True, exist_ok=True)
                p.chmod(0o700 if name == "operations" else 0o755)
            (runtime / f"locks/shares-{self.user.uid}.lock").touch()
        elif args[0] == "install":
            self.path(args[-1]).mkdir(parents=True, exist_ok=True)
        elif args[0] == "pdbedit":
            output = f"{self.user.name}:1000:Fixture\n"
        elif args[0] in ("systemctl", "userctl"):
            user = args[0] == "userctl"
            if "--property=MainPID" in args:
                output = "999\n"
            else:
                units = [a for a in args if a.endswith(".service")]
                for unit in units:
                    state = self.states.setdefault((user, unit), {"enabled": "disabled", "active": False})
                    if "show" in args:
                        output = "loaded\n"
                    elif "is-enabled" in args:
                        output = state["enabled"] + "\n"
                    elif "is-active" in args:
                        output = "active\n" if state["active"] else "inactive\n"
                    elif self.fail_restart and user and "restart" in args:
                        self.fail_restart = False
                        raise usb.CommandError("simulated restart failure")
                    else:
                        if "enable" in args: state["enabled"] = "enabled-runtime" if "--runtime" in args else "enabled"
                        if "disable" in args: state["enabled"] = "disabled"
                        if "start" in args or "restart" in args or "--now" in args: state["active"] = True
                        if "stop" in args and not self.ignore_stop: state["active"] = False
        return subprocess.CompletedProcess(args, rc, output, "")


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        source = LIB.parent
        for subdir in ("lib", "scripts", "config"):
            shutil.copytree(source / subdir, self.source / subdir, ignore=shutil.ignore_patterns("__pycache__"))
        self.manifest()
        home = self.root / "home/fixture"
        home.mkdir(parents=True)
        self.user = usb.User("fixture-user", os.getuid(), os.getgid(), home, self.root / "media/fixture", home / ".local/state/t95-usb-shares")
        (self.root / "etc/samba").mkdir(parents=True)
        (self.root / "etc/armbian-release").write_text("fixture\n")
        (self.root / "var/lib").mkdir(parents=True)
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
        self.system = InstallSystem(self.root, self.user)
        self.owner_patch = patch.object(install.os, "fchown")
        self.chown_patch = patch.object(install.os, "chown")
        self.owner_patch.start()
        self.chown_patch.start()
        self.link_patch = patch.object(install.os, "lchown")
        self.link_patch.start()
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        self.output.__exit__(None, None, None)
        self.owner_patch.stop()
        self.chown_patch.stop()
        self.link_patch.stop()
        self.temp.cleanup()

    def manifest(self):
        lines = [hashlib.sha256(p.read_bytes()).hexdigest() + "  ./" + str(p.relative_to(self.source))
                 for p in sorted(self.source.rglob("*")) if p.is_file() and p.name != "MANIFEST.sha256"]
        (self.source / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")

    def manager(self, update=False):
        return install.Installer(self.user, update=update, system=self.system, source=self.source, owner=os.getuid())

    def existing(self):
        manager = self.manager()
        config = self.root / "etc/samba/smb.conf"
        config.write_bytes(manager.samba_config() + b"\n[PERSONAL]\n    path = /srv/personal\n    read only = yes\n")
        udiskie = self.user.home / ".config/udiskie"
        udiskie.mkdir(parents=True)
        (udiskie / "config.yml").write_text("program_options:\n  automount: false\n")
        (udiskie / "config.json").write_text('{"old": true}\n')
        unit = self.user.home / ".config/systemd/user/udiskie.service"
        unit.parent.mkdir(parents=True)
        unit.write_text("old unit\n")
        return config, udiskie / "config.yml", unit

    def test_fresh_install_backups_precede_apt_and_installs_explicit_configuration(self):
        manager = self.manager()
        manager.install()
        self.assertEqual((self.root / "var/lib/t95-samba").stat().st_mode & 0o777, 0o700)
        self.assertEqual((manager.backup / "state.json").stat().st_mode & 0o777, 0o600)
        unit = self.user.home / ".config/systemd/user/udiskie.service"
        self.assertIn("--config=%h/.config/udiskie/config.json", unit.read_text())
        self.assertTrue((self.root / "usr/local/lib/t95-usb/t95_usb.py").exists())
        self.assertTrue(any(c == ["userctl", "restart", "udiskie.service"] for c in self.system.calls))
        self.assertTrue(any(c[-1:] == ["reconcile"] for c in self.system.calls))

    def test_update_preserves_samba_passwords_data_path_and_yaml(self):
        config, yaml, unit = self.existing()
        original = config.read_bytes()
        manager = self.manager(update=True)
        manager.install()
        self.assertEqual(config.read_bytes(), original)
        self.assertIn("automount: false", yaml.read_text())
        self.assertIn("--config=", unit.read_text())
        self.assertFalse(any(c[0] == "pdbedit" or "smbpasswd" in c for c in self.system.calls))
        self.assertFalse(any(c == ["systemctl", "restart", "smbd.service"] for c in self.system.calls))
        self.assertTrue(any(r["path"] == str(yaml) for r in manager.files))

    def test_incompatible_update_fails_before_packages_and_preserves_config(self):
        config, _, _ = self.existing()
        config.write_text("[global]\n[PERSONAL]\npath = /srv/other\n")
        before = config.read_bytes()
        with self.assertRaisesRegex(usb.USBError, "bestehende T95"):
            self.manager(update=True).install()
        self.assertEqual(config.read_bytes(), before)
        self.assertFalse(any(c[0] == "apt-get" for c in self.system.calls))

    def test_missing_required_setting_lists_correction_without_rewriting(self):
        config, _, _ = self.existing()
        config.write_text(config.read_text().replace("usershare max shares = 20", "usershare max shares = 0"))
        with self.assertRaisesRegex(usb.USBError, "usershare max shares = 20"):
            self.manager(update=True).install()
        self.assertIn("usershare max shares = 0", config.read_text())

    def test_failed_service_activation_restores_original_files_and_service_state(self):
        config, yaml, unit = self.existing()
        before = {p: p.read_bytes() for p in (config, yaml, unit)}
        states = deepcopy(self.system.states)
        self.system.fail_restart = True
        manager = self.manager(update=True)
        with self.assertRaisesRegex(usb.USBError, "Vorherige Projektdateien"):
            manager.install()
        for path, content in before.items(): self.assertEqual(path.read_bytes(), content)
        for key, value in states.items():
            self.assertEqual(value, self.system.states[key])
        self.assertIn('"phase": "rolled-back"', (manager.backup / "state.json").read_text())

    def test_backup_failure_prevents_apt(self):
        self.existing()
        with patch.object(install, "atomic_file", side_effect=OSError("backup failed")):
            with self.assertRaises(OSError): self.manager(update=True).install()
        self.assertFalse(any(c[0] == "apt-get" for c in self.system.calls))

    def test_manifest_corruption_prevents_apt_and_mutation(self):
        config, _, _ = self.existing()
        (self.source / "lib/t95_usb.py").write_text("changed without matching manifest")
        with self.assertRaisesRegex(usb.USBError, "Prüfsumme"):
            self.manager(update=True).install()
        self.assertFalse(any(c[0] == "apt-get" for c in self.system.calls))

    def test_stale_manager_group_is_reported_and_never_reports_installed(self):
        self.existing()
        self.system.path("/proc/999/status").write_text("Groups:\t999999\n")
        manager = self.manager(update=True)
        with self.assertRaisesRegex(usb.USBError, "sambashare noch nicht"):
            manager.install()
        self.assertIn('"phase": "rolled-back"', (manager.backup / "state.json").read_text())

    def test_failed_reconcile_restores_old_map_format(self):
        self.existing()
        self.user.state.mkdir(parents=True)
        old = self.user.state / "sda1.map"
        content = f"OLD\t{self.user.base}/DATA\t/dev/sda1\tuuid-test\n"
        old.write_text(content)
        def migration_then_failure():
            store = usb.UserState(self.user)
            record = store.read()[0]
            record.update(schema=1, boot="fixture", diskseq="10", syspath="/sys/test")
            store.write(record)
            raise usb.USBError("reconcile failed after migration")
        self.system.reconcile_callback = migration_then_failure
        manager = self.manager(update=True)
        with self.assertRaises(usb.USBError): manager.install()
        self.assertEqual(old.read_text(), content)
        self.assertFalse(list(self.user.state.glob("*.json")))

    def test_unrestored_service_state_is_recorded_as_rollback_failed(self):
        self.existing()
        self.system.states[(True, "udiskie.service")]["active"] = False
        self.system.ignore_stop = True
        def fail(): raise usb.USBError("reconciliation failed")
        self.system.reconcile_callback = fail
        manager = self.manager(update=True)
        with self.assertRaisesRegex(usb.USBError, "Rücknahme unvollständig"):
            manager.install()
        self.assertIn('"phase": "rollback-failed"', (manager.backup / "state.json").read_text())

    def test_install_uses_verified_payload_even_if_checkout_changes_during_apt(self):
        self.existing()
        original = (self.source / "lib/t95_usb.py").read_bytes()
        def changed(): (self.source / "lib/t95_usb.py").write_bytes(b"changed after verification")
        self.system.package_callback = changed
        self.manager(update=True).install()
        self.assertEqual((self.root / "usr/local/lib/t95-usb/t95_usb.py").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()

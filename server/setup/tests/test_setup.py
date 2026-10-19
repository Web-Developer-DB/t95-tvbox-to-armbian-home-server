"""Filesystem fixtures + fake package/service backend; never changes the host."""
import hashlib
import contextlib
import io
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess
import tempfile
import tarfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "t95_setup.py"
spec = importlib.util.spec_from_file_location("t95_setup", MODULE)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
ACCOUNT = next(p for p in pwd.getpwall() if 1000 <= p.pw_uid < 60000 and p.pw_dir.startswith("/home/"))


class Backend:
    def __init__(self):
        self.calls = []
        self.packages = {"bluez", "pipewire", "curl", "procps", "iproute2", "util-linux"}
        self.extra_remove = False
        self.fail_enable = False
        self.fail_apt = False
        self.units = {}
        self.fail_stop = None
        self.ignore_stop = None

    def __call__(self, command, check=True, timeout=120):
        self.calls.append(command)
        cmd = command
        user_scope = cmd[0] == "runuser"
        if cmd[0] == "runuser":
            cmd = cmd[cmd.index(f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{ACCOUNT.pw_uid}/bus") + 1:]
        out, rc = "", 0
        if self.fail_apt and cmd[:2] == ["apt-get", "update"]:
            out, rc = "simulated APT failure", 1
        elif cmd[0] == "dpkg-query":
            out, rc = ("install ok installed", 0) if cmd[-1] in self.packages else ("", 1)
        elif cmd[:2] == ["apt-get", "install"]:
            self.packages.update(cmd[4:])
        elif cmd[:3] == ["apt-get", "-s", "remove"]:
            out = "\n".join("Remv " + p for p in cmd[4:] if p in self.packages)
            if self.extra_remove:
                out += "\nRemv unrelated-server-package"
        elif cmd[:2] == ["apt-get", "remove"]:
            self.packages.difference_update(cmd[4:])
        elif cmd[0] == "systemctl":
            unit_args = [a for a in cmd[1:] if a.endswith((".service", ".socket"))]
            def unit_state(unit):
                key = (user_scope, unit)
                if key not in self.units:
                    self.units[key] = {
                        "enabled": "enabled" if unit in ("bluetooth.service", "pipewire.service") else "disabled",
                        "active": unit in ("bluetooth.service", "pipewire.service"),
                    }
                return self.units[key]
            unit_packages = {"bluetooth.service": "bluez", "mpris-proxy.service": "bluez",
                             "mpd.service": "mpd", "mpd.socket": "mpd", "mpdris2.service": "mpdris2",
                             "pipewire.service": "pipewire", "pipewire.socket": "pipewire",
                             "pipewire-pulse.service": "pipewire-pulse", "pipewire-pulse.socket": "pipewire-pulse",
                             "wireplumber.service": "wireplumber"}
            present = not unit_args or unit_packages.get(unit_args[0]) in self.packages
            if "is-enabled" in cmd:
                out = unit_state(unit_args[0])["enabled"] if present else "not-found"
            elif "is-active" in cmd:
                out = "active" if present and unit_state(unit_args[0])["active"] else "inactive"
            elif "show" in cmd:
                out = "loaded" if present else "not-found"
            elif self.fail_enable and "enable" in cmd and "wireplumber.service" in cmd:
                self.fail_enable = False
                out, rc = "simulated service failure", 1
            elif self.fail_stop and "stop" in cmd and self.fail_stop in cmd:
                out, rc = "simulated stop failure", 1
            elif self.ignore_stop and "stop" in cmd and self.ignore_stop in cmd:
                pass
            else:
                for unit in unit_args:
                    state = unit_state(unit)
                    if "enable" in cmd:
                        state["enabled"] = "enabled-runtime" if "--runtime" in cmd else "enabled"
                    if "disable" in cmd:
                        state["enabled"] = "disabled"
                    if "mask" in cmd:
                        state["enabled"] = "masked"
                    if "start" in cmd or "restart" in cmd or ("enable" in cmd and "--now" in cmd):
                        state["active"] = True
                    if "stop" in cmd or ("disable" in cmd and "--now" in cmd) or "mask" in cmd:
                        state["active"] = False
        elif cmd[:2] == ["loginctl", "show-user"]:
            out = "yes"
        elif cmd[:2] == ["mpd", "--version"]:
            out = "Music Player Daemon 0.24.4\nOutput plugins: pipewire alsa null"
        elif cmd[0] == "bluetoothctl":
            out = "Controller 00:11:22:33:44:55 Test [default]" if cmd[-1] == "list" else "Changing power on succeeded"
        elif cmd == ["pw-dump"]:
            out = json.dumps([{"id": 73, "info": {"props": {
                "media.class": "Audio/Sink", "node.name": "bluez_output.AA_BB_CC_DD_EE_FF.3"}}}])
        result = subprocess.CompletedProcess(command, rc, out)
        if check and rc:
            raise RuntimeError(out)
        return result


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.backend = Backend()
        self.root.joinpath("etc").mkdir()
        self.root.joinpath("etc/armbian-release").write_text("BOARD=t95\n")
        self.home = self.root / ACCOUNT.pw_dir.lstrip("/")
        self.home.mkdir(parents=True)
        self.chown = patch.object(setup.os, "chown")
        self.fchown = patch.object(setup.os, "fchown")
        self.chown.start()
        self.fchown.start()

    def tearDown(self):
        self.chown.stop()
        self.fchown.stop()
        self.tmp.cleanup()

    def manager(self, component):
        return setup.Setup(component, ACCOUNT.pw_name, self.root, self.backend)

    def board(self, alias=False):
        compatible = self.root / "proc/device-tree/compatible"
        compatible.parent.mkdir(parents=True)
        compatible.write_bytes(b"mbox,t95-axp313\0allwinner,sun50i-h616\0")
        firmware = self.root / "lib/firmware/brcm/BCM43342.hcd"
        firmware.parent.mkdir(parents=True)
        firmware.write_bytes(b"synthetic firmware fixture; not a redistributable chip blob")
        self.fw_patch = patch.object(setup, "FW_HASH", hashlib.sha256(firmware.read_bytes()).hexdigest())
        self.fw_patch.start()
        self.addCleanup(self.fw_patch.stop)
        device = self.root / "sys/devices/platform/soc/5000400.serial/serial0-0"
        driver = self.root / "sys/bus/serial/drivers/hci_uart_bcm"
        device.mkdir(parents=True)
        driver.mkdir(parents=True)
        (driver / "bind").touch()
        (driver / "unbind").touch()
        (device / "driver").symlink_to(driver)
        sysclass = self.root / "sys/class/bluetooth/hci0"
        sysclass.mkdir(parents=True)
        (sysclass / "device").symlink_to(device)
        sysbus = self.root / "sys/bus/serial/devices"
        sysbus.mkdir(parents=True)
        (sysbus / "serial0-0").symlink_to(device)
        fw_alias = firmware.with_name("BCM.mbox,t95-axp313.hcd")
        if alias:
            fw_alias.symlink_to("BCM43342.hcd")
        return firmware, fw_alias

    def test_dashboard_apply_idempotent_remove(self):
        before = self.root / "etc/default/armbian-motd"
        before.parent.mkdir()
        before.write_text("old settings\n")
        before.chmod(0o640)
        original = setup.fingerprint(before)
        extra = self.root / "etc/update-motd.d/77-unrelated"
        extra.parent.mkdir()
        extra.write_text("other module\n")
        manager = self.manager("dashboard")
        manager.install()
        self.assertEqual(len(manager.state["files"]), 14)
        self.assertEqual(self.root.joinpath(setup.DASHBOARD_USB_HELP_PATH.lstrip('/')).read_bytes(), setup.DASHBOARD_USB_HELP)
        baseline = manager.state_file.read_bytes()
        self.backend.calls.clear()
        manager.install()
        self.assertEqual(baseline, manager.state_file.read_bytes())
        self.assertFalse(any(c[0] == "apt-get" for c in self.backend.calls))
        # The installed local command can operate with the recorded baseline.
        restored = self.manager("dashboard")
        restored.remove()
        self.assertEqual(setup.fingerprint(before), original)
        self.assertEqual(extra.read_text(), "other module\n")
        self.assertFalse((self.root / "etc/update-motd.d/95-sd-card-stats").exists())
        self.assertFalse(self.root.joinpath(setup.DASHBOARD_USB_HELP_PATH.lstrip('/')).exists())

    def old_dashboard(self):
        manager = self.manager('dashboard')
        manager.install()
        target = manager.path(setup.DASHBOARD_USB_HELP_PATH)
        archived = setup.SOURCE / 'server/ssh-dashboard/2026-10-16/rootfs' / setup.DASHBOARD_USB_HELP_PATH.lstrip('/')
        target.write_bytes(archived.read_bytes())
        record = next(r for r in manager.state['files'] if r['path'] == str(target))
        record['installed'] = setup.fingerprint(target)
        manager.save()
        self.backend.calls.clear()
        return manager, target

    def test_existing_dashboard_gets_usb_hint_without_reinstalling_or_replacing_backup(self):
        manager, target = self.old_dashboard()
        original_records = json.loads(json.dumps(manager.state['files']))
        original_packages = list(manager.state['new_packages'])
        custom = self.root / 'etc/default/armbian-motd'
        custom.write_text('custom dashboard setting\n')
        manager.install()
        self.assertEqual(len(manager.state['files']), 14)
        for current, original in zip(manager.state['files'], original_records):
            self.assertEqual(current['before'], original['before'])
            self.assertEqual(current.get('backup'), original.get('backup'))
            if current['path'] != str(target):
                self.assertEqual(current, original)
        self.assertEqual(manager.state['new_packages'], original_packages)
        self.assertEqual(custom.read_text(), 'custom dashboard setting\n')
        self.assertEqual(target.read_bytes(), setup.DASHBOARD_USB_HELP)
        self.assertFalse(any(c[0] == 'apt-get' for c in self.backend.calls))

    def test_dashboard_hint_update_restores_existing_foreign_hint_on_removal(self):
        manager = self.manager('dashboard')
        target = manager.path(setup.DASHBOARD_USB_HELP_PATH)
        target.parent.mkdir(parents=True)
        target.write_text('previous hint\n')
        target.chmod(0o640)
        before = setup.fingerprint(target)
        manager.install()
        manager.remove()
        self.assertEqual(setup.fingerprint(target), before)
        self.assertEqual(target.read_text(), 'previous hint\n')

    def test_dashboard_hint_manual_edit_is_not_overwritten_by_repeat_install(self):
        manager = self.manager('dashboard')
        manager.install()
        target = manager.path(setup.DASHBOARD_USB_HELP_PATH)
        target.write_text('manual hint\n')
        original = manager.state_file.read_bytes()
        with self.assertRaisesRegex(ValueError, 'geänderte USB-Dashboard-Hilfe'):
            manager.install()
        self.assertEqual(target.read_text(), 'manual hint\n')
        self.assertEqual(manager.state_file.read_bytes(), original)

    def test_dashboard_hint_failed_update_leaves_existing_dashboard_and_journal_intact(self):
        manager, target = self.old_dashboard()
        original = manager.state_file.read_bytes()
        existing = {r['path']: Path(r['path']).read_bytes() for r in manager.state['files']}
        with patch.object(manager, 'cache_tools', side_effect=OSError('simulated cache failure')):
            with self.assertRaises(OSError): manager.install()
        self.assertTrue(target.exists())
        self.assertEqual(manager.state_file.read_bytes(), original)
        self.assertEqual(existing, {p: Path(p).read_bytes() for p in existing})

    def test_dashboard_hint_is_quiet_without_usb_tool_and_never_executes_it(self):
        script = self.root / 'hint.sh'
        script.write_bytes(setup.DASHBOARD_USB_HELP)
        syntax = subprocess.run(['/bin/bash', '-n', str(script)], capture_output=True, text=True)
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        binaries = self.root / 'bin'
        binaries.mkdir()
        marker = self.root / 'must-not-exist'
        env = {'PATH': str(binaries), 'LANG': 'C', 'T95_TEST_MARKER': str(marker)}
        result = subprocess.run(['/bin/bash', str(script)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        executable = binaries / 'usb-eject'
        executable.write_text('#!/bin/sh\n: > "$T95_TEST_MARKER"\nexit 99\n')
        executable.chmod(0o755)
        for locale, label, options in [
                ('C', 'Safely remove USB drives', {}),
                ('de_DE.UTF-8', 'USB-Laufwerke sicher entfernen', {}),
                ('C', 'Safely remove USB drives', {'NO_COLOR': '1'}),
                ('de_DE.UTF-8', 'USB-Laufwerke sicher entfernen', {'TERM': 'dumb'})]:
            with self.subTest(locale=locale, options=options):
                env['LANG'] = locale
                result = subprocess.run(['/bin/bash', str(script)], env=env | options, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                visible = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
                self.assertIn(label, visible)
                self.assertIn('sudo usb-eject --status', visible)
                self.assertIn('sudo usb-eject "NAME"', visible)
                self.assertIn('Tips:', visible)
                self.assertNotIn('Imager', visible)
                self.assertNotIn('Proxmox', visible)
                self.assertTrue(all(len(line) <= 64 for line in visible.splitlines()))
                if options:
                    self.assertNotIn('\x1b[', result.stdout)
                else:
                    self.assertIn('\x1b[1;36m' + label, result.stdout)
                    self.assertIn('\x1b[1;92msudo usb-eject --status', result.stdout)
                self.assertFalse(marker.exists())

    def test_dashboard_tampered_payload_refused_before_apt(self):
        source = self.root / "payload"
        shutil.copytree(setup.SOURCE / "server/ssh-dashboard", source / "server/ssh-dashboard")
        (source / "server/ssh-dashboard/2026-10-16/rootfs/etc/default/armbian-motd").write_text("tampered")
        with patch.object(setup, "SOURCE", source):
            with self.assertRaisesRegex(ValueError, "Prüfsumme"):
                self.manager("dashboard").install()
        self.assertFalse(any(c[0] == "apt-get" for c in self.backend.calls))
        self.assertFalse((self.root / "etc/default/armbian-motd").exists())

    def test_redirected_destination_rolls_back(self):
        target = self.root / "etc/default/armbian-motd"
        target.parent.mkdir()
        protected = self.root / "protected"
        protected.write_text("untouched")
        target.symlink_to(protected)
        with self.assertRaisesRegex(ValueError, "Umgeleitete"):
            self.manager("dashboard").install()
        self.assertEqual(protected.read_text(), "untouched")
        self.assertTrue(target.is_symlink())

    def test_manual_edit_blocks_removal_and_force_is_explicit(self):
        manager = self.manager("dashboard")
        manager.install()
        target = self.root / "etc/default/armbian-motd"
        target.write_text("manual change")
        with self.assertRaisesRegex(ValueError, "geänderte Dateien"):
            manager.remove()
        self.assertEqual(target.read_text(), "manual change")
        self.assertEqual(manager.state["phase"], "installed")
        manager.remove(force=True)
        self.assertFalse(target.exists())

    def test_bluetooth_install_audio_remove_keeps_data_and_shared_services(self):
        firmware, alias = self.board()
        original_hash = setup.fingerprint(firmware)["sha256"]
        state_parent = self.home / ".local/state"
        state_parent.mkdir(parents=True)
        sentinel = state_parent / "samba-existing"
        sentinel.write_text("do not touch")
        manager = self.manager("bluetooth")
        manager.install()
        self.assertEqual(os.readlink(alias), "BCM43342.hcd")
        self.assertEqual(setup.fingerprint(firmware)["sha256"], original_hash)
        config = self.home / ".config/mpd/mpd.conf"
        self.assertIn('bind_to_address "127.0.0.1"', config.read_text())
        self.assertIn('target "t95.bluetooth.unselected"', config.read_text())
        self.assertNotIn(".local/state", config.read_text())
        routing = self.home / ".config/pipewire/client.conf.d/51-t95-mpd-target.conf"
        self.assertTrue(routing.is_file())
        manager.audio("AA:BB:CC:DD:EE:FF")
        self.assertIn('target "bluez_output.AA_BB_CC_DD_EE_FF.3"', config.read_text())
        self.assertTrue(any(c[-4:] == ["wpctl", "set-volume", "73", "0.20"] for c in self.backend.calls))
        music_file = Path(manager.state["music"]) / "user-song.txt"
        music_file.write_text("personal data")
        self.backend.calls.clear()
        manager.remove()
        self.assertFalse(alias.exists())
        self.assertFalse(config.exists())
        self.assertFalse(routing.exists())
        self.assertEqual(music_file.read_text(), "personal data")
        self.assertEqual(sentinel.read_text(), "do not touch")
        self.assertEqual(manager.state["phase"], "removed")
        self.assertTrue(self.backend.units[(False, "bluetooth.service")]["active"])
        self.assertTrue(self.backend.units[(True, "pipewire.service")]["active"])
        self.assertFalse(any(c[0] == "loginctl" for c in self.backend.calls))
        self.assertFalse(any("smbd" in " ".join(c) or "ssh" in " ".join(c) for c in self.backend.calls))

    def test_preexisting_firmware_alias_is_retained(self):
        _, alias = self.board(alias=True)
        manager = self.manager("bluetooth")
        manager.install()
        self.assertFalse(any(r["path"] == str(alias) for r in manager.state["files"]))
        manager.remove()
        self.assertTrue(alias.is_symlink())

    def test_failed_bluetooth_install_restores_prior_config_and_can_be_removed(self):
        _, alias = self.board()
        config = self.home / ".config/mpd/mpd.conf"
        config.parent.mkdir(parents=True)
        config.write_text("prior user configuration")
        self.backend.fail_enable = True
        manager = self.manager("bluetooth")
        with self.assertRaisesRegex(RuntimeError, "simulated"):
            manager.install()
        self.assertEqual(config.read_text(), "prior user configuration")
        self.assertFalse(alias.exists())
        self.assertEqual(manager.state["phase"], "failed")
        self.assertEqual(manager.conflicts(), [])
        manager.remove()
        self.assertEqual(config.read_text(), "prior user configuration")

    def test_package_removal_never_removes_preexisting_or_extra_packages(self):
        manager = self.manager("dashboard")
        manager.install()
        self.assertNotIn("curl", manager.state["new_packages"])
        self.backend.extra_remove = True
        with self.assertRaisesRegex(ValueError, "weitere Pakete"):
            manager.remove(purge=True)
        self.assertFalse(any(c[:2] == ["apt-get", "remove"] for c in self.backend.calls))
        self.backend.extra_remove = False
        manager.remove(purge=True)
        removals = [c for c in self.backend.calls if c[:2] == ["apt-get", "remove"]]
        self.assertEqual(len(removals), 1)
        self.assertNotIn("curl", removals[0])
        self.assertNotIn("autoremove", removals[0])

    def test_early_apt_failure_cleanup_does_not_require_radio_tools(self):
        self.board()
        self.backend.fail_apt = True
        manager = self.manager("bluetooth")
        with self.assertRaisesRegex(RuntimeError, "APT failure"):
            manager.install()
        self.assertTrue(all("installed" not in r for r in manager.state["files"]))
        self.backend.calls.clear()
        manager.remove()
        self.assertEqual(manager.state["phase"], "removed")
        self.assertFalse(any(c[0] == "rfkill" for c in self.backend.calls))

    def test_invalid_audio_address_has_no_side_effect(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        baseline = manager.state_file.read_bytes()
        self.backend.calls.clear()
        with self.assertRaisesRegex(ValueError, "Aufruf"):
            manager.audio('AA:BB:CC:DD:EE:FF"; command')
        self.assertEqual(manager.state_file.read_bytes(), baseline)
        self.assertEqual(self.backend.calls, [])

    def test_wrong_board_refused_without_install_journal(self):
        self.board()
        (self.root / "proc/device-tree/compatible").write_bytes(b"other,board\0")
        manager = self.manager("bluetooth")
        with self.assertRaisesRegex(ValueError, "Board"):
            manager.install()
        self.assertFalse(manager.state_file.exists())
        self.assertEqual(self.backend.calls, [])

    def test_radio_off_on_preserves_pairings_and_server(self):
        manager = self.manager("bluetooth")
        pairing = self.root / "var/lib/bluetooth/test-bond"
        pairing.parent.mkdir(parents=True)
        pairing.write_text("keep pairing")
        manager.radio("off")
        manager.radio("on")
        self.assertEqual(pairing.read_text(), "keep pairing")
        self.assertIn(["rfkill", "block", "bluetooth"], self.backend.calls)
        self.assertIn(["rfkill", "unblock", "bluetooth"], self.backend.calls)
        self.assertFalse(any("reboot" in c or "shutdown" in c or "apt-get" in c for c in self.backend.calls))

    def test_audio_backup_is_private_and_precedes_package_changes(self):
        self.board()
        config = self.home / ".config/mpd/mpd.conf"
        config.parent.mkdir(parents=True)
        config.write_text("original audio configuration")
        config.chmod(0o640)
        normal = self.backend
        manager = self.manager("bluetooth")
        def packages_change_config(command, check=True, timeout=120):
            if command[:2] == ["apt-get", "install"]:
                backup = manager.state["audio_backup"]
                archive = Path(backup["path"])
                self.assertEqual(archive.stat().st_mode & 0o777, 0o600)
                self.assertEqual(manager.state_dir.stat().st_mode & 0o777, 0o700)
                self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), backup["sha256"])
                with tarfile.open(archive) as saved:
                    member = saved.getmember(str(config.relative_to(self.root)))
                    self.assertEqual(member.mode, 0o640)
                    self.assertEqual(saved.extractfile(member).read(), b"original audio configuration")
                config.write_text("package changed this before setup writes")
            return normal(command, check, timeout)
        manager.run = packages_change_config
        manager.install()
        manager.remove()
        self.assertEqual(config.read_text(), "original audio configuration")
        self.assertEqual(config.stat().st_mode & 0o777, 0o640)

    def test_failed_package_install_restores_prepared_config_before_setup_write(self):
        self.board()
        config = self.home / ".config/mpd/mpd.conf"
        config.parent.mkdir(parents=True)
        config.write_text("before package transaction")
        manager = self.manager("bluetooth")
        normal = self.backend
        def partial_install(command, check=True, timeout=120):
            if command[:2] == ["apt-get", "install"]:
                config.write_text("partially changed by packages")
                raise RuntimeError("simulated partial package failure")
            return normal(command, check, timeout)
        manager.run = partial_install
        with self.assertRaisesRegex(RuntimeError, "partial package failure"):
            manager.install()
        self.assertEqual(config.read_text(), "before package transaction")
        self.assertEqual(manager.state["phase"], "failed")

    def test_failed_audio_backup_prevents_package_installation(self):
        self.board()
        manager = self.manager("bluetooth")
        with patch.object(setup.tarfile, "open", side_effect=OSError("backup failed")):
            with self.assertRaisesRegex(OSError, "backup failed"):
                manager.install()
        self.assertFalse(any(c[0] == "apt-get" for c in self.backend.calls))
        self.assertEqual(manager.state["phase"], "failed")

    def test_cleanup_after_failed_preflight_does_not_stop_unrecorded_services(self):
        self.board()
        manager = self.manager("bluetooth")
        with self.assertRaisesRegex(ValueError, "Musikpfad"):
            manager.install(music="relative-music-directory")
        self.assertEqual(manager.state["services"], [])
        self.backend.calls.clear()
        manager.remove()
        self.assertFalse(any("stop" in c or "restart" in c for c in self.backend.calls))
        self.assertEqual(manager.state["phase"], "removed")

    def test_repeated_audio_install_preserves_the_first_configuration_archive(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        archive = Path(manager.state["audio_backup"]["path"])
        before = archive.read_bytes()
        self.backend.calls.clear()
        manager.install()
        self.assertEqual(archive.read_bytes(), before)
        self.assertFalse(any(c[0] == "apt-get" for c in self.backend.calls))

    def test_legacy_mpd_configuration_is_backed_up_and_restored(self):
        self.board()
        legacy = self.home / ".mpdconf"
        legacy.write_text("the previous manual player configuration")
        legacy.chmod(0o600)
        manager = self.manager("bluetooth")
        manager.install()
        self.assertFalse(legacy.exists())
        manager.remove()
        self.assertEqual(legacy.read_text(), "the previous manual player configuration")
        self.assertEqual(legacy.stat().st_mode & 0o777, 0o600)

    def test_remove_restores_preexisting_active_player_and_audio_services(self):
        self.board()
        self.backend.packages.update(setup.PACKAGES["bluetooth"])
        # Matches the reported box: all audio daemons existed before setup.
        for unit in setup.USER_UNITS:
            self.backend.units[(True, unit)] = {"active": unit != "mpdris2.service", "enabled": "enabled"}
        manager = self.manager("bluetooth")
        manager.install()
        manager.remove(purge=True)
        for record in manager.state["services"]:
            observed = self.backend.units[(record["scope"] == "user", record["unit"])]
            self.assertEqual(observed["active"], record["active"], record["unit"])
            self.assertEqual(observed["enabled"], record["enabled"], record["unit"])
        self.assertEqual(manager.state["phase"], "removed")
        self.assertFalse(any("--global" in c and "disable" in c for c in self.backend.calls))

    def test_failed_player_stop_cannot_report_removed(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        self.backend.fail_stop = "mpd.service"
        with self.assertRaisesRegex(RuntimeError, "stop failure"):
            manager.remove()
        self.assertNotEqual(manager.state["phase"], "removed")

    def test_unrestored_service_state_cannot_report_removed_and_can_retry(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        self.backend.ignore_stop = "wireplumber.service"
        with self.assertRaisesRegex(RuntimeError, "Dienstzustand"):
            manager.remove()
        self.assertEqual(manager.state["phase"], "restoring")
        self.backend.ignore_stop = None
        manager.remove()
        self.assertEqual(manager.state["phase"], "removed")

    def test_failed_bluetooth_package_removal_does_not_report_complete(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        self.backend.extra_remove = True
        with self.assertRaisesRegex(ValueError, "weitere Pakete"):
            manager.remove(purge=True)
        self.assertEqual(manager.state["phase"], "restoring")
        self.backend.extra_remove = False
        manager.remove(purge=True)
        self.assertEqual(manager.state["phase"], "removed")

    def test_shared_session_bus_is_kept_for_samba_automount(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        self.assertIn("dbus-user-session", manager.state["new_packages"])
        unit = self.home / ".config/systemd/user/udiskie.service"
        unit.write_text("Samba automount must survive audio rollback")
        manager.remove(purge=True)
        self.assertIn("dbus-user-session", self.backend.packages)
        self.assertEqual(unit.read_text(), "Samba automount must survive audio rollback")

    def test_rfkill_switch_is_restored_after_its_package_was_removed(self):
        self.board()
        switch = self.root / "sys/class/rfkill/rfkill4"
        switch.mkdir(parents=True)
        (switch / "type").write_text("bluetooth\n")
        (switch / "name").write_text("hci0\n")
        (switch / "soft").write_text("1\n")
        manager = self.manager("bluetooth")
        manager.install()
        (switch / "soft").write_text("0\n")
        self.backend.calls.clear()
        manager.remove(purge=True)
        self.assertNotIn("rfkill", self.backend.packages)
        self.assertEqual((switch / "soft").read_text(), "1\n")
        self.assertFalse(any(c[0] == "rfkill" for c in self.backend.calls))

    def test_runtime_enable_state_is_restored(self):
        self.board()
        self.backend.packages.add("mpdris2")
        self.backend.units[(True, "mpdris2.service")] = {"enabled": "enabled-runtime", "active": False}
        manager = self.manager("bluetooth")
        manager.install()
        manager.remove()
        self.assertEqual(self.backend.units[(True, "mpdris2.service")],
                         {"enabled": "enabled-runtime", "active": False})

    def test_status_does_not_activate_an_inactive_bluetooth_service(self):
        manager = self.manager("bluetooth")
        self.backend.units[(False, "bluetooth.service")] = {"enabled": "disabled", "active": False}
        normal = self.backend
        def missing_rfkill(command, check=True, timeout=120):
            if command[0] == "rfkill":
                return subprocess.CompletedProcess(command, 127, "missing")
            return normal(command, check, timeout)
        manager.run = missing_rfkill
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            manager.status()
        self.assertIn("rfkill nicht installiert", printed.getvalue())
        self.assertFalse(any(c[0] == "bluetoothctl" for c in self.backend.calls))
        self.assertFalse(any("start" in c or "restart" in c for c in self.backend.calls))

    def test_old_removed_journal_restores_services_without_overwriting_later_files(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        manager.restore_files()
        manager.state["phase"] = "removed"
        del manager.state["radio_before"]
        manager.save()
        self.backend.units[(True, "pipewire.service")]["active"] = False
        user_file = self.home / ".config/mpd/mpd.conf"
        user_file.write_text("configuration changed after old removal")
        cached = self.root / "usr/local/lib/t95-setup/server/setup/t95_setup.py"
        cached.write_text("old cached setup version")
        manager.remove()
        self.assertTrue(self.backend.units[(True, "pipewire.service")]["active"])
        self.assertEqual(user_file.read_text(), "configuration changed after old removal")
        self.assertEqual(manager.state["phase"], "removed")
        self.assertEqual(cached.read_bytes(), MODULE.read_bytes())

    def test_old_removed_journal_retry_keeps_files_changed_after_original_removal(self):
        self.board()
        manager = self.manager("bluetooth")
        manager.install()
        manager.restore_files()
        manager.state["phase"] = "removed"
        manager.save()
        user_file = self.home / ".config/mpd/mpd.conf"
        user_file.write_text("keep later manual audio configuration")
        self.backend.fail_stop = "mpd.service"
        with self.assertRaisesRegex(RuntimeError, "stop failure"):
            manager.remove()
        self.assertEqual(manager.state["phase"], "restoring")
        self.backend.fail_stop = None
        # A fresh invocation must remember that files were already removed.
        manager = self.manager("bluetooth")
        manager.remove()
        self.assertEqual(manager.state["phase"], "removed")
        self.assertEqual(user_file.read_text(), "keep later manual audio configuration")


if __name__ == "__main__":
    unittest.main()

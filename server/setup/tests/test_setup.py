"""Filesystem fixtures + fake package/service backend; never changes the host."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tempfile
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
        self.packages = {"bluez", "curl", "procps", "iproute2", "util-linux"}
        self.extra_remove = False
        self.fail_enable = False
        self.fail_apt = False

    def __call__(self, command, check=True, timeout=120):
        self.calls.append(command)
        cmd = command
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
            if "is-enabled" in cmd:
                out = "enabled" if cmd[-1] in ("bluetooth.service", "pipewire.service") else "disabled"
            elif "is-active" in cmd:
                out = "active" if cmd[-1] in ("bluetooth.service", "pipewire.service") else "inactive"
            elif self.fail_enable and "enable" in cmd and "wireplumber.service" in cmd:
                self.fail_enable = False
                out, rc = "simulated service failure", 1
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
        self.assertTrue(any(c == ["rfkill", "block", "bluetooth"] for c in self.backend.calls))
        self.assertFalse(any("stop" in c and c[-1] == "pipewire.service" for c in self.backend.calls))
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
        self.assertEqual(manager.state["files"], [])
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


if __name__ == "__main__":
    unittest.main()

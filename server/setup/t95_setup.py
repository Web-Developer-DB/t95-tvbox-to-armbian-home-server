#!/usr/bin/env python3
"""T95: Dashboard und Bluetooth-Musikplayer installieren, bedienen, zurücknehmen."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

SOURCE = Path(__file__).resolve().parents[2]
FW_HASH = "09970c63b7a0fc677915195923739ddac5e9ee8d589ef9f4b0ded7370684874f"
PACKAGES = {
    "dashboard": ["figlet", "curl", "jq", "procps", "iproute2", "util-linux"],
    "bluetooth": ["bluez", "pipewire", "pipewire-pulse", "wireplumber",
                  "libspa-0.2-bluetooth", "mpd", "mpc", "mpdris2",
                  "dbus-user-session", "python3-dbus", "python3-gi", "usbutils", "rfkill"],
}
USER_UNITS = ["pipewire.socket", "pipewire-pulse.socket", "pipewire.service",
              "pipewire-pulse.service", "wireplumber.service", "mpd.service",
              "mpdris2.service", "mpris-proxy.service"]
PLAYER_UNITS = ["mpdris2.service", "mpd.service", "mpris-proxy.service"]
USER_AUDIO_CONFIGS = [
    ".mpdconf", ".config/mpd/mpd.conf", ".config/mpDris2/mpDris2.conf",
    ".config/pipewire/client.conf.d/51-t95-mpd-target.conf",
    ".config/systemd/user/mpdris2.service",
    ".config/systemd/user/wireplumber.service.d/51-t95-state.conf",
    ".config/wireplumber/wireplumber.conf.d/51-t95-headless-bluetooth.conf",
]

DASHBOARD_USB_HELP_PATH = "/etc/update-motd.d/35-armbian-tips"
DASHBOARD_USB_HELP = r'''#!/bin/bash
# T95 dashboard: display-only USB cheat sheet. Never execute the shown commands.
command -v usb-eject >/dev/null 2>&1 || exit 0

reset='' section_color='' title_color='' label_color='' command_color='' note_color=''
# PAM may omit TERM; Bash's implicit, unexported "dumb" is not a user preference.
if [[ -z ${NO_COLOR:-} && ( ${TERM:-} != dumb || ${TERM@a} != *x* ) ]]; then
    reset=$'\033[0m'
    section_color=$'\033[0;90m'
    title_color=$'\033[1;36m'
    label_color=$'\033[1;33m'
    command_color=$'\033[1;92m'
    note_color=$'\033[0;37m'
fi

case "${LC_ALL:-${LC_MESSAGES:-${LANG:-C}}}" in
    de*)
        heading='USB-Laufwerke sicher entfernen'
        status_label='1 Status/Freigaben'
        eject_label='2 Laufwerk auswerfen'
        name_help='= Freigabename aus dem Status.'
        scope_help='Gilt für das ganze USB-Laufwerk mit allen Partitionen.'
        warning_label='Wichtig:'
        transfer_help='Dateiübertragungen zuerst beenden.'
        unplug_help='Erst nach Erfolgsmeldung abziehen.'
        ;;
    *)
        heading='Safely remove USB drives'
        status_label='1 Status and shares'
        eject_label='2 Eject drive'
        name_help='= share name shown by status.'
        scope_help='Whole USB drive, including all its partitions.'
        warning_label='Important:'
        transfer_help='Finish file transfers first.'
        unplug_help='Unplug only after the success message.'
        ;;
esac

printf '\n%s Tips:%s\n\n' "$section_color" "$reset"
printf ' %s%s%s\n\n' "$title_color" "$heading" "$reset"
printf '  %s%-20s%s  %s%s%s\n' "$label_color" "$status_label" "$reset" \
    "$command_color" 'sudo usb-eject --status' "$reset"
printf '  %s%-20s%s  %s%s%s\n' "$label_color" "$eject_label" "$reset" \
    "$command_color" 'sudo usb-eject "NAME"' "$reset"
printf '\n  %sNAME%s %s%s%s\n' "$title_color" "$reset" "$note_color" "$name_help" "$reset"
printf '  %s%s%s\n\n' "$note_color" "$scope_help" "$reset"
printf '  %s%s%s %s%s%s\n' "$label_color" "$warning_label" "$reset" \
    "$note_color" "$transfer_help" "$reset"
printf '  %*s %s%s%s\n\n' "${#warning_label}" '' "$note_color" "$unplug_help" "$reset"
'''.encode('utf-8')


def run(command, check=True, timeout=120):
    try:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout)
    except FileNotFoundError as error:
        if check:
            raise
        return subprocess.CompletedProcess(command, 127, str(error))
    if check and result.returncode:
        raise RuntimeError(f"{shlex.join(command)}\n{result.stdout.strip()}")
    return result


def fingerprint(path):
    if path.is_symlink():
        return {"kind": "link", "target": os.readlink(path)}
    if not path.exists():
        return {"kind": "absent"}
    if not path.is_file():
        raise ValueError(f"Keine reguläre Datei: {path}")
    metadata = path.stat()
    return {"kind": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mode": stat.S_IMODE(metadata.st_mode), "uid": metadata.st_uid, "gid": metadata.st_gid}


def atomic_file(path, data, mode=0o644, owner=None):
    fd, name = tempfile.mkstemp(prefix=".t95-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            os.fchmod(output.fileno(), mode)
            if owner is not None:
                os.fchown(output.fileno(), *owner)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def check_destination(path, allow_link=False):
    if any(p.is_symlink() for p in path.parents):
        raise ValueError(f"Umgeleitetes Konfigurationsverzeichnis: {path.parent}")
    if path.is_symlink() and not allow_link:
        raise ValueError(f"Umgeleitete Zieldatei: {path}")
    if path.exists() and not path.is_file() and not (allow_link and path.is_symlink()):
        raise ValueError(f"Keine reguläre Zieldatei: {path}")


class Setup:
    def __init__(self, component, username=None, root=Path("/"), runner=run):
        self.component = component
        self.root = root.resolve()
        self.run = runner
        self.state_dir = self.path("/var/lib/t95-setup") / component
        self.state_file = self.state_dir / "state.json"
        self.state = json.loads(self.state_file.read_text()) if self.state_file.exists() else None
        saved_user = self.state.get("user") if self.state else None
        sudo_user = os.environ.get("SUDO_USER")
        username = username or saved_user or (sudo_user if sudo_user != "root" else None)
        self.user = None
        if username:
            if not re.fullmatch(r"[a-z_][a-z0-9_-]*\$?", username):
                raise ValueError("Ungültiger Benutzername")
            account = pwd.getpwnam(username)
            if account.pw_uid == 0:
                raise ValueError("Bitte einen normalen Benutzer mit --user angeben")
            self.user = username
            self.uid, self.gid = account.pw_uid, account.pw_gid
            self.home = self.path(account.pw_dir).resolve()
        if saved_user and self.user != saved_user:
            raise ValueError(f"Diese Installation gehört zu {saved_user}")

    def path(self, absolute):
        p = Path(absolute)
        if not p.is_absolute() or ".." in p.parts:
            raise ValueError(f"Ungültiger Pfad: {p}")
        return self.root / p.relative_to("/")

    def user_run(self, args, check=True):
        if not self.user:
            raise ValueError("Benutzer fehlt: --user NAME angeben")
        return self.run(["runuser", "-u", self.user, "--", "env",
                         f"HOME={self.home}", f"USER={self.user}",
                         f"XDG_RUNTIME_DIR=/run/user/{self.uid}",
                         f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{self.uid}/bus", *args], check=check)

    def service(self, scope, args, check=True):
        if scope == "user":
            return self.user_run(["systemctl", "--user", *args], check)
        return self.run(["systemctl", *args], check=check)

    def unit_load_state(self, scope, unit):
        result = self.service(scope, ["show", unit, "--property=LoadState", "--value"], False)
        value = result.stdout.strip()
        if result.returncode and value != "not-found":
            raise RuntimeError(f"Dienst nicht prüfbar: {unit}: {value}")
        return value

    def save(self):
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.state_dir.chmod(0o700)
        atomic_file(self.state_file, (json.dumps(self.state, indent=2) + "\n").encode(), 0o600)

    def begin(self):
        if self.state and self.state["phase"] != "removed":
            if self.state["phase"] == "installed":
                print("Bereits installiert. Für Änderungen zuerst remove ausführen.")
                return False
            raise ValueError("Unvollständige Installation: zuerst remove zur Rücknahme ausführen")
        if self.state_dir.exists():
            archive = self.state_dir.with_name(self.component + "-" + str(time.time_ns()))
            self.state_dir.rename(archive)
        self.state = {"schema": 1, "component": self.component, "user": self.user,
                      "phase": "preparing", "files": [], "directories": [],
                      "services": [], "new_packages": [], "created": datetime.now(timezone.utc).isoformat()}
        self.save()
        return True

    def directory(self, directory, user=False):
        missing = []
        current = directory
        while not current.exists():
            missing.append(current)
            current = current.parent
        # /lib may be the standard usr-merge symlink. Canonicalize that prefix
        # before calling this method; refuse redirected user configuration paths.
        if any(p.is_symlink() for p in (directory, *directory.parents) if p != self.root):
            raise ValueError(f"Umgeleitetes Konfigurationsverzeichnis: {directory}")
        for p in reversed(missing):
            p.mkdir(mode=0o755)
            if user:
                os.chown(p, self.uid, self.gid)
            self.state["directories"].append(str(p))
            self.save()

    def remember(self, path, allow_link=False):
        """Save the original before package installation or file mutation."""
        check_destination(path, allow_link=allow_link)
        record = next((r for r in self.state["files"] if r["path"] == str(path)), None)
        if record is None:
            record = {"path": str(path), "before": fingerprint(path)}
            if record["before"]["kind"] == "file":
                backup = self.state_dir / f"file-{len(self.state['files'])}"
                atomic_file(backup, path.read_bytes(), 0o600)
                record["backup"] = str(backup)
            self.state["files"].append(record)
            self.save()  # Journal before mutation, including power-loss recovery.
        return record

    def write(self, path, data=None, mode=0o644, user=False, link=None):
        record = self.remember(path, allow_link=link is not None)
        self.directory(path.parent, user)
        if path.is_symlink() and link is None:
            raise ValueError(f"Umgeleitete Zieldatei: {path}")
        if link is not None:
            temporary = path.with_name(".t95-link-" + str(time.time_ns()))
            try:
                temporary.symlink_to(link)
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        else:
            atomic_file(path, data, mode, (self.uid, self.gid) if user else (0, 0))
        record["installed"] = fingerprint(path)
        self.save()

    def conflicts(self):
        return [r["path"] for r in self.state["files"]
                if "installed" in r and fingerprint(Path(r["path"])) != r["installed"]]

    def restore_files(self):
        # Verify every backup before modifying any target.
        for record in self.state["files"]:
            if record["before"]["kind"] == "file":
                if fingerprint(Path(record["backup"]))["sha256"] != record["before"]["sha256"]:
                    raise ValueError("Sicherungsdatei beschädigt; Abbruch")
        for record in reversed(self.state["files"]):
            if "installed" not in record and fingerprint(Path(record["path"])) == record["before"]:
                # Do not create directories for an untouched preflight backup.
                # APT can nevertheless have changed a prepared target before
                # failing; in that case its original still must be restored.
                continue
            path, old = Path(record["path"]), record["before"]
            self.directory(path.parent, user=self.user and path.is_relative_to(self.home))
            if old["kind"] == "file":
                atomic_file(path, Path(record["backup"]).read_bytes(), old["mode"], (old["uid"], old["gid"]))
            elif old["kind"] == "link":
                temp = path.with_name(".t95-restore-" + str(time.time_ns()))
                temp.symlink_to(old["target"])
                temp.replace(path)
            else:
                path.unlink(missing_ok=True)
            record["installed"] = fingerprint(path)
        self.save()
        # Runtime state/music/playlist directories are deliberately retained.

    def snapshot_services(self):
        for scope, units in [("system", ["bluetooth.service", "mpd.socket", "mpd.service"]),
                             ("user", USER_UNITS)]:
            for unit in units:
                if self.unit_load_state(scope, unit) == "not-found":
                    enabled, active = "not-found", False
                else:
                    enabled = self.service(scope, ["is-enabled", unit], False).stdout.strip()
                    active = self.service(scope, ["is-active", unit], False).stdout.strip() == "active"
                self.state["services"].append(dict(scope=scope, unit=unit, enabled=enabled, active=active))
        self.state["linger_before"] = self.run(
            ["loginctl", "show-user", self.user, "-p", "Linger", "--value"], check=False).stdout.strip()
        self.save()

    def restore_services(self):
        if not self.state["services"]:
            return
        for scope in ("system", "user"):
            self.service(scope, ["daemon-reload"])
        for record in self.state["services"]:
            scope, unit = record["scope"], record["unit"]
            if self.unit_load_state(scope, unit) == "not-found":
                if record["active"] or record["enabled"] in ("enabled", "enabled-runtime"):
                    raise RuntimeError(f"Früher vorhandener Dienst fehlt: {unit}; Rücknahme unvollständig")
                continue
            self.service(scope, ["disable", unit])
            if record["enabled"] in ("enabled", "enabled-runtime"):
                args = ["enable", unit]
                if record["enabled"] == "enabled-runtime":
                    args.insert(1, "--runtime")
                self.service(scope, args)
            elif record["enabled"] in ("masked", "masked-runtime"):
                args = ["mask", "--now", unit]
                if record["enabled"] == "masked-runtime":
                    args.insert(1, "--runtime")
                self.service(scope, args)
            # Reload restored PipeWire/WirePlumber/MPD configuration into memory.
            # A plain start leaves an already running service on setup settings.
            self.service(scope, ["restart" if record["active"] else "stop", unit])
        # Check the final graph: starting a later unit may activate an earlier
        # socket or dependency, so per-command success alone is insufficient.
        for record in self.state["services"]:
            scope, unit = record["scope"], record["unit"]
            if self.unit_load_state(scope, unit) == "not-found":
                continue
            actual = self.service(scope, ["is-active", unit], False).stdout.strip()
            if (actual == "active") != record["active"]:
                raise RuntimeError(f"Dienstzustand nicht wiederhergestellt: {unit}: {actual}")
            enabled = self.service(scope, ["is-enabled", unit], False).stdout.strip()
            expected = record["enabled"]
            allowed = {"disabled", "static", "not-found"} if expected == "not-found" else {expected}
            if enabled not in allowed:
                raise RuntimeError(f"Autostart nicht wiederhergestellt: {unit}: {enabled} statt {expected}. "
                                   "Bei neu hinzugefügten Paketen remove --remove-packages verwenden.")

    def backup_audio_configuration(self):
        """Private reference snapshot plus per-file automatic rollback journal."""
        for relative in USER_AUDIO_CONFIGS:
            self.remember(self.home / relative)
        paths = [self.path(p) for p in (
            "/etc/mpd.conf", "/etc/default/mpd", "/etc/bluetooth",
            "/etc/pipewire", "/etc/wireplumber", "/etc/pulse")]
        paths += [self.home / p for p in (
            ".mpdconf", ".config/mpd", ".config/mpDris2", ".config/pipewire",
            ".config/wireplumber", ".config/pulse")]
        for unit in USER_UNITS:
            paths += [self.home / ".config/systemd/user" / unit,
                      self.home / ".config/systemd/user" / (unit + ".d")]
        archive = self.state_dir / "audio-before-setup.tar.gz"
        def regular_configs(member):
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise ValueError(f"Keine Konfigurationsdatei: {member.name}")
            return member
        # Opening with xb avoids overwriting the first snapshot on retries.
        with archive.open("xb") as output:
            os.fchmod(output.fileno(), 0o600)
            with tarfile.open(fileobj=output, mode="w:gz", dereference=False) as backup:
                for path in paths:
                    if path.exists() or path.is_symlink():
                        backup.add(path, arcname=str(path.relative_to(self.root)), filter=regular_configs)
        self.state["audio_backup"] = {"path": str(archive),
                                     "sha256": fingerprint(archive)["sha256"]}
        self.state["radio_before"] = []
        rfkill = self.path("/sys/class/rfkill")
        for entry in sorted(rfkill.glob("rfkill*")):
            if (entry / "type").read_text().strip() == "bluetooth":
                self.state["radio_before"].append({"name": (entry / "name").read_text().strip(),
                                                   "soft": (entry / "soft").read_text().strip()})
        if any(r["unit"] == "bluetooth.service" and r["active"] for r in self.state["services"]):
            shown = self.run(["bluetoothctl", "--timeout", "3", "show"], check=False)
            powered = re.search(r"^\s*Powered: (yes|no)\s*$", shown.stdout, re.M)
            if powered:
                self.state["controller_powered_before"] = powered[1] == "yes"
        self.save()
        print("Audio-Konfiguration vor Installation gesichert:", archive, flush=True)

    def restore_radio(self):
        if "radio_before" not in self.state:
            print("Hinweis: Protokoll ohne vorherigen Funkzustand; Funk unverändert.")
            return
        for previous in self.state["radio_before"]:
            matches = [p for p in self.path("/sys/class/rfkill").glob("rfkill*")
                       if (p / "type").read_text().strip() == "bluetooth"
                       and (p / "name").read_text().strip() == previous["name"]]
            if len(matches) != 1:
                raise RuntimeError("Vorheriges Bluetooth-Funkgerät nicht eindeutig gefunden")
            entry = matches[0]
            if (entry / "soft").read_text().strip() != previous["soft"]:
                # rfkill may itself have been a newly added package and is no
                # longer available after package rollback. Restore just this
                # captured kernel switch, never all radios indiscriminately.
                (entry / "soft").write_text(previous["soft"] + "\n")
                if (entry / "soft").read_text().strip() != previous["soft"]:
                    raise RuntimeError("Vorheriger Bluetooth-Funkzustand nicht wiederhergestellt")
        if "controller_powered_before" in self.state:
            self.bt("power", "on" if self.state["controller_powered_before"] else "off")

    def install_packages(self):
        owned = []
        for package in PACKAGES[self.component]:
            result = self.run(["dpkg-query", "-W", "-f=${Status}", package], check=False)
            if result.stdout.strip() != "install ok installed":
                owned.append(package)
        self.state["new_packages"] = owned
        self.save()
        print("Paketlisten aktualisieren und benötigte Pakete installieren …", flush=True)
        self.run(["apt-get", "update"], timeout=900)
        self.run(["apt-get", "install", "-y", "--no-install-recommends", *PACKAGES[self.component]], timeout=1800)

    def cache_tools(self):
        destination = self.path("/usr/local/lib/t95-setup")
        manager = destination / "server/setup/t95_setup.py"
        check_destination(manager)
        manager.parent.mkdir(parents=True, exist_ok=True)
        atomic_file(manager, Path(__file__).read_bytes())
        # Cached payload permits dashboard removal without network access.
        archive = SOURCE / "server/ssh-dashboard/2026-10-16"
        cached = destination / "server/ssh-dashboard/2026-10-16"
        if archive.resolve() != cached.resolve():
            shutil.copytree(archive, cached, dirs_exist_ok=True)
        for component in ("bluetooth", "dashboard"):
            wrapper = self.path(f"/usr/local/bin/t95-{component}")
            check_destination(wrapper)
            wrapper.parent.mkdir(parents=True, exist_ok=True)
            content = ("#!/usr/bin/env bash\n# T95 managed command\nset -euo pipefail\n"
                       f"if [[ $EUID == 0 ]]; then\n"
                       f"  exec python3 /usr/local/lib/t95-setup/server/setup/t95_setup.py {component} \"$@\"\n"
                       "fi\n"
                       f"exec sudo python3 /usr/local/lib/t95-setup/server/setup/t95_setup.py {component} \"$@\"\n")
            if wrapper.is_symlink() or (wrapper.exists() and b"# T95 managed command\n" not in wrapper.read_bytes()):
                raise ValueError(f"Vorhandenes fremdes Werkzeug: {wrapper}")
            atomic_file(wrapper, content.encode(), 0o755)

    def install_dashboard(self):
        archive = SOURCE / "server/ssh-dashboard/2026-10-16"
        entries = json.loads((archive / "manifest.json").read_text())["files"]
        if len({e["path"] for e in entries}) != len(entries):
            raise ValueError("Doppelte Manifestpfade")
        for e in entries:
            p = Path(e["path"])
            if p.is_absolute() or ".." in p.parts or not (
                p.parent == Path("etc/update-motd.d") or str(p) in
                {"etc/default/armbian-motd", "usr/lib/armbian/armbian-allwinner-battery"}):
                raise ValueError("Ungültiger Dashboard-Pfad")
            if e["mode"] not in ("0644", "0755") or (archive / "rootfs" / p).is_symlink():
                raise ValueError("Ungültige Dashboard-Datei")
            if fingerprint(archive / "rootfs" / p)["sha256"] != e["sha256"]:
                raise ValueError("Dashboard-Prüfsumme falsch")
            check_destination(self.path("/" + e["path"]))
        self.remember(self.path(DASHBOARD_USB_HELP_PATH))
        self.install_packages()
        for e in entries:
            self.write(self.path("/" + e["path"]), (archive / "rootfs" / e["path"]).read_bytes(), int(e["mode"], 8))
        self.write(self.path(DASHBOARD_USB_HELP_PATH), DASHBOARD_USB_HELP, 0o755)

    def refresh_dashboard_help(self):
        """Add/update only the hint on existing installs, keeping the first backup."""
        target = self.path(DASHBOARD_USB_HELP_PATH)
        check_destination(target)
        before = fingerprint(target)
        record = next((r for r in self.state["files"] if r["path"] == str(target)), None)
        if record and "installed" in record and before != record["installed"]:
            raise ValueError("Seit Installation geänderte USB-Dashboard-Hilfe; separat sichern/prüfen")
        if (record and before.get("sha256") == hashlib.sha256(DASHBOARD_USB_HELP).hexdigest()
                and before.get("mode") == 0o755):
            print("Dashboard-Tipps mit USB-Hilfe bereits installiert.")
            return
        previous_state = json.loads(json.dumps(self.state))
        previous_content = target.read_bytes() if before["kind"] == "file" else None
        self.state["phase"] = "updating"
        self.save()
        try:
            self.write(target, DASHBOARD_USB_HELP, 0o755)
            self.cache_tools()
            self.state["phase"] = "installed"
            self.save()
        except (Exception, KeyboardInterrupt) as original:
            try:
                if before["kind"] == "file":
                    atomic_file(target, previous_content, before["mode"], (before["uid"], before["gid"]))
                else:
                    target.unlink(missing_ok=True)
                self.state = previous_state
                self.save()
            except Exception as rollback:
                self.state["phase"] = "rollback-failed"
                self.save()
                raise RuntimeError(f"USB-Dashboard-Hilfe fehlgeschlagen: {original}; Rücknahme fehlgeschlagen: {rollback}") from rollback
            raise
        print("Dashboard-Tipps auf USB-Hilfe aktualisiert. Übriges Dashboard und ursprüngliche Sicherung erhalten.")

    def firmware_paths(self):
        base = self.path("/lib/firmware/brcm").resolve(strict=True)
        return base / "BCM43342.hcd", base / "BCM.mbox,t95-axp313.hcd"

    def check_board(self):
        compatible = self.path("/proc/device-tree/compatible").read_bytes().split(b"\0")
        if b"mbox,t95-axp313" not in compatible:
            raise ValueError("Bluetooth-Setup benötigt das T95-AXP313A-Board aus diesem Projekt")
        firmware, alias = self.firmware_paths()
        if fingerprint(firmware).get("sha256") != FW_HASH:
            raise ValueError("Erwartete BCM43342-Firmware aus v1.0.1 fehlt/ist abweichend; keine fremde Firmware laden")
        device = self.path("/sys/class/bluetooth/hci0/device").resolve(strict=True)
        driver = (device / "driver").resolve(strict=True)
        if (device.name != "serial0-0" or "5000400.serial" not in str(device) or
                driver != self.path("/sys/bus/serial/drivers/hci_uart_bcm").resolve()):
            raise ValueError("hci0 ist nicht das erwartete interne BCM43342-UART-Modul")
        if (alias.exists() or alias.is_symlink()) and (not alias.is_symlink() or os.readlink(alias) != "BCM43342.hcd"):
            raise ValueError("Abweichender Firmware-Alias vorhanden; manuell prüfen")
        return driver, alias

    def rebind(self, driver):
        self.run(["systemctl", "stop", "bluetooth.service"])
        (driver / "unbind").write_text("serial0-0\n")
        try:
            (driver / "bind").write_text("serial0-0\n")
        finally:
            # If binding failed, make one cleanup attempt before restoring BlueZ.
            device_driver = self.path("/sys/bus/serial/devices/serial0-0/driver")
            if not device_driver.exists():
                try:
                    (driver / "bind").write_text("serial0-0\n")
                except OSError as error:
                    print(f"Bluetooth-Rebind benötigt Prüfung: {error}", file=sys.stderr)
            self.run(["systemctl", "start", "bluetooth.service"], check=False)
        for _ in range(15):
            if self.run(["bluetoothctl", "--timeout", "2", "list"], check=False).stdout.startswith("Controller "):
                return
            time.sleep(1)
        raise RuntimeError("Bluetooth-Controller nach Firmware-Rebind nicht bereit")

    def bt(self, *args):
        result = self.run(["bluetoothctl", "--timeout", "15", *args])
        if re.search(r"Failed|No default controller|not available", result.stdout):
            raise RuntimeError(result.stdout.strip())
        print(result.stdout.strip())

    def install_bluetooth(self, music=None):
        if not self.user:
            raise ValueError("Für den Player --user NAME angeben")
        driver, alias = self.check_board()
        for relative in USER_AUDIO_CONFIGS:
            check_destination(self.home / relative)
        # Paths are quoted for MPD and written into an INI file. Reject control
        # characters and INI interpolation markers instead of accepting injection.
        music = Path(music) if music else self.home / "Music"
        if not music.is_absolute() or any(c in str(music) + str(self.home) for c in '\n\r"\\%'):
            raise ValueError("Musikpfad muss absolut sein und darf keine Steuer-/Konfigurationszeichen enthalten")
        self.snapshot_services()
        self.backup_audio_configuration()
        self.install_packages()
        if "pipewire" not in self.run(["mpd", "--version"]).stdout.lower():
            raise ValueError("Installiertes MPD unterstützt keine PipeWire-Ausgabe")
        legacy = self.home / ".mpdconf"
        if legacy.exists():
            # MPD gives this legacy file precedence over ~/.config/mpd/mpd.conf.
            # Its original was already journaled before the package operation.
            legacy.unlink()
            next(r for r in self.state["files"] if r["path"] == str(legacy))["installed"] = fingerprint(legacy)
            self.save()
        self.run(["loginctl", "enable-linger", self.user])
        self.run(["systemctl", "start", f"user@{self.uid}.service"])
        for _ in range(15):
            if self.user_run(["systemctl", "--user", "show-environment"], False).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Benutzerdienste nicht bereit")
        self.service("system", ["disable", "--now", "mpd.socket", "mpd.service"])
        self.service("user", ["stop", *PLAYER_UNITS], False)
        if not alias.is_symlink():
            self.write(alias, link="BCM43342.hcd")
            self.rebind(driver)
        share = self.home / ".local/share/t95-bluetooth"
        for directory in (music, share / "mpd", share / "playlists", share / "wireplumber-state"):
            # Only create music directories in the user's home; external mounts
            # must already exist. Never chown an existing shared music folder.
            if not directory.is_relative_to(self.home) and not directory.is_dir():
                raise ValueError("Externer Musikordner muss bereits vorhanden/eingehängt sein")
            if directory.is_relative_to(self.home):
                self.directory(directory, user=True)
        self.state["music"] = str(music)
        self.state["target"] = "t95.bluetooth.unselected"
        self.save()
        self.write(self.home / ".config/wireplumber/wireplumber.conf.d/51-t95-headless-bluetooth.conf", b'''# T95 headless Bluetooth audio
wireplumber.profiles = {
  main = { monitor.bluez.seat-monitoring = disabled }
}
''', user=True)
        self.write(self.home / ".config/systemd/user/wireplumber.service.d/51-t95-state.conf", b'''[Service]
Environment=XDG_STATE_HOME=%h/.local/share/t95-bluetooth/wireplumber-state
''', user=True)
        # target alone permits WirePlumber to fall back to another sink. Limit
        # this client rule to MPD, leaving other applications' routing intact.
        self.write(self.home / ".config/pipewire/client.conf.d/51-t95-mpd-target.conf", b'''stream.rules = [
  {
    matches = [ { application.name = "Music Player Daemon" } ]
    actions = { update-props = {
      node.dont-fallback = true
      node.dont-move = true
    } }
  }
]
''', user=True)
        self.write_mpd()
        self.write(self.home / ".config/mpDris2/mpDris2.conf", f'''[Connection]
host = 127.0.0.1
port = 6600
[Library]
music_dir = {music}
[Bling]
mmkeys = False
notify = False
'''.encode(), user=True)
        self.write(self.home / ".config/systemd/user/mpdris2.service", b'''[Unit]
Description=MPD MPRIS bridge for Bluetooth buttons
Requires=mpd.service
After=mpd.service dbus.service
PartOf=mpd.service
[Service]
Type=simple
ExecStart=/usr/bin/mpDris2
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
''', user=True)
        self.service("user", ["daemon-reload"])
        self.service("system", ["enable", "--now", "bluetooth.service"])
        self.run(["rfkill", "unblock", "bluetooth"])
        self.bt("power", "on")
        self.service("user", ["enable", "--now", *USER_UNITS])
        self.service("user", ["restart", "wireplumber.service", "mpd.service", "mpdris2.service"])
        self.user_run(["mpc", "-h", "127.0.0.1", "-p", "6600", "stop"])
        print("Player eingerichtet, Wiedergabe gestoppt. Jetzt: t95-bluetooth pair")

    def write_mpd(self):
        share = self.home / ".local/share/t95-bluetooth"
        self.write(self.home / ".config/mpd/mpd.conf", f'''# T95 managed MPD configuration
music_directory "{self.state['music']}"
playlist_directory "{share}/playlists"
db_file "{share}/mpd/database"
log_file "{share}/mpd/mpd.log"
state_file "{share}/mpd/state"
bind_to_address "127.0.0.1"
port "6600"
auto_update "yes"
restore_paused "yes"
audio_output {{
    type "pipewire"
    name "T95 Bluetooth"
    target "{self.state['target']}"
    mixer_type "software"
}}
'''.encode(), user=True)

    def audio(self, address):
        if not self.state or self.state["phase"] != "installed":
            raise ValueError("Zuerst Bluetooth-Player installieren")
        if not re.fullmatch(r"(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", address or ""):
            raise ValueError("Aufruf: t95-bluetooth audio AA:BB:CC:DD:EE:FF")
        marker = address.replace(":", "_").upper()
        # The profile suffix is discovered; do not assume it always is .1.
        for _ in range(15):
            nodes = json.loads(self.user_run(["pw-dump"]).stdout)
            matches = [(n["id"], n.get("info", {}).get("props", {}).get("node.name", "")) for n in nodes
                       if n.get("info", {}).get("props", {}).get("media.class") == "Audio/Sink"]
            matches = [(i, name) for i, name in matches if name.upper().startswith("BLUEZ_OUTPUT." + marker + ".")]
            if matches:
                break
            time.sleep(1)
        else:
            raise ValueError("Kein Audio-Ausgang für diese Adresse. Zuerst connect, A2DP und wpctl status prüfen")
        if self.conflicts():
            raise ValueError("Verwaltete Dateien wurden geändert; vor Audio-Auswahl separat sichern/prüfen")
        node_id, name = matches[0]
        self.user_run(["wpctl", "set-default", str(node_id)])
        self.user_run(["wpctl", "set-volume", str(node_id), "0.20"])
        self.user_run(["wpctl", "set-mute", str(node_id), "0"])
        self.state["target"] = name
        self.write_mpd()
        self.service("user", ["restart", "mpd.service", "mpdris2.service"])
        self.user_run(["mpc", "-h", "127.0.0.1", "-p", "6600", "stop"])
        print("Kopfhörer als MPD-Ausgang gewählt, Lautstärke 20 %, Wiedergabe gestoppt.")

    def radio(self, action):
        if action in ("off", "restart"):
            if self.user:
                self.user_run(["mpc", "-h", "127.0.0.1", "-p", "6600", "stop"], False)
            self.run(["rfkill", "block", "bluetooth"])
            self.service("system", ["stop", "bluetooth.service"])
            print("Bluetooth-Funk aus. Kopfhörer können jetzt mit dem PC verbunden werden.")
        if action in ("on", "restart"):
            if action == "restart":
                time.sleep(1)
            self.run(["rfkill", "unblock", "bluetooth"])
            self.service("system", ["start", "bluetooth.service"])
            for _ in range(15):
                if self.run(["bluetoothctl", "--timeout", "2", "list"], check=False).stdout.startswith("Controller "):
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Bluetooth-Controller nicht bereit; t95-bluetooth status prüfen")
            self.bt("power", "on")

    def remove_packages(self):
        packages = [p for p in self.state["new_packages"] if p in PACKAGES[self.component]
                    and self.run(["dpkg-query", "-W", "-f=${Status}", p], check=False).stdout.strip()
                    == "install ok installed"]
        if (self.component == "bluetooth" and "dbus-user-session" in packages
                and (self.home / ".config/systemd/user/udiskie.service").exists()):
            # Samba's user automounter needs the same session bus even when
            # audio originally installed it. APT cannot see this script-level
            # dependency. Do not break the file server on the next login.
            packages.remove("dbus-user-session")
            print("dbus-user-session bleibt für die vorhandene Samba-/USB-Einrichtung erhalten.")
        if not packages:
            return
        simulation = self.run(["apt-get", "-s", "remove", "--no-auto-remove", *packages]).stdout
        removed = {line.split()[1].split(":")[0] for line in simulation.splitlines() if line.startswith("Remv ")}
        if not removed.issubset(set(packages)):
            raise ValueError("APT würde weitere Pakete entfernen. Pakete bleiben erhalten; keine automatische Rücknahme.")
        self.run(["apt-get", "remove", "-y", "--no-auto-remove", *packages], timeout=1800)
        for package in packages:
            if self.run(["dpkg-query", "-W", "-f=${Status}", package], check=False).stdout.strip() == "install ok installed":
                raise RuntimeError(f"Paket wurde nicht entfernt: {package}; Rücknahme unvollständig")

    def stop_audio_for_rollback(self):
        if not self.state["services"]:
            # Preflight may have failed before capturing/changing any service.
            return
        units = [unit for unit in USER_UNITS if self.unit_load_state("user", unit) != "not-found"]
        if units:
            # One systemd transaction stops sockets together with the daemons.
            self.service("user", ["stop", *units])

    def remove(self, force=False, purge=False):
        if not self.state:
            raise ValueError("Kein Installationsprotokoll vorhanden; bestehende Einrichtung wird nicht blind gelöscht")
        was_removed = self.state["phase"] == "removed"
        if not was_removed:
            # A retry of the old-journal service migration must not overwrite
            # configuration changed after its original removal.
            services_only = self.component == "bluetooth" and self.state.get("rollback_services_only", False)
            conflicts = [] if services_only else self.conflicts()
            if conflicts and not force:
                raise ValueError("Seit Installation geänderte Dateien; separat sichern, dann --force verwenden:\n" + "\n".join(conflicts))
            if self.component == "bluetooth":
                # Stop sockets too, so package removal cannot leave running
                # audio processes or immediately reactivate them.
                self.stop_audio_for_rollback()
                self.state["phase"] = "restoring"
                self.save()
            if not services_only:
                self.restore_files()
            if self.component == "bluetooth":
                if purge:
                    self.remove_packages()
                self.restore_services()
                self.restore_radio()
                self.cache_tools()
            self.state["phase"] = "removed"
            if self.component == "bluetooth":
                self.state["rollback_mode"] = "restore-previous"
            self.save()
            print("Entfernt: vorherige Dateien wiederhergestellt. Sicherung bleibt:", self.state_dir)
        else:
            if self.component == "bluetooth":
                # Upgrade old removal journals too: their previous behavior
                # disabled the player rather than restoring its baseline.
                self.state["rollback_services_only"] = True
                self.state["phase"] = "restoring"
                self.save()
                self.stop_audio_for_rollback()
                if purge:
                    self.remove_packages()
                self.restore_services()
                self.restore_radio()
                self.cache_tools()
                self.state["phase"] = "removed"
                self.state["rollback_mode"] = "restore-previous"
                self.save()
                print("Bereits entfernte Einrichtung: vorherige Dienste erneut abgeglichen.")
            else:
                print("Bereits entfernt.")
        if purge and self.component != "bluetooth":
            self.remove_packages()
        elif not purge:
            print("Pakete bleiben installiert. Optional --remove-packages: nur durch dieses Setup hinzugefügte Zielpakete.")

    def install(self, music=None):
        if not self.path("/etc/armbian-release").is_file():
            raise ValueError("Eine bestehende Armbian-Installation ist erforderlich")
        if self.component == "dashboard" and self.state and self.state["phase"] == "installed":
            self.refresh_dashboard_help()
            return
        if self.component == "bluetooth":
            if not self.user:
                raise ValueError("Für den Player --user NAME angeben")
            self.check_board()
        if not self.begin():
            return
        try:
            if self.component == "dashboard":
                self.install_dashboard()
            else:
                self.install_bluetooth(music)
            self.cache_tools()
            self.state["phase"] = "installed"
            self.save()
        except (Exception, KeyboardInterrupt) as original:
            print("Installation fehlgeschlagen; Konfigurationsdateien werden zurückgenommen.", file=sys.stderr)
            try:
                self.restore_files()
                if self.component == "bluetooth":
                    self.restore_services()
                    self.restore_radio()
            except Exception as rollback_error:
                self.state["phase"] = "rollback-failed"
                self.save()
                raise RuntimeError(f"Installation fehlgeschlagen: {original}. "
                                   f"Auch die Rücknahme benötigt Prüfung: {rollback_error}") from rollback_error
            else:
                self.state["phase"] = "failed"
                self.save()
            print("APT-Pakete/Linger können verbleiben; Protokoll:", self.state_dir, file=sys.stderr)
            raise
        print(f"Fertig. Lokaler Einstieg: t95-{self.component} status / remove")

    def status(self):
        print("Setup:", self.state["phase"] if self.state else "nicht durch dieses Werkzeug installiert")
        if self.state:
            print("Protokoll:", self.state_dir)
            print("Abweichende Dateien:", len(self.conflicts()) if self.state["phase"] != "removed" else "–")
            if self.state.get("audio_backup"):
                print("Konfigurationssicherung:", self.state["audio_backup"]["path"])
        if self.component == "bluetooth":
            if self.state and self.state["phase"] == "removed":
                if self.state.get("rollback_mode") == "restore-previous":
                    print("Rücknahme = vorheriger Zustand; zuvor aktive Audiodienste dürfen laufen.")
                else:
                    print("Älteres Rücknahmeprotokoll: remove gleicht die vorherigen Dienste erneut ab.")
            bluetooth = self.service("system", ["is-active", "bluetooth.service"], False).stdout.strip()
            print("Bluetooth-Dienst:", bluetooth)
            # A diagnostic call must not activate BlueZ via D-Bus after removal.
            if bluetooth == "active":
                controller = self.run(["bluetoothctl", "--timeout", "5", "show"], check=False)
                print(controller.stdout.strip())
            else:
                print("Controllerabfrage übersprungen: Bluetooth-Dienst ist nicht aktiv.")
            radio = self.run(["rfkill", "list", "bluetooth"], check=False)
            print("rfkill nicht installiert (Paket kann nach Rücknahme fehlen)." if radio.returncode == 127
                  else radio.stdout.strip())
            if self.user:
                before = {r["unit"]: r["active"] for r in (self.state or {}).get("services", [])
                          if r["scope"] == "user"}
                for unit in USER_UNITS:
                    actual = self.service("user", ["is-active", unit], False).stdout.strip()
                    expected = "aktiv" if before.get(unit) else "inaktiv" if unit in before else "unbekannt"
                    print(f"{unit}: {actual}; vor Installation: {expected}")


@contextmanager
def setup_lock():
    directory = Path("/var/lib/t95-setup")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (directory / "lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=["dashboard", "bluetooth"])
    parser.add_argument("action", choices=["install", "remove", "status", "on", "off", "restart", "pair", "audio"])
    parser.add_argument("address", nargs="?", help="Bluetooth-Adresse für audio")
    parser.add_argument("--user", help="bestehender normaler Benutzer für die Audiowiedergabe")
    parser.add_argument("--music-dir", help="absoluter Musikordner; Standard: HOME/Music")
    parser.add_argument("--force", action="store_true", help="bei remove auch nachträglich geänderte Konfiguration zurücknehmen")
    parser.add_argument("--remove-packages", action="store_true", help="bei remove nur neu hinzugefügte Zielpakete entfernen")
    args = parser.parse_args()
    if args.address and args.action != "audio":
        parser.error("Eine Geräteadresse ist nur bei audio erlaubt")
    if (args.force or args.remove_packages) and args.action != "remove":
        parser.error("--force und --remove-packages sind nur bei remove erlaubt")
    if args.music_dir and (args.component, args.action) != ("bluetooth", "install"):
        parser.error("--music-dir ist nur bei bluetooth install erlaubt")
    if os.geteuid() != 0:
        parser.error("Bitte mit sudo python3 ausführen; --user NAME für den Player")
    if args.component == "dashboard" and args.action not in ("install", "remove", "status"):
        parser.error("Dashboard unterstützt install, remove und status")
    with setup_lock():
        setup = Setup(args.component, args.user)
        if args.action == "install":
            setup.install(args.music_dir)
        elif args.action == "remove":
            setup.remove(args.force, args.remove_packages)
        elif args.action == "status":
            setup.status()
        elif args.action == "audio":
            setup.audio(args.address)
        elif args.action == "pair":
            print("Kopfhörer in Kopplungsmodus, automatische PC/Handy-Verbindung verhindern.\n"
                  "In bluetoothctl: power on; agent on; default-agent; scan on\n"
                  "Dann: pair ADRESSE; trust ADRESSE; connect ADRESSE; scan off; quit\n"
                  "Danach: t95-bluetooth audio ADRESSE")
            setup.radio("on")
            # Keep an interactive BlueZ client/agent alive throughout discovery and pairing.
            subprocess.run(["bluetoothctl"], check=True)
        else:
            setup.radio(args.action)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        raise SystemExit(f"T95-Setup: {error}")

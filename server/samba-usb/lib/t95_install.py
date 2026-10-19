#!/usr/bin/env python3
"""Install/update the optional T95 Samba USB layer, with private rollback copies."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

from t95_usb import System, User, Manager, USBError, atomic_json, plain

SOURCE = Path(__file__).resolve().parents[1]
PACKAGES = ["samba", "samba-common-bin", "udisks2", "udiskie", "dbus-user-session",
            "polkitd", "exfatprogs", "ntfs-3g", "python3", "python3-dbus", "udev", "util-linux"]


def atomic_file(path, content, mode, uid=0, gid=0, link=None):
    temporary = path.with_name(".t95-" + str(time.time_ns()))
    try:
        if link is not None:
            temporary.symlink_to(link)
            os.lchown(temporary, uid, gid)
        else:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                os.fchmod(output.fileno(), mode)
                os.fchown(output.fileno(), uid, gid)
                output.flush()
                os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Installer:
    def __init__(self, user, update=False, data="/srv/T95-DATA/Share", name="T95-SERVER",
                 system=None, source=SOURCE, owner=0):
        self.user, self.update, self.source = user, update, source
        self.system = system or System()
        self.data, self.name = Path(plain(data)), plain(name)
        self.backup = None
        self.files = []
        self.services = []
        self.owner = owner
        self.state_before = []
        self.payload = {}

    def target(self, path):
        return self.system.path(path)

    def destinations(self):
        return [self.target(p) for p in (
            "/usr/local/lib/t95-usb/t95_usb.py", "/usr/local/bin/t95-usb-share", "/usr/local/bin/usb-eject",
            "/etc/polkit-1/rules.d/50-t95-udisks.rules", "/etc/udev/rules.d/99-t95-usb-eject.rules",
            f"/etc/tmpfiles.d/t95-usb-{self.user.uid}.conf", "/etc/samba/smb.conf")
        ] + [self.user.home / p for p in (
            ".config/udiskie/config.json", ".config/udiskie/config.yml",
            ".config/systemd/user/udiskie.service", ".config/systemd/user/default.target.wants/udiskie.service")]

    def preflight(self):
        self.system.check_tools(("apt-get", "systemctl", "runuser", "getent", "loginctl"))
        if not self.target("/etc/armbian-release").is_file():
            raise USBError("Bestehende Armbian-Installation erforderlich")
        if not self.data.is_absolute() or ".." in self.data.parts or self.data.resolve() != self.data:
            raise USBError("DATA_PATH muss ein absoluter, nicht umgeleiteter Pfad sein")
        if any(c in str(self.data) for c in "\n\r%[]") or not re.fullmatch(r"[A-Za-z0-9_-]{1,15}", self.name):
            raise USBError("Ungültiger Datenpfad oder NETBIOS_NAME (1–15 Zeichen)")
        for target in self.destinations():
            if any(p.is_symlink() for p in target.parents):
                raise USBError(f"Umgeleitetes Zielverzeichnis: {target}")
            if target.is_symlink() and target.name != "udiskie.service":
                raise USBError(f"Umgeleitete Zieldatei: {target}")
            if target.exists() and not (target.is_file() or target.is_symlink()):
                raise USBError(f"Keine reguläre Konfigurationsdatei: {target}")
            if not target.is_relative_to(self.user.home):
                self.check_admin_parents(target)
        manifest = self.source / "MANIFEST.sha256"
        entries = {}
        for line in manifest.read_text().splitlines():
            digest, relative = line.split(maxsplit=1)
            relative = relative.removeprefix("./")
            path = self.source / relative
            if (not re.fullmatch(r"[a-f0-9]{64}", digest) or path.resolve() != path
                    or not path.is_relative_to(self.source) or not path.is_file()):
                raise USBError("Ungültiges Paketmanifest")
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != digest:
                raise USBError(f"Prüfsumme stimmt nicht: {relative}")
            self.payload[relative] = content
            entries[relative] = digest
        for required in ("lib/t95_usb.py", "lib/t95_install.py", "scripts/usb-eject", "scripts/t95-usb-share",
                         "config/systemd-user/udiskie.service", "config/udiskie/config.json",
                         "config/polkit/50-t95-udisks.rules", "config/udev/99-t95-usb-eject.rules"):
            if required not in entries:
                raise USBError(f"Paketdatei fehlt im Manifest: {required}")
        if self.update:
            self.validate_samba()
        print("Vorprüfung und Paketprüfsummen bestanden.", flush=True)

    def validate_samba(self):
        import configparser
        output = self.system.run(["testparm", "-s", "-v"]).stdout
        config = configparser.ConfigParser(interpolation=None, strict=False)
        config.read_string(output)
        sections = {section.casefold(): section for section in config.sections()}
        if "global" not in sections or "t95-data" not in sections:
            raise USBError("--update benötigt eine bestehende T95-Samba-Einrichtung mit [T95-DATA]")
        global_ = config[sections["global"]]
        expected = {"usershare path": "/var/lib/samba/usershares", "usershare owner only": "no",
                    "usershare allow guests": "no", "usershare prefix allow list": str(self.user.base)}
        missing = [f"{key} = {value}" for key, value in expected.items() if
                   (global_.get(key, "").casefold() if value == "no" else global_.get(key)) != value]
        if int(global_.get("usershare max shares", "0")) < 1:
            missing.append("usershare max shares = 20")
        valid_users = config[sections["t95-data"]].get("valid users", "").split()
        if self.user.name not in valid_users:
            missing.append(f"[T95-DATA]: valid users muss {self.user.name} enthalten")
        if missing:
            raise USBError("Bestehende Samba-Konfiguration bleibt unverändert. Zuerst prüfen/ergänzen:\n  " + "\n  ".join(missing))

    def save(self, phase, error=None):
        atomic_json(self.backup / "state.json", {"schema": 1, "user": self.user.name, "phase": phase,
                    "update": self.update, "files": self.files, "services": self.services,
                    "state_before": self.state_before,
                    "error": error, "created": datetime.now(timezone.utc).isoformat()})

    def snapshot(self):
        parent = self.target("/var/lib/t95-samba")
        parent.mkdir(mode=0o700, exist_ok=True)
        if parent.is_symlink() or parent.stat().st_uid != self.owner or parent.stat().st_mode & 0o077:
            raise USBError("Unsicheres Sicherungsverzeichnis")
        self.backup = parent / ("installation-" + str(time.time_ns()))
        self.backup.mkdir(mode=0o700)
        targets = self.destinations()
        if self.user.state.exists():
            targets += sorted(p for p in self.user.state.iterdir() if p.suffix in (".map", ".json"))
            self.state_before = [p.name for p in self.user.state.iterdir() if p.suffix in (".map", ".json")]
        for target in targets:
            record = {"path": str(target), "kind": "absent"}
            if target.is_symlink():
                meta = target.lstat()
                record.update(kind="link", target=os.readlink(target), uid=meta.st_uid, gid=meta.st_gid)
            elif target.exists():
                meta = target.stat()
                if not stat.S_ISREG(meta.st_mode):
                    raise USBError("Nicht reguläre Sicherungsquelle")
                saved = self.backup / f"file-{len(self.files)}"
                atomic_file(saved, target.read_bytes(), 0o600)
                record.update(kind="file", backup=str(saved), sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),
                              mode=stat.S_IMODE(meta.st_mode), uid=meta.st_uid, gid=meta.st_gid)
            self.files.append(record)
        for scope, units in (("system", ["smbd.service", "nmbd.service", "udisks2.service", "polkit.service"]),
                             ("user", ["udiskie.service"])):
            for unit in units:
                run = (lambda args: self.system.service(self.user, args, check=False)) if scope == "user" else (
                    lambda args: self.system.run(["systemctl", *args], check=False))
                available = run(["show", unit, "--property=LoadState", "--value"])
                if available.returncode and "Failed to connect" not in available.stderr:
                    raise USBError(f"Vorheriger Dienstzustand nicht prüfbar: {unit}")
                self.services.append({"scope": scope, "unit": unit, "available": not available.returncode,
                                      "active": run(["is-active", unit]).stdout.strip() == "active" if not available.returncode else False,
                                      "enabled": run(["is-enabled", unit]).stdout.strip() if not available.returncode else "not-found"})
        self.save("backed-up")
        print("Private Konfigurationssicherung:", self.backup, flush=True)

    def mkdir(self, path, mode=0o755, user=False):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise USBError(f"Umgeleitetes Verzeichnis: {path}")
        missing = []
        p = path
        while not p.exists():
            missing.append(p)
            p = p.parent
        for p in reversed(missing):
            p.mkdir(mode=mode)
            if user:
                os.chown(p, self.user.uid, self.user.gid)

    def put(self, target, content, mode=0o644, user=False):
        self.mkdir(target.parent, user=user)
        if not user:
            self.check_admin_parents(target)
        atomic_file(target, content, mode, self.user.uid if user else 0, self.user.gid if user else 0)

    def check_admin_parents(self, target):
        boundary = self.system.root
        for parent in (target.parent, *target.parent.parents):
            if parent == boundary or not parent.is_relative_to(boundary):
                break
            if parent.exists():
                info = parent.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid != self.owner or info.st_mode & 0o022:
                    raise USBError(f"Unsicheres Administrationsverzeichnis: {parent}")

    def install_files(self):
        for relative, target, mode in (
            ("lib/t95_usb.py", "/usr/local/lib/t95-usb/t95_usb.py", 0o755),
            ("scripts/t95-usb-share", "/usr/local/bin/t95-usb-share", 0o755),
            ("scripts/usb-eject", "/usr/local/bin/usb-eject", 0o755),
            ("config/udev/99-t95-usb-eject.rules", "/etc/udev/rules.d/99-t95-usb-eject.rules", 0o644)):
            self.put(self.target(target), self.payload[relative], mode)
        polkit = self.payload["config/polkit/50-t95-udisks.rules"].decode().replace("__T95_USER__", self.user.name)
        self.put(self.target("/etc/polkit-1/rules.d/50-t95-udisks.rules"), polkit.encode())
        for relative, target in (("config/udiskie/config.json", ".config/udiskie/config.json"),
                                 ("config/systemd-user/udiskie.service", ".config/systemd/user/udiskie.service")):
            self.put(self.user.home / target, self.payload[relative], user=True)
        runtime = self.target("/run/t95-usb")
        tmpfiles = "\n".join(f"d /run/t95-usb{suffix} {mode} root root -" for suffix, mode in (
            ("", "0755"), ("/locks", "0755"), ("/guards", "0755"), ("/operations", "0700")))
        tmpfiles += f"\nf /run/t95-usb/locks/shares-{self.user.uid}.lock 0660 root {self.user.gid} -\n"
        tmpfile_path = self.target(f"/etc/tmpfiles.d/t95-usb-{self.user.uid}.conf")
        self.put(tmpfile_path, tmpfiles.encode())
        self.system.run(["systemd-tmpfiles", "--create", str(tmpfile_path)])
        for suffix in ("", "locks", "guards", "operations"):
            p = runtime / suffix
            if p.is_symlink() or not p.is_dir() or p.stat().st_uid != self.owner:
                raise USBError("Laufzeitverzeichnisse wurden nicht sicher angelegt")
        self.system.run(["udevadm", "verify", str(self.target("/etc/udev/rules.d/99-t95-usb-eject.rules"))])
        self.system.run(["udevadm", "control", "--reload-rules"])

    def samba_config(self):
        return f'''[global]
    workgroup = WORKGROUP
    server role = standalone server
    security = user
    map to guest = Bad User
    netbios name = {self.name}
    server min protocol = SMB2
    log file = /var/log/samba/log.%m
    max log size = 1000
    usershare path = /var/lib/samba/usershares
    usershare max shares = 20
    usershare owner only = no
    usershare allow guests = no
    usershare prefix allow list = {self.user.base}
[T95-DATA]
    path = {self.data}
    browseable = yes
    read only = no
    guest ok = no
    valid users = {self.user.name}
    create mask = 0660
    directory mask = 0770
'''.encode()

    def check_manager_groups(self):
        group = self.system.run(["getent", "group", "sambashare"]).stdout.split(":")
        gid = int(group[2])
        pid = self.system.run(["systemctl", "show", f"user@{self.user.uid}.service", "--property=MainPID", "--value"]).stdout.strip()
        if not pid.isdigit() or int(pid) == 0:
            raise USBError("Benutzermanager läuft nicht")
        status = self.target(f"/proc/{pid}/status").read_text()
        groups = re.search(r"^Groups:\s*(.*)$", status, re.M)
        if not groups or gid not in {int(g) for g in groups[1].split()}:
            raise USBError("Benutzermanager kennt sambashare noch nicht. Box kontrolliert neu starten, danach Einrichtung erneut aufrufen. Ein neuer SSH-Login allein genügt bei Linger nicht.")

    def restore(self):
        self.save("restoring")
        # Stop only the project automounter before replacing its code/config.
        self.system.service(self.user, ["stop", "udiskie.service"], check=False)
        for record in self.files:
            if record["kind"] == "file" and hashlib.sha256(Path(record["backup"]).read_bytes()).hexdigest() != record["sha256"]:
                raise USBError("Sicherung beschädigt; automatische Rücknahme abgebrochen")
        if self.user.state.exists():
            # Remove only the module's new mapping records before restoring its
            # old format; otherwise old Bash hooks could miss migrated shares.
            from t95_usb import UserState
            store = UserState(self.user)
            for record in store.read():
                if record["_file"] not in self.state_before:
                    store.delete(record)
        for record in reversed(self.files):
            target = Path(record["path"])
            self.mkdir(target.parent, user=target.is_relative_to(self.user.home))
            if record["kind"] == "file":
                atomic_file(target, Path(record["backup"]).read_bytes(), record["mode"], record["uid"], record["gid"])
            elif record["kind"] == "link":
                atomic_file(target, b"", 0o644, record["uid"], record["gid"], link=record["target"])
            else:
                target.unlink(missing_ok=True)
        self.system.run(["udevadm", "control", "--reload-rules"])
        self.system.run(["systemctl", "daemon-reload"])
        user_ready = self.system.service(self.user, ["show-environment"], check=False).returncode == 0
        if user_ready:
            self.system.service(self.user, ["daemon-reload"])
        for record in self.services:
            if record["scope"] == "user" and not user_ready:
                if record["available"]:
                    raise USBError("Vorheriger Benutzermanager ist nicht erreichbar")
                continue
            run = (lambda args: self.system.service(self.user, args)) if record["scope"] == "user" else (
                lambda args: self.system.run(["systemctl", *args]))
            loaded = (self.system.service(self.user, ["show", record["unit"], "--property=LoadState", "--value"], check=False)
                      if record["scope"] == "user" else self.system.run(["systemctl", "show", record["unit"], "--property=LoadState", "--value"], check=False))
            if loaded.stdout.strip() == "not-found":
                if record["active"]:
                    raise USBError("Früher aktiver Dienst fehlt nach Rücknahme")
                continue
            run(["disable", record["unit"]])
            if record["enabled"] in ("enabled", "enabled-runtime"):
                run(["enable", *( ["--runtime"] if record["enabled"] == "enabled-runtime" else []), record["unit"]])
            elif record["enabled"] in ("masked", "masked-runtime"):
                run(["mask", *( ["--runtime"] if record["enabled"] == "masked-runtime" else []), record["unit"]])
            run(["restart" if record["active"] else "stop", record["unit"]])
        for record in self.services:
            if record["scope"] == "user" and not user_ready:
                continue
            run = (lambda args: self.system.service(self.user, args, check=False)) if record["scope"] == "user" else (
                lambda args: self.system.run(["systemctl", *args], check=False))
            if (run(["is-active", record["unit"]]).stdout.strip() == "active") != record["active"]:
                raise USBError(f"Dienstzustand nicht wiederhergestellt: {record['unit']}")
            expected = record["enabled"]
            allowed = {"not-found", "disabled", "static", "indirect"} if expected == "not-found" else {expected}
            if run(["is-enabled", record["unit"]]).stdout.strip() not in allowed:
                raise USBError(f"Dienst-Autostart nicht wiederhergestellt: {record['unit']}")
        self.save("rolled-back")

    def install(self):
        self.preflight()
        self.snapshot()  # Nothing is changed by APT or the project before this.
        try:
            self.save("installing")
            print("Installiere benötigte Pakete …", flush=True)
            self.system.run(["apt-get", "update"], timeout=1800)
            self.system.run(["apt-get", "install", "-y", *PACKAGES], timeout=1800)
            group = self.system.run(["getent", "group", "sambashare"], check=False)
            if group.returncode:
                self.system.run(["groupadd", "sambashare"])
            self.system.run(["usermod", "-aG", "sambashare", self.user.name])
            self.system.run(["loginctl", "enable-linger", self.user.name])
            self.system.run(["systemctl", "start", f"user@{self.user.uid}.service"])
            self.check_manager_groups()
            for path, mode in ((self.user.base, 0o755), (self.user.state, 0o700)):
                self.mkdir(path, mode, user=True)
            self.system.run(["install", "-d", "-o", "root", "-g", "sambashare", "-m", "1770", "/var/lib/samba/usershares"])
            self.install_files()
            if not self.update:
                self.mkdir(self.target(str(self.data)), 0o2770, user=True)
                self.put(self.target("/etc/samba/smb.conf"), self.samba_config())
            self.validate_samba()
            if not self.update:
                listed = self.system.run(["pdbedit", "-L"]).stdout.splitlines()
                if not any(line.split(":", 1)[0] == self.user.name for line in listed):
                    print("Samba-Passwort für", self.user.name, "festlegen:", flush=True)
                    self.system.interactive(["smbpasswd", "-a", self.user.name])
            self.system.run(["systemctl", "enable", "--now", "smbd.service", "nmbd.service"])
            self.system.run(["systemctl", "start", "udisks2.service"])
            self.system.run(["systemctl", "try-restart", "polkit.service"])
            self.system.service(self.user, ["daemon-reload"])
            self.system.service(self.user, ["enable", "udiskie.service"])
            self.system.service(self.user, ["restart", "udiskie.service"])
            if self.system.service(self.user, ["is-active", "udiskie.service"]).stdout.strip() != "active":
                raise USBError("USB-Automounter ist nicht aktiv")
            self.system.as_user(self.user, ["/usr/local/bin/t95-usb-share", "reconcile"])
            if not self.update:
                self.system.run(["systemctl", "restart", "smbd.service"])
            self.save("installed")
        except (Exception, KeyboardInterrupt) as error:
            try:
                self.restore()
            except Exception as rollback:
                self.save("rollback-failed", f"{error}; Rücknahme: {rollback}")
                raise USBError(f"Einrichtung fehlgeschlagen: {error}. Rücknahme unvollständig: {rollback}. Sicherung: {self.backup}") from rollback
            raise USBError(f"Einrichtung fehlgeschlagen: {error}. Vorherige Projektdateien/Dienste wiederhergestellt. Pakete/Gruppen/Linger können verbleiben. Sicherung: {self.backup}") from error
        print("Fertig. Bestehende Samba-Konfiguration erhalten." if self.update else "Fertig.", flush=True)
        print('Status: sudo usb-eject --status\nAuswerfen: sudo usb-eject "Freigabename"', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="Projektkomponenten aktualisieren; Samba-Konfiguration/Passwörter erhalten")
    args = parser.parse_args()
    try:
        if os.geteuid() != 0:
            raise USBError("Bitte als root bzw. mit sudo ausführen")
        user = User.lookup(os.environ.get("T95_USER", ""))
        Installer(user, args.update, os.environ.get("DATA_PATH", "/srv/T95-DATA/Share"),
                  os.environ.get("NETBIOS_NAME", "T95-SERVER")).install()
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print("FEHLER:", str(error) or "Unterbrochen", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

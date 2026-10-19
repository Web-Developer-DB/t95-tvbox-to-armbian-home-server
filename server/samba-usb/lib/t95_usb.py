#!/usr/bin/env python3
"""T95 USB shares and per-attachment eject. System effects are injectable."""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import configparser
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

SUPPORTED = {"ext4", "exfat", "vfat", "ntfs", "ntfs3", "fuseblk", "btrfs"}
RUNTIME = Path("/run/t95-usb")


class USBError(RuntimeError):
    pass


class CommandError(USBError):
    pass


def command(args, check=True, timeout=30):
    try:
        result = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CommandError(f"{args[0]}: {error}") from error
    if check and result.returncode:
        raise CommandError(f"{args[0]}: {result.stderr.strip() or result.stdout.strip()}")
    return result


def plain(value):
    """Reject record/command control characters, without interpreting shell text."""
    value = str(value)
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise USBError("Steuerzeichen in Geräte-/Freigabedaten; Vorgang abgebrochen")
    return value


def below(path, base):
    return path != base and path.is_relative_to(base)


def safe_directory(path, owner=0, group=0, mode=0o755, create=False):
    """Only root-owned parents may be used for privileged runtime records."""
    if create:
        path.mkdir(mode=mode, parents=False, exist_ok=True)
    meta = path.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != owner or meta.st_mode & 0o022:
        raise USBError(f"Unsicheres Laufzeitverzeichnis: {path}")
    return path


def atomic_json(path, value, mode=0o600):
    fd, name = tempfile.mkstemp(prefix=".t95-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            os.fchmod(output.fileno(), mode)
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


@dataclass(frozen=True)
class User:
    name: str
    uid: int
    gid: int
    home: Path
    base: Path
    state: Path

    @classmethod
    def lookup(cls, name):
        if not re.fullmatch(r"[a-z_][a-z0-9_-]*\$?", name or ""):
            raise USBError("Gültigen normalen Benutzer über T95_USER/SUDO_USER angeben")
        account = pwd.getpwnam(name)
        if not account.pw_uid:
            raise USBError("root ist kein Samba-/USB-Benutzer")
        home = Path(account.pw_dir)
        base = Path(os.environ.get("T95_MOUNT_BASE", f"/media/{name}"))
        state = Path(os.environ.get("T95_STATE_DIR", str(home / ".local/state/t95-usb-shares")))
        if not base.is_absolute() or not state.is_absolute() or ".." in base.parts + state.parts:
            raise USBError("Mount- und Statuspfad müssen absolute, eindeutige Pfade sein")
        if base.resolve() != base or state.resolve() != state or not state.is_relative_to(home):
            raise USBError("Umgeleiteter Mount-/Statuspfad oder Statuspfad außerhalb des Benutzerordners")
        return cls(name, account.pw_uid, account.pw_gid, home, base, state)


@dataclass(frozen=True)
class Disk:
    device: str
    syspath: str
    seq: str
    boot: str
    drive: str
    nodes: tuple
    numbers: tuple

    def identity(self):
        return {"device": self.device, "syspath": self.syspath,
                "diskseq": self.seq, "boot": self.boot}


class System:
    """The only boundary that runs commands, reads sysfs, or calls UDisks."""
    def __init__(self, runner=command, root=Path("/")):
        self.run = runner
        self.root = root
        self._bus = None

    def path(self, path):
        return self.root / str(path).lstrip("/")

    def as_user(self, user, args, **kwargs):
        if os.geteuid() == user.uid:
            return self.run(args, **kwargs)
        return self.run(["runuser", "-u", user.name, "--", "env", f"HOME={user.home}",
                         f"XDG_RUNTIME_DIR=/run/user/{user.uid}",
                         f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user.uid}/bus", *args], **kwargs)

    def service(self, user, args, **kwargs):
        return self.as_user(user, ["systemctl", "--user", *args], **kwargs)

    def interactive(self, args):
        result = subprocess.run(args, check=False)
        if result.returncode:
            raise CommandError(f"{args[0]} fehlgeschlagen")

    def check_tools(self, names):
        missing = [name for name in names if shutil.which(name) is None]
        if missing:
            raise USBError("Benötigte Grundwerkzeuge fehlen: " + ", ".join(missing))

    def objects(self):
        import dbus
        if self._bus is None:
            self._bus = dbus.SystemBus()
        proxy = self._bus.get_object("org.freedesktop.UDisks2", "/org/freedesktop/UDisks2")
        return dbus.Interface(proxy, "org.freedesktop.DBus.ObjectManager").GetManagedObjects(timeout=15)

    def power_off(self, drive):
        import dbus
        proxy = self._bus.get_object("org.freedesktop.UDisks2", drive)
        try:
            dbus.Interface(proxy, "org.freedesktop.UDisks2.Drive").PowerOff({}, timeout=30)
        except dbus.DBusException as error:
            if error.get_dbus_name() == "org.freedesktop.UDisks2.Error.NotSupported":
                return False
            raise USBError(f"USB-Abschalten fehlgeschlagen: {error}") from error
        return True

    def inventory(self):
        result = self.run(["lsblk", "--json", "--paths", "--output",
                           "NAME,TYPE,PKNAME,MAJ:MIN,TRAN,FSTYPE,UUID,LABEL"])
        data = json.loads(result.stdout)
        nodes = {}
        def visit(items):
            for item in items:
                name = plain(item["name"])
                if name in nodes and nodes[name] != item:
                    raise USBError("Mehrdeutige Geräteauflistung")
                nodes[name] = item
                visit(item.get("children", []))
        visit(data["blockdevices"])
        if not nodes:
            raise USBError("Geräteauflistung ist leer; keine sichere Zuordnung möglich")
        return nodes

    def mounts(self):
        result = self.run(["findmnt", "--json", "--list", "--evaluate", "--nofsroot", "--output",
                           "TARGET,SOURCE,MAJ:MIN,FSTYPE,FSROOT"])
        data = json.loads(result.stdout)
        return data["filesystems"]

    def snapshot(self):
        return Snapshot(self, self.inventory(), self.mounts(), self.objects())

    def activate_guard(self, disk):
        # Only the target disk and its partitions receive change events.
        for node in disk.nodes:
            self.run(["udevadm", "trigger", "--action=change", str(self.path("/sys/class/block") / Path(node).name)])
        self.run(["udevadm", "settle", "--timeout=10"])

    def wait_guard(self, disk, timeout=30):
        deadline = time.monotonic() + timeout
        quiet = None
        while time.monotonic() < deadline:
            current = self.snapshot()
            current.verify(disk)
            blocks = [p for p in current.blocks.values() if str(p.get("Drive")) == disk.drive]
            expected = {os.makedev(*map(int, n.split(":"))) for n in disk.numbers}
            present = {int(p.get("DeviceNumber", -1)) for p in blocks}
            guarded = expected.issubset(present) and all(bool(p.get("HintIgnore")) and not bool(p.get("HintAuto")) for p in blocks)
            jobs = any(set(map(str, props.get("Objects", []))) & (set(current.block_paths(disk)) | {disk.drive})
                       for interfaces in current.objects.values()
                       for name, props in interfaces.items() if name == "org.freedesktop.UDisks2.Job")
            if guarded and blocks and not jobs:
                quiet = quiet or time.monotonic()
                if time.monotonic() - quiet >= 0.5:
                    return current
            else:
                quiet = None
            time.sleep(0.1)
        raise USBError("Auswurfsperre oder Ende laufender Geräteaufträge nicht bestätigt; nicht abziehen")

    def sync(self, mount):
        self.run(["sync", "--file-system", mount], timeout=60)

    def unmount(self, mount):
        self.run(["umount", "--", mount], timeout=60)

    def close_share(self, name):
        self.run(["smbcontrol", "smbd", "close-share", name])

    def permissions(self, user, path):
        return tuple(self.as_user(user, ["test", flag, path], check=False).returncode == 0
                     for flag in ("-r", "-w", "-x"))

    def log(self, message):
        print(message, flush=True)
        try:
            self.run(["logger", "-t", "T95-USB-SHARE", "--", message], check=False)
        except CommandError as error:
            print(f"Hinweis: Journalmeldung nicht gesendet: {error}", file=sys.stderr)


class Snapshot:
    def __init__(self, system, nodes, mounts, objects):
        self.system, self.nodes, self.mounts, self.objects = system, nodes, mounts, objects
        self.blocks = {str(path): props["org.freedesktop.UDisks2.Block"]
                       for path, props in objects.items() if "org.freedesktop.UDisks2.Block" in props}
        self.drives = {str(path): props["org.freedesktop.UDisks2.Drive"]
                       for path, props in objects.items() if "org.freedesktop.UDisks2.Drive" in props}

    def disk(self, device):
        device = str(device)
        if device not in self.nodes:
            raise USBError(f"Gerät nicht vorhanden: {device}")
        node = self.nodes[device]
        while node["type"] == "part":
            parent = node.get("pkname")
            if parent and not parent.startswith("/"):
                parent = "/dev/" + parent
            if parent not in self.nodes:
                raise USBError("Übergeordnetes Laufwerk nicht eindeutig ermittelt")
            node = self.nodes[parent]
        if node["type"] != "disk":
            raise USBError("Mapper-, LVM-, RAID- und Loop-Geräte werden nicht ausgeworfen")
        name = node["name"]
        descendants = []
        def collect(item):
            if item["type"] not in ("disk", "part"):
                raise USBError("Komplexe Laufwerkstopologie wird nicht unterstützt")
            if item.get("fstype") in ("crypto_LUKS", "LVM2_member", "linux_raid_member", "swap"):
                raise USBError("Verschlüsselte, RAID-/LVM- oder Swap-Partition auf dem Laufwerk")
            descendants.append(item)
            for child in item.get("children", []):
                collect(child)
        collect(node)
        numbers = tuple(str(p["maj:min"]) for p in descendants)
        block_matches = [p for p in self.blocks.values() if int(p.get("DeviceNumber", -1)) ==
                         os.makedev(*map(int, str(node["maj:min"]).split(":")))]
        if len(block_matches) != 1:
            raise USBError("UDisks-Geräteidentität nicht eindeutig")
        drive = str(block_matches[0].get("Drive", "/"))
        if drive not in self.drives or str(self.drives[drive].get("ConnectionBus")) != "usb":
            raise USBError("Das ausgewählte Laufwerk ist kein bestätigtes USB-Gerät")
        if node.get("tran") not in ("usb", None):
            raise USBError("Widersprüchliche USB-Gerätezuordnung")
        syslink = self.system.path("/sys/class/block") / Path(name).name
        syspath = syslink.resolve(strict=True)
        seq = (syslink / "diskseq").read_text().strip()
        if not re.fullmatch(r"[0-9]+", seq):
            raise USBError("Kernel-diskseq fehlt oder ist ungültig")
        boot = self.system.path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return Disk(name, str(syspath), seq, boot, drive,
                    tuple(p["name"] for p in descendants), numbers)

    def verify(self, disk):
        current = self.disk(disk.device)
        if current.identity() != disk.identity() or current.nodes != disk.nodes:
            raise USBError("Gerät wurde getrennt oder verändert; Vorgang abgebrochen")
        return current

    def block_paths(self, disk):
        numbers = {os.makedev(*map(int, n.split(":"))) for n in disk.numbers}
        return [path for path, p in self.blocks.items() if int(p.get("DeviceNumber", -1)) in numbers]

    def at(self, path):
        found = [m for m in self.mounts if m["target"] == str(path)]
        if len(found) > 1:
            raise USBError(f"Mehrfach belegter Mountpunkt: {path}")
        return found[0] if found else None

    def device_at(self, mount):
        # Btrfs and FUSE NTFS mounts use an anonymous mount device number.
        # Their SOURCE still names the real block device; --nofsroot separates
        # Btrfs subvolume suffixes. Accept old/simulated suffixes explicitly.
        source = plain(mount.get("source", "")).split("[", 1)[0]
        source_matches = []
        if source.startswith("/dev/"):
            canonical = self.system.path(source).resolve()
            source_matches = [n["name"] for n in self.nodes.values()
                              if self.system.path(n["name"]).resolve() == canonical]
        if mount["fstype"] in ("btrfs", "fuseblk"):
            if len(source_matches) != 1:
                raise USBError("Blockquelle des Btrfs-/FUSE-Mounts nicht eindeutig")
            return source_matches[0]
        matches = [n["name"] for n in self.nodes.values() if str(n["maj:min"]) == str(mount["maj:min"])]
        if len(matches) != 1:
            raise USBError("Blockgerät des Mountpunkts nicht eindeutig")
        if source_matches and source_matches != matches:
            raise USBError("Widersprüchliche Blockgerätequelle des Mountpunkts")
        return matches[0]

    def belongs(self, mount, disk):
        if str(mount["maj:min"]) in disk.numbers:
            return True
        if mount["fstype"] in ("btrfs", "fuseblk"):
            return self.device_at(mount) in disk.nodes
        return False

    def disk_mounts(self, disk, user):
        mounts = [m for m in self.mounts if self.belongs(m, disk)]
        # A Btrfs filesystem may be reported with another member as SOURCE.
        # Check every Btrfs member on the target before touching any partition.
        for node in disk.nodes:
            entry = self.nodes[node]
            if entry.get("fstype") != "btrfs":
                continue
            uuid = plain(entry.get("uuid") or "")
            if not uuid or "/" in uuid or ".." in uuid:
                raise USBError("Ungültige Btrfs-Dateisystemkennung")
            devices = self.system.path(f"/sys/fs/btrfs/{uuid}/devices")
            if devices.exists() and any(p.resolve().name not in {Path(n).name for n in disk.nodes} for p in devices.iterdir()):
                raise USBError("Btrfs über mehrere physische Laufwerke wird nicht ausgeworfen")
        swaps = self.system.path("/proc/swaps").read_text().splitlines()
        for line in swaps[1:]:
            if not line.strip():
                continue
            source = re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), line.split()[0])
            if source in disk.nodes or any(Path(source).is_relative_to(Path(m["target"])) for m in mounts):
                raise USBError("Aktiver Swap-Bereich oder Swap-Datei auf dem Laufwerk")
        for mount in mounts:
            path = Path(plain(mount["target"]))
            if not below(path, user.base) or path.resolve() != path:
                raise USBError(f"Fremder/System-Mount auf dem USB-Laufwerk: {path}")
            if mount["fstype"] not in SUPPORTED:
                raise USBError(f"Nicht unterstütztes Dateisystem: {mount['fstype']}")
            if mount["fstype"] == "btrfs":
                uuid = self.nodes[self.device_at(mount)].get("uuid")
                if not uuid or "/" in uuid or ".." in uuid:
                    raise USBError("Ungültige Btrfs-Dateisystemkennung")
                devices = self.system.path(f"/sys/fs/btrfs/{uuid}/devices")
                members = list(devices.iterdir())
                if not members or any(p.resolve().name not in {Path(n).name for n in disk.nodes} for p in members):
                    raise USBError("Btrfs-Gerätezuordnung ist nicht als einzelnes Laufwerk bestätigt")
        # A bind/nested foreign filesystem must not be silently detached with it.
        targets = [Path(m["target"]) for m in mounts]
        if any(any(below(Path(m["target"]), p) for p in targets) and m not in mounts for m in self.mounts):
            raise USBError("Fremder Mount unterhalb eines USB-Mountpunkts")
        return sorted(mounts, key=lambda m: len(Path(m["target"]).parts), reverse=True)


class Runtime:
    def __init__(self, user, path=RUNTIME, owner=0):
        self.user, self.path, self.owner = user, path, owner

    def check(self):
        for path in (self.path, self.path / "locks", self.path / "guards", self.path / "operations"):
            safe_directory(path, self.owner)

    @contextmanager
    def lock(self, name, create=False, wait=10):
        self.check()
        path = self.path / "locks" / name
        flags = os.O_RDWR | os.O_NOFOLLOW | (os.O_CREAT if create else 0)
        fd = os.open(path, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner or info.st_nlink != 1:
                raise USBError("Unsichere Sperrdatei")
            deadline = time.monotonic() + wait
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise USBError("Laufwerks-/Freigabevorgang läuft bereits; erneut versuchen")
                    time.sleep(0.05)
            yield
        finally:
            os.close(fd)

    def share_lock(self):
        return self.lock(f"shares-{self.user.uid}.lock")

    def guarded(self, disk):
        self.check()
        path = self.path / "guards" / disk.seq
        try:
            info = path.lstat()
        except FileNotFoundError:
            return False
        if not stat.S_ISREG(info.st_mode) or info.st_uid != self.owner:
            raise USBError("Unsichere Auswurfsperre")
        return True

    def guard(self, disk, names):
        self.check()
        # Names are readable by the user hook, but only root can replace guards.
        atomic_json(self.path / "guards" / disk.seq, {**disk.identity(), "shares": sorted(names)}, 0o644)

    def reservations(self, snapshot):
        names = set()
        self.check()
        for path in (self.path / "guards").iterdir():
            if not re.fullmatch(r"[0-9]+", path.name):
                continue
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(fd) as input_file:
                meta = os.fstat(input_file.fileno())
                if meta.st_uid != self.owner or not stat.S_ISREG(meta.st_mode) or meta.st_size > 65536:
                    raise USBError("Unsichere Freigabenreservierung")
                record = json.loads(input_file.read(65537))
            if record.get("device") not in snapshot.nodes:
                continue
            disk = snapshot.disk(record["device"])
            if disk.identity() == {k: record.get(k) for k in disk.identity()}:
                names.update(plain(n).casefold() for n in record.get("shares", []))
        return names

    def operation(self, disk, phase, names, error=None, paths=None):
        value = {"schema": 1, **disk.identity(), "phase": phase,
                 "user": self.user.name, "shares": sorted(names), "paths": paths or {}, "error": error}
        atomic_json(self.path / "operations" / f"{disk.seq}.json", value)

    def operations(self):
        self.check()
        result = []
        for path in sorted((self.path / "operations").glob("*.json")):
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd) as input_file:
                meta = os.fstat(input_file.fileno())
                if meta.st_uid != self.owner or not stat.S_ISREG(meta.st_mode):
                    raise USBError("Unsicheres Auswurfprotokoll")
                value = json.load(input_file)
                if value.get("user") == self.user.name:
                    result.append(value)
        return result


class UserState:
    """Open directory components without following links; never execute records."""
    def __init__(self, user):
        self.user = user

    @contextmanager
    def directory(self):
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in self.user.state.parts[1:]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            yield fd
        finally:
            os.close(fd)

    def read(self):
        result = []
        with self.directory() as directory:
            for name in sorted(os.listdir(directory)):
                if not name.endswith((".json", ".map")):
                    continue
                fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(fd) as input_file:
                    meta = os.fstat(input_file.fileno())
                    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != self.user.uid or meta.st_size > 65536:
                        raise USBError("Ungültige USB-Zuordnungsdatei")
                    content = input_file.read(65537)
                    if len(content) > 65536:
                        raise USBError("USB-Zuordnungsdatei ist zu groß")
                    if name.endswith(".map"):
                        fields = content.rstrip("\n").split("\t")
                        if len(fields) != 4:
                            raise USBError("Alte USB-Zuordnung ist beschädigt; zuerst prüfen")
                        value = dict(zip(("share", "path", "device", "uuid"), fields))
                        value["schema"] = 0
                    else:
                        value = json.loads(content)
                        if value.get("schema") != 1:
                            raise USBError("Unbekannte USB-Statusversion")
                    for field in ("share", "path", "device", "uuid"):
                        if not isinstance(value.get(field), str):
                            raise USBError("Unvollständige USB-Zuordnung")
                        plain(value[field])
                    value["_file"] = name
                    result.append(value)
        return result

    def write(self, record):
        name = hashlib.sha256(record["path"].encode()).hexdigest()[:24] + ".json"
        payload = {k: v for k, v in record.items() if not k.startswith("_")}
        with self.directory() as directory:
            try:
                current = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
            except FileNotFoundError:
                pass
            else:
                with os.fdopen(current) as input_file:
                    metadata = os.fstat(input_file.fileno())
                    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != self.user.uid or metadata.st_size > 65536:
                        raise USBError("Ungültige vorhandene USB-Zuordnungsdatei")
                    unchanged = json.loads(input_file.read(65537)) == payload
                if unchanged:
                    if record.get("_file") and record["_file"] != name:
                        os.unlink(record["_file"], dir_fd=directory)
                        os.fsync(directory)
                        return True
                    return False
            temporary = ".t95-" + str(os.getpid()) + "-" + str(time.time_ns())
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                with os.fdopen(fd, "w") as output:
                    if os.geteuid() == 0:
                        os.fchown(output.fileno(), self.user.uid, self.user.gid)
                    json.dump(payload, output, ensure_ascii=False)
                    output.write("\n")
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
                os.fsync(directory)
            finally:
                try:
                    os.unlink(temporary, dir_fd=directory)
                except FileNotFoundError:
                    pass
        if record.get("_file") and record["_file"] != name:
            self.delete(record)
        return True

    def delete(self, record):
        name = record.get("_file") or hashlib.sha256(record["path"].encode()).hexdigest()[:24] + ".json"
        if "/" in name or not name.endswith((".map", ".json")):
            raise USBError("Ungültiger Statusdateiname")
        with self.directory() as directory:
            try:
                os.unlink(name, dir_fd=directory)
                os.fsync(directory)
            except FileNotFoundError:
                pass


class Net:
    def __init__(self, system, user):
        self.system, self.user = system, user
        self.owner = 0

    @contextmanager
    def directory(self):
        configured = self.system.run(["testparm", "-s", "--parameter-name=usershare path"]).stdout.strip()
        if configured != "/var/lib/samba/usershares":
            raise USBError("Unerwarteter Samba-usershare-Pfad; Projektkonfiguration prüfen")
        # Open every component without following links, including while running as root.
        fd = os.open(self.system.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in Path(configured).parts[1:]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = next_fd
                metadata = os.fstat(fd)
                if metadata.st_uid != self.owner:
                    raise USBError("Samba-usershare-Verzeichnis gehört nicht root")
                if part != "usershares" and metadata.st_mode & 0o022:
                    raise USBError("Unsicheres übergeordnetes Samba-Verzeichnis")
            metadata = os.fstat(fd)
            if metadata.st_mode & 0o002 or (metadata.st_mode & 0o020 and not metadata.st_mode & stat.S_ISVTX):
                raise USBError("Samba-usershare-Verzeichnis benötigt geschützte Schreibrechte/Sticky-Bit")
            yield fd
        finally:
            os.close(fd)

    @staticmethod
    def definition(filename, content):
        """Read name/path metadata, without requiring a still-mounted target.

        Samba's net usershare info/list both opendir(path); this is invalid as
        an inventory after UDisks removes an unmounted mountpoint. Activation
        is still validated by Samba itself in add(). Device ownership is never
        inferred from this metadata: Manager validates mounts/attachment IDs.
        """
        lines = content.splitlines()
        if not lines or lines[0] not in ("#VERSION 1", "#VERSION 2"):
            raise USBError("Unbekannte Samba-usershare-Dateiversion")
        keys = ["path", "comment", "usershare_acl"]
        if lines[0] == "#VERSION 2":
            keys.append("guest_ok")
            if len(lines) == 6:
                keys.append("sharename")
        if len(lines) != len(keys) + 1:
            raise USBError("Unvollständige Samba-usershare-Definition")
        fields = {}
        for key, line in zip(keys, lines[1:]):
            if not line.startswith(key + "="):
                raise USBError("Ungültige Samba-usershare-Feldfolge")
            fields[key] = plain(line[len(key) + 1:])
        name, path = fields.get("sharename", filename), fields["path"].strip(" ")
        if (not name or name.casefold() != filename.casefold() or name in (".", "..")
                or any(c in name for c in '/\\:*?"<>|[]')):
            raise USBError("Ungültiger oder widersprüchlicher Samba-Freigabename")
        if not Path(path).is_absolute() or ".." in Path(path).parts:
            raise USBError("Samba-Freigabepfad ist nicht absolut/eindeutig")
        if not re.fullmatch(r"S-1-\d+(?:-\d+)+:[FRD](?:,S-1-\d+(?:-\d+)+:[FRD])*", fields["usershare_acl"], re.I):
            raise USBError("Ungültige Samba-usershare-ACL")
        if fields.get("guest_ok", "n") not in ("y", "n"):
            raise USBError("Ungültige Samba-usershare-Gasteinstellung")
        return plain(name), plain(path)

    def shares(self):
        shares = {}
        try:
            with self.directory() as directory:
                for filename in sorted(os.listdir(directory)):
                    if filename.startswith(":tmp"):
                        continue  # Samba's in-progress atomic add, never a published share.
                    metadata = os.stat(filename, dir_fd=directory, follow_symlinks=False)
                    if metadata.st_uid != self.user.uid:
                        continue  # Match net usershare info's default: only this user's definitions.
                    fd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                    with os.fdopen(fd) as input_file:
                        opened = os.fstat(input_file.fileno())
                        if (not stat.S_ISREG(opened.st_mode) or opened.st_uid != self.user.uid
                                or opened.st_mode & 0o022 or opened.st_size > 10240
                                or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)):
                            raise USBError(f"Unsichere Samba-usershare-Datei: {filename}")
                        content = input_file.read(10241)
                        if len(content.encode()) > 10240:
                            raise USBError(f"Samba-usershare-Datei ist zu groß: {filename}")
                    name, path = self.definition(filename, content)
                    if name.casefold() in {n.casefold() for n in shares}:
                        raise USBError("Mehrdeutiger Samba-Freigabename")
                    shares[name] = path
        except (OSError, ValueError, USBError) as error:
            raise CommandError(f"Samba-Freigabedefinitionen nicht vollständig lesbar: {error}") from error
        return shares

    def reserved(self):
        result = self.system.run(["testparm", "-s"])
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.read_string(result.stdout)
        return {name.casefold() for name in parser.sections()} | {"global", "t95-data"}

    def add(self, name, path):
        self.system.as_user(self.user, ["net", "usershare", "add", name, path,
                                       "T95 USB automatisch", self.user.name + ":F", "guest_ok=n"])
        if self.shares().get(name) != path:
            raise USBError("Samba hat die neue Freigabe nicht bestätigt")
        # Validate only the newly mounted share; an unrelated stale definition
        # must not prevent healthy devices being published.
        result = self.system.as_user(self.user, ["net", "usershare", "info", name])
        parser = configparser.ConfigParser(interpolation=None, delimiters=("=",), strict=True)
        parser.read_string(result.stdout)
        if not parser.has_section(name) or parser[name].get("path") != path:
            raise USBError("Samba hat die neue Freigabe nicht bestätigt")

    def delete(self, name):
        self.system.as_user(self.user, ["net", "usershare", "delete", name])
        if name in self.shares():
            raise USBError("Samba-Freigabe wurde nicht entfernt")


class Manager:
    def __init__(self, user, system=None, runtime=None, state=None, net=None):
        self.user = user
        self.system = system or System()
        self.runtime = runtime or Runtime(user)
        self.state = state or UserState(user)
        self.net = net or Net(self.system, user)

    def record(self, snapshot, mount, share):
        device = snapshot.device_at(mount)
        disk = snapshot.disk(device)
        return {"schema": 1, **disk.identity(), "device": device,
                "number": str(mount["maj:min"]), "path": mount["target"], "share": share,
                "uuid": str(snapshot.nodes[device].get("uuid") or "")}

    def eligible(self, snapshot, mount):
        path = Path(plain(mount["target"]))
        if not below(path, self.user.base) or path.resolve() != path or mount["fstype"] not in SUPPORTED:
            return False
        disk = snapshot.disk(snapshot.device_at(mount))
        snapshot.disk_mounts(disk, self.user)
        return not self.runtime.guarded(disk)

    def valid_record(self, snapshot, record):
        mount = snapshot.at(record["path"])
        if not mount or not below(Path(record["path"]), self.user.base):
            return False
        device = snapshot.device_at(mount)
        if device != record["device"] or (record["uuid"] and
                str(snapshot.nodes[device].get("uuid") or "") != record["uuid"]):
            return False
        if record["schema"] == 1:
            disk = snapshot.disk(device)
            if any(record.get(k) != v for k, v in disk.identity().items() if k != "device"):
                return False
        return True

    def reconcile(self):
        with self.runtime.share_lock():
            snapshot = self.system.snapshot()
            shares = self.net.shares()
            records = self.state.read()
            for old in records:
                mount = snapshot.at(old["path"])
                valid = self.valid_record(snapshot, old)
                if not valid:
                    if shares.get(old["share"]) == old["path"]:
                        self.net.delete(old["share"])
                        shares.pop(old["share"])
                    self.state.delete(old)
                elif shares.get(old["share"]) == old["path"]:
                    updated = self.record(snapshot, mount, old["share"])
                    updated["_file"] = old["_file"]
                    self.state.write(updated)
            reserved = self.net.reserved() | self.runtime.reservations(snapshot)
            for mount in snapshot.mounts:
                if not below(Path(mount["target"]), self.user.base):
                    continue
                try:
                    eligible = self.eligible(snapshot, mount)
                except USBError as error:
                    self.system.log(f"Nicht als USB-Projektfreigabe verwaltet: {mount['target']}: {error}")
                    continue
                if eligible:
                    self.publish(snapshot, mount, shares, reserved)

    def publish(self, snapshot, mount, shares, reserved):
        path = mount["target"]
        existing = [name for name, target in shares.items() if target == path]
        if len(existing) > 1:
            raise USBError("Mehrere Usershares zeigen auf denselben Mountpunkt; zuerst prüfen")
        created = not existing
        if existing:
            name = existing[0]
        else:
            device = snapshot.device_at(mount)
            label = plain(snapshot.nodes[device].get("label") or "")
            base = re.sub(r"[^A-Za-z0-9_.-]+", "-", label).strip("-.")[:64] or "Extern-USB"
            occupied = {n.casefold() for n in shares} | reserved
            name, counter = (base, 2) if label else (base + "-1", 2)
            while name.casefold() in occupied:
                name = base + "-" + str(counter)
                counter += 1
        record = self.record(snapshot, mount, name)
        try:
            if created:
                self.net.add(name, path)
                shares[name] = path
            changed = self.state.write(record)
        except Exception:
            if created:
                try:
                    self.net.delete(name)
                except Exception as error:
                    self.system.log(f"FEHLER: Status und Freigabe {name} müssen repariert werden: {error}")
            raise
        if created or changed:
            self.system.log(f"Freigabe bereit: {name} -> {path}")

    def resolve(self, name, snapshot):
        query_error = None
        try:
            shares = self.net.shares()
        except CommandError as error:
            self.system.log(f"Samba-Abfrage fehlgeschlagen; prüfe gespeicherte Zuordnung: {error}")
            query_error, shares = error, {}
        candidates = [shares[name]] if name in shares else [r["path"] for r in self.state.read()
                        if r["share"] == name and self.valid_record(snapshot, r)]
        candidates = sorted(set(candidates))
        live = [snapshot.at(p) for p in candidates if snapshot.at(p)]
        if len(live) == 1:
            return snapshot.disk(snapshot.device_at(live[0]))
        if not live:
            matches = []
            for previous in self.runtime.operations():
                if name in previous["shares"]:
                    try:
                        disk = snapshot.disk(previous["device"])
                    except USBError:
                        continue
                    if disk.identity() == {k: previous[k] for k in disk.identity()}:
                        matches.append(disk)
            if len({d.seq for d in matches}) == 1:
                return matches[-1]
        if query_error:
            raise USBError("Samba-Abfrage fehlgeschlagen und keine eindeutige aktuelle Zuordnung vorhanden") from query_error
        raise USBError("Keine eindeutig zugeordnete gemountete USB-Freigabe gefunden")

    def eject(self, name):
        plain(name)
        snapshot = self.system.snapshot()
        disk = self.resolve(name, snapshot)
        # Root-owned operation lock; it never blocks another physical drive.
        with self.runtime.lock("disk-" + disk.seq + ".lock", create=True, wait=0):
            names = {name}
            target_shares = {}
            try:
                for operation in self.runtime.operations():
                    if disk.identity() == {k: operation.get(k) for k in disk.identity()}:
                        names.update(operation["shares"])
                        target_shares.update(operation.get("paths", {}))
                with self.runtime.share_lock():
                    snapshot = self.system.snapshot()
                    snapshot.verify(disk)
                    snapshot.disk_mounts(disk, self.user)
                    shares = self.net.shares()  # Failure is not interpreted as absence.
                    target_shares = {n: p for n, p in target_shares.items() if shares.get(n) == p
                                     and (not snapshot.at(p) or snapshot.belongs(snapshot.at(p), disk))}
                    for share, path in shares.items():
                        mount = snapshot.at(path)
                        if mount and snapshot.belongs(mount, disk):
                            names.add(share)
                            target_shares[share] = path
                    self.runtime.guard(disk, names)
                    self.runtime.operation(disk, "ejecting", names, paths=target_shares)
                self.system.log(f"Auswerfen: {disk.device}; Freigaben: {', '.join(sorted(names))}")
                self.system.activate_guard(disk)
                snapshot = self.system.wait_guard(disk)
                mounts = snapshot.disk_mounts(disk, self.user)
                for share in sorted(names):
                    if share in target_shares:
                        with self.runtime.share_lock():
                            self.system.snapshot().verify(disk)
                            latest_shares = self.net.shares()
                            if share in latest_shares:
                                if latest_shares[share] != target_shares[share]:
                                    raise USBError("Freigabe wurde vor dem Schließen verändert")
                                self.system.close_share(share)
                for mount in mounts:
                    current = self.system.snapshot()
                    current.verify(disk)
                    current.disk_mounts(disk, self.user)
                    selected = current.at(mount["target"])
                    if selected:
                        if not current.belongs(selected, disk):
                            raise USBError("Mountpunkt gehört inzwischen zu einem anderen Gerät")
                        self.system.sync(mount["target"])
                        checked = self.system.snapshot()
                        checked.verify(disk)
                        checked.disk_mounts(disk, self.user)
                        selected = checked.at(mount["target"])
                        if not selected:
                            continue
                        if not checked.belongs(selected, disk):
                            raise USBError("Mountpunkt wurde während der Synchronisation ersetzt")
                        self.system.unmount(mount["target"])
                snapshot = self.system.snapshot()
                snapshot.verify(disk)
                if snapshot.disk_mounts(disk, self.user):
                    raise USBError("Mounts sind noch vorhanden; nicht abziehen")
                self.system.wait_guard(disk)
                with self.runtime.share_lock():
                    current = self.net.shares()
                    latest = self.system.snapshot()
                    latest.verify(disk)
                    if latest.disk_mounts(disk, self.user):
                        raise USBError("Laufwerk wurde vor der Freigabebereinigung erneut eingebunden")
                    for share in names:
                        if share in current and share in target_shares:
                            if current[share] != target_shares[share]:
                                raise USBError("Freigabe wurde zwischenzeitlich verändert")
                            occupied = latest.at(current[share])
                            if occupied and not latest.belongs(occupied, disk):
                                raise USBError("Freigabepfad gehört inzwischen zu einem anderen Gerät")
                            self.net.delete(share)
                    for record in self.state.read():
                        same_device = record["device"] in disk.nodes and (not record["uuid"] or
                            record["uuid"] == str(snapshot.nodes[record["device"]].get("uuid") or ""))
                        same_attachment = record["schema"] == 0 or all(record.get(k) == v for k, v in disk.identity().items() if k != "device")
                        if record["share"] in names and same_device and same_attachment:
                            self.state.delete(record)
                self.runtime.operation(disk, "unmounted", names, paths=target_shares)
                snapshot = self.system.snapshot()
                snapshot.verify(disk)
                if snapshot.disk_mounts(disk, self.user):
                    raise USBError("Laufwerk wurde vor dem Abschalten erneut eingebunden")
                props = snapshot.drives[disk.drive]
                sibling = str(props.get("SiblingId", ""))
                neighbours = sibling and any(path != disk.drive and str(p.get("SiblingId", "")) == sibling
                                             for path, p in snapshot.drives.items())
                can_off = bool(props.get("CanPowerOff")) and not neighbours
                if can_off and self.system.power_off(disk.drive):
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        latest = self.system.snapshot()
                        if disk.device not in latest.nodes:
                            break
                        latest.verify(disk)
                        time.sleep(0.1)
                    else:
                        raise USBError("USB-Abschalten wurde nicht durch Geräteentfernung bestätigt")
                    self.runtime.operation(disk, "powered-off", names, paths=target_shares)
                    self.system.log("USB-Datenträger kann entfernt werden.")
                else:
                    latest = self.system.wait_guard(disk)
                    if latest.disk_mounts(disk, self.user):
                        raise USBError("Laufwerk wurde erneut eingebunden; nicht abziehen")
                    self.runtime.operation(disk, "ejected", names, paths=target_shares)
                    self.system.log("Sicher ausgehängt; Hardware bleibt eingeschaltet. Du kannst das Laufwerk abziehen.")
            except (Exception, KeyboardInterrupt) as error:
                self.runtime.operation(disk, "failed", names, str(error) or "Unterbrochen", paths=target_shares)
                self.system.log("FEHLER: Auswurf unvollständig. Nicht abziehen; Status prüfen und erneut versuchen.")
                raise

    def status(self):
        snapshot = self.system.snapshot()
        print("USB-Automounter:", self.system.service(self.user, ["is-active", "udiskie.service"], check=False).stdout.strip())
        print("Samba-USB-Freigaben:")
        share_error = None
        try:
            shares = self.net.shares()
        except USBError as error:
            shares, share_error = {}, error
            print(f"  FEHLER: {error}")
        for name, path in shares.items():
            print(f"  {name}: {path}")
        seen = set()
        for node in snapshot.nodes.values():
            if node["type"] != "disk":
                continue
            try:
                disk = snapshot.disk(node["name"])
            except USBError as error:
                print(f"Nicht verwaltet: {node['name']}: {error}")
                continue
            if disk.seq in seen:
                continue
            seen.add(disk.seq)
            print(f"USB: {disk.device}; diskseq={disk.seq}; Auswurfsperre={'aktiv' if self.runtime.guarded(disk) else 'aus'}")
            for device in disk.nodes:
                node = snapshot.nodes[device]
                if node.get("fstype"):
                    print(f"  {device}: {node['fstype']}; Label: {node.get('label') or '–'}")
            try:
                mounts = snapshot.disk_mounts(disk, self.user)
            except USBError as error:
                print(f"  Nicht zum Auswerfen freigegeben: {error}")
                continue
            if not mounts:
                print("  Nicht eingehängt; Auswurfsperre aktiv." if self.runtime.guarded(disk) else
                      "  Nicht eingehängt. Mountfehler im Kernel-/udiskie-Protokoll prüfen.")
            for mount in mounts:
                read, write, traverse = self.system.permissions(self.user, mount["target"])
                print(f"  {mount['target']} ({mount['fstype']}); Benutzerrechte: lesen={read and traverse}, schreiben={write and traverse}")
        for operation in self.runtime.operations():
            print(f"Vorgang {operation['device']}: {operation['phase']}; {operation.get('error') or '–'}")
        print("ext4: Linux-Dateirechte gelten weiter. NTFS: dirty/hiberniert kann Mount verhindern. Keine automatische Reparatur.")
        if share_error is not None:
            raise USBError("Status unvollständig: Samba-Freigabedefinitionen konnten nicht vollständig geprüft werden") from share_error


def cleanup_guard(seq, runtime=RUNTIME):
    if not re.fullmatch(r"[0-9]+", seq):
        raise USBError("Ungültige diskseq")
    safe_directory(runtime)
    safe_directory(runtime / "guards")
    (runtime / "guards" / seq).unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("hook", "eject", "guard-cleanup"))
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.action == "eject" and (len(args.arguments) != 1 or not args.arguments[0]
            or (args.arguments[0].startswith("-") and args.arguments[0] != "--status")):
        parser.error('Aufruf: usb-eject "Freigabename" oder usb-eject --status')
    try:
        if args.action == "guard-cleanup":
            if os.geteuid() != 0 or len(args.arguments) != 1:
                parser.error("guard-cleanup erfordert root und genau eine diskseq")
            cleanup_guard(args.arguments[0])
            return 0
        username = os.environ.get("T95_USER") or os.environ.get("SUDO_USER") or pwd.getpwuid(os.getuid()).pw_name
        user = User.lookup(username)
        manager = Manager(user)
        if args.action == "eject":
            if os.geteuid() != 0:
                raise USBError("Bitte mit sudo ausführen")
            if len(args.arguments) != 1:
                parser.error('Aufruf: usb-eject "Freigabename" oder usb-eject --status')
            if args.arguments == ["--status"]:
                manager.status()
            elif args.arguments[0].startswith("-"):
                parser.error("Unbekannte Option")
            else:
                manager.eject(args.arguments[0])
        else:
            if os.geteuid() != user.uid:
                raise USBError("Freigabe-Hook muss als eingerichteter Benutzer laufen")
            if not args.arguments or args.arguments[0] not in ("startup", "reconcile", "device_mounted", "device_unmounted", "device_removed", "device_added", "device_changed", "job_failed"):
                return 0
            manager.reconcile()
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print("FEHLER:", str(error) or "Unterbrochen", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

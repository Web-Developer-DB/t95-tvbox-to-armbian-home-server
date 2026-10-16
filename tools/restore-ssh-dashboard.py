#!/usr/bin/env python3
"""Restore the archived MOTD files; preview by default, with backup and rollback."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
from datetime import datetime, timezone

ARCHIVE = Path(__file__).resolve().parents[1] / "server/ssh-dashboard/2026-10-16"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="install after creating a backup")
    action.add_argument("--rollback", type=Path, help="restore a backup created by this tool")
    parser.add_argument("--root", type=Path, default=Path("/"), help="alternative filesystem root for tests")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    entries = json.loads((ARCHIVE / "manifest.json").read_text())["files"]
    names = {entry["path"] for entry in entries}
    if len(names) != len(entries):
        raise ValueError("Duplicate manifest paths")
    for entry in entries:
        relative = PurePosixPath(entry["path"])
        allowed = (relative.parent == PurePosixPath("etc/update-motd.d") or
                   str(relative) in {"etc/default/armbian-motd", "usr/lib/armbian/armbian-allwinner-battery"})
        source = ARCHIVE / "rootfs" / relative
        if relative.is_absolute() or ".." in relative.parts or not allowed:
            raise ValueError("Unsupported manifest path")
        if source.is_symlink() or digest(source) != entry["sha256"]:
            raise ValueError(f"Payload checksum mismatch: {relative}")
        if entry["mode"] not in {"0644", "0755"}:
            raise ValueError("Unsupported file mode")

    def target(relative):
        if relative not in names:
            raise ValueError("Backup path is outside the archived file set")
        path = root / relative
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError(f"Refusing a redirected target: {relative}")
        if path.exists() and not path.is_file():
            raise ValueError(f"Target is not a regular file: {relative}")
        return path

    def replace(source, destination, mode, owner=None):
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".t95-motd-", dir=destination.parent)
        os.close(fd)
        temporary = Path(name)
        try:
            shutil.copy2(source, temporary)
            temporary.chmod(mode)
            if owner is not None and os.geteuid() == 0:
                os.chown(temporary, *owner)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

    backup_root = root / "var/backups/t95-dashboard"

    def rollback(backup):
        backup = backup.resolve(strict=True)
        if backup.is_symlink() or not backup.is_relative_to(backup_root.resolve()):
            raise ValueError("Backup must be inside var/backups/t95-dashboard")
        records = json.loads((backup / "backup.json").read_text())
        if len(records) != len(names) or {record["path"] for record in records} != names:
            raise ValueError("Backup file set differs from this snapshot")
        for record in records:
            target(record["path"])
            if record["existed"]:
                source = backup / "rootfs" / record["path"]
                if source.is_symlink() or digest(source) != record["sha256"]:
                    raise ValueError("Backup checksum mismatch")
        for record in records:
            destination = target(record["path"])
            if record["existed"]:
                replace(backup / "rootfs" / record["path"], destination,
                        record["mode"], (record["uid"], record["gid"]))
            else:
                destination.unlink(missing_ok=True)
        print(f"Backup restored: {backup}")

    if (args.apply or args.rollback) and root == Path("/") and os.geteuid() != 0:
        raise PermissionError("Use sudo for installation or rollback on the real system")
    if args.rollback:
        rollback(args.rollback)
        return

    changes = []
    for entry in entries:
        destination = target(entry["path"])
        if (not destination.exists() or digest(destination) != entry["sha256"] or
                stat.S_IMODE(destination.stat().st_mode) != int(entry["mode"], 8)):
            changes.append(entry)
    print(f"Payload verified: {len(entries)} files; {len(changes)} changes")
    if not args.apply:
        for entry in changes:
            print(f"  {entry['mode']} /{entry['path']}")
        print("Preview only. Use --apply to install, or --root DIR for a test filesystem.")
        return
    if not (root / "etc/armbian-release").is_file():
        raise ValueError("This snapshot requires an existing Armbian installation")
    if not changes:
        print("The archived dashboard is already installed; no backup needed.")
        return

    backup_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-"), dir=backup_root))
    records = []
    for entry in entries:
        destination = target(entry["path"])
        record = {"path": entry["path"], "existed": destination.exists()}
        if destination.exists():
            metadata = destination.stat()
            old = backup / "rootfs" / entry["path"]
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, old)
            record.update(mode=stat.S_IMODE(metadata.st_mode), uid=metadata.st_uid,
                          gid=metadata.st_gid, sha256=digest(old))
        records.append(record)
    manifest = backup / "backup.json"
    manifest.write_text(json.dumps(records, indent=2) + "\n")
    manifest.chmod(0o600)
    try:
        for entry in changes:
            destination = target(entry["path"])
            replace(ARCHIVE / "rootfs" / entry["path"], destination, int(entry["mode"], 8))
            if digest(destination) != entry["sha256"]:
                raise ValueError("Installed checksum mismatch")
    except Exception:
        rollback(backup)
        raise
    print(f"Installed. Backup: {backup}")
    print("The next SSH login will generate current readings. No SSH restart is required.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(f"Dashboard restore failed: {error}")

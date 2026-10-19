# ⚙️ Technical reference: Samba and USB

[Deutsch](SAMBA-USB-SETUP.md) | **English**

New users should follow the [module guide](../README.en.md). This reference
describes the implementation updated 2026-10-19. Earlier manual recipes have
been replaced by the installer and its `--update` mode.

| Layer | Purpose |
| --- | --- |
| Samba | Fixed `T95-DATA` plus individual USB usershares |
| UDisks / udiskie | Mount filesystems and report events |
| Shared Python core | Device identity, shares, state and targeted eject |
| udev | Prevent remounting only the ejected drive |

## 📦 Installation and updates

The installer verifies the entire package manifest before APT. Replaced files
and earlier service states are backed up privately at
`/var/lib/t95-samba/installation-…/`. Dependencies include Python 3 with
`python3-dbus`, udev and util-linux. Installed core: `/usr/local/lib/t95-usb/`.

`T95_USER` selects an existing normal Linux user; actual UID and primary GID are
resolved. `DATA_PATH` and `NETBIOS_NAME` customize fresh setup. The default data
path is `/srv/T95-DATA/Share`; the recommended SD setup explicitly uses
`/srv/t95-sd-data/Share`.

`--update` preserves Samba configuration, passwords, data path and custom fixed
shares. It validates required usershare settings and reports missing values.
Existing `config.yml` stays intact; the service explicitly selects
`--config=%h/.config/udiskie/config.json`.

After daemon reload, enabling and a deliberate udiskie restart, mounted storage
is reconciled. A stale user-manager group list prevents false setup success;
the error requests a controlled reboot followed by another setup invocation.

## 🧩 Shares and state

A short shared lock protects name allocation, publication and state changes.
Labels are sanitized; unlabelled storage uses names such as `Extern-USB-1`.
Collisions receive counters. Fixed shares and names reserved for still-attached
ejected drives are excluded from allocation.

Atomic JSON mappings in `~/.local/state/t95-usb-shares/` contain schema version,
share, mount, partition and current device identity. Old `.map` files are
migrated only after validating the current mapping. Records are never executed
as shell code. Device/Samba query failures are not treated as empty results.

The hook reconciles actual mounts at startup and on device events. Repeated
events do not create duplicate shares. Failed state writes roll back newly
created shares or log an explicit repair requirement.

## ⏏️ Targeted eject

`usb-eject` resolves a share to its whole physical USB drive. Boot ID, canonical
sysfs path and `diskseq` distinguish reused device names. System/foreign mounts,
swap and unsupported storage topologies prevent ejection.

A root-managed guard is installed under `/run/t95-usb/` before unmounting.
The udev rule applies `UDISKS_IGNORE=1` and `UDISKS_AUTO=0` only to this disk and
its partitions. UDisks must confirm the guard and pending device jobs must end.
**udiskie continues running throughout ejection.**

Connections to all associated Samba shares are closed. Filesystems are synced
and mounts unmounted from the deepest path outward. Btrfs and FUSE NTFS can
have anonymous mount device numbers, so the real block source is also used.
Only confirmed unmounting permits deletion of associated shares and mappings.

Power-off is attempted only when supported and when sibling drives in a shared
physical device would not be affected. Otherwise confirmed unmounting with an
active remount guard permits safe unplugging. Unexpected power-off errors are
reported as failures.

The guard remains until unplugging or reboot. Restarting udiskie does not clear
it; a new attachment does not inherit it. Operation journals under
`/run/t95-usb/operations/` are private. Name reservations are readable, but only
root can change them.

## 🔎 Diagnostics and rollback

**On the T95, normal SSH user:**

```bash
sudo usb-eject --status
sudo journalctl -t T95-USB-SHARE -b --no-pager -n 60
systemctl --user status udiskie.service --no-pager -l
```

Status lists devices, filesystems, mounts, user access, shares, guards and failed
ejections. Exit codes: `0` confirmed success, `1` operation failure, `2` invalid
invocation. Some partitions may already be unmounted after an error; inspect
status and repeat the same eject command.

Installation failures automatically restore and verify project files and prior
service states. Failed restoration remains visible as `rollback-failed` with a
backup path. Packages, groups and linger may remain. A later manual restoration
requires inspecting the private journal and any subsequent changes.

## 🧪 Evidence and boundaries

[Audit/fix status](../../../docs/SAMBA_USB_AUDIT.en.md) ·
[Hardware acceptance](RESTORE-CHECKLIST.en.md) · [Troubleshooting](TROUBLESHOOTING.en.md)

Supported scope: ext4, exFAT, FAT32, NTFS and Btrfs on one physical drive.
Unix permissions, drivers and volume condition still apply. No automatic repair,
formatting, force-unmounting or recursive permission changes. Hardware acceptance
of the new implementation is pending.

<!-- Compatibility anchors for older documentation links. -->
<a id="-1-target-design"></a>
<a id="-10-restore-limits"></a>
<a id="-2-verified-server-state"></a>
<a id="-3-packages-and-account"></a>
<a id="-4-samba-configuration"></a>
<a id="-5-udisks-polkit-and-udiskie-service"></a>
<a id="-6-dynamic-share-and-eject-scripts"></a>
<a id="-7-validation"></a>
<a id="-8-common-failure-patterns"></a>
<a id="-9-security-and-publication"></a>
<a id="-complete-guide-samba--dynamic-usb-shares-on-t95armbian"></a>
<a id="1-target-design"></a>
<a id="10-restore-limits"></a>
<a id="2-verified-server-state"></a>
<a id="3-packages-and-account"></a>
<a id="4-samba-configuration"></a>
<a id="5-udisks-polkit-and-udiskie-service"></a>
<a id="6-dynamic-share-and-eject-scripts"></a>
<a id="7-validation"></a>
<a id="8-common-failure-patterns"></a>
<a id="9-security-and-publication"></a>
<a id="complete-guide-samba--dynamic-usb-shares-on-t95armbian"></a>

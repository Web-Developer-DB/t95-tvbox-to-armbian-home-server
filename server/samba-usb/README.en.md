<a id="file-sharing-and-usb-drives-on-the-t95"></a>

# 📂 File sharing and USB drives on the T95

[Deutsch](README.md) | **English**

**Plug in USB storage and share files at home.** This module combines regular
Samba packages with a project configuration for the T95 and its USB ports.
Supported sticks, SSDs and disks are mounted automatically and published as
individual shares for PCs, phones and VLC.

**Ejecting one drive keeps the others usable.** The automounter continues
running and accepts newly connected USB devices during ejection.
The recommended fixed `T95-DATA` share uses the system SD at
`/srv/t95-sd-data/Share`; USB shares are independent.

| Your goal | Continue here |
| --- | --- |
| 🚀 New file server | [Requirements](#requirements) → [Setup](#set-up-file-sharing) |
| 🔄 Update an existing setup | [Preserve Samba configuration](#update-an-existing-setup) |
| 📂 Access files | [PCs, phones and VLC](#client-and-vlc-access) |
| ⏏️ Unplug a drive | [Eject that drive safely](#safely-eject-usb-storage) |
| 🔎 Understand an error | [Status and troubleshooting](docs/TROUBLESHOOTING.en.md) |

> [!IMPORTANT]
> **USB implementation updated 2026-10-19:** audit fixes are covered by automated
> tests. An existing-setup update and exFAT Samba read/write, eject/power-off and
> reconnection are confirmed on the T95. Other filesystem and multiple-device
> tests remain pending. [Evidence and checklist](../../docs/SAMBA_USB_AUDIT.en.md).

<a id="requirements"></a>

## 📋 Requirements

- T95 running the tested Armbian image; normal SSH user with `sudo`.
- [Kernel/DTB protection](../../docs/INSTALLATION.en.md#5-protect-the-kernel-and-dtb-before-updates) enabled; Internet for installation.
- Healthy ext4, exFAT, FAT32 or NTFS USB storage. Existing ext4 Unix permissions still apply.
- Btrfs: one physical drive, including subvolumes. LUKS, LVM, RAID and multi-device Btrfs are outside the supported scope.
- Adequate power; externally power disks when needed.

An [SD backup](../../docs/BACKUP.en.md) is optional. Internal eMMC is not prepared
or formatted by this module.

<a id="set-up-file-sharing"></a>
<a id="quick-start-reproducible-restore"></a>

## 🚀 Set up file sharing

> [!WARNING]
> **Fresh setup replaces Samba configuration after a private backup.**
> Use [update mode](#update-an-existing-setup) for an existing installation.

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo apt update
sudo apt install -y git
git clone --branch main --depth 1 https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git
cd t95-tvbox-to-armbian-home-server/server/samba-usb
sha256sum -c MANIFEST.sha256
```

Expected: all checksum entries show `OK`. If the repository folder already
exists, inspect local changes and use an up-to-date verified copy.

**On the T95, same terminal, normal SSH user:**

```bash
export T95_USER="$(id -un)"
id "$T95_USER"
sudo T95_USER="$T95_USER" DATA_PATH=/srv/t95-sd-data/Share ./scripts/restore-samba-usb-setup.sh
```

`sudo` requests your Linux password. If no Samba account exists, setup then
requests a separate Samba password. Password input stays invisible.
**Success: `Fertig.`** Then [verify access](#verify-after-installation).

If setup reports that the user manager does not yet know `sambashare`, it reports
failure and restores project configuration. Reboot the box in a controlled
manner, then repeat the same setup command. With linger enabled, a new SSH login
alone does not refresh that manager's groups.

<a id="update-an-existing-setup"></a>

## 🔄 Update an existing setup

**Prerequisite:** current verified repository copy; work in `server/samba-usb`.
Inspect local changes before updating that copy.

**On the T95, normal SSH user:**

```bash
sha256sum -c MANIFEST.sha256
sudo T95_USER="$(id -un)" ./scripts/restore-samba-usb-setup.sh --update
```

Expected: `Fertig. Bestehende Samba-Konfiguration erhalten.` Samba passwords,
data path and custom Samba shares are preserved. Missing required Samba settings
are reported with correction guidance; update mode does not rewrite them.
udiskie restarts to load its configuration, then existing mounts are reconciled
with shares.

<a id="verify-after-installation"></a>

## ✅ Verify after installation

**On the T95, normal SSH user:**

```bash
sudo usb-eject --status
net usershare list
```

Expected: active automounter and a separate share for each supported mounted
USB filesystem. The usershare list may be empty without USB storage.
Fixed `T95-DATA` is not included in that list.

The drive overview shows connected USB drives; internal SD, eMMC and ZRAM
devices are hidden. Operations from earlier device connections are hidden too.
Warnings about a currently connected USB drive remain visible, including
mount failures or blocked ejections. Status alone does not establish that it
is safe to unplug; use the [eject command](#safely-eject-usb-storage).

<a id="client-and-vlc-access"></a>

## 📂 Client and VLC access

| Client | Address or action |
| --- | --- |
| Linux file manager | `smb://SERVER-IP/` |
| Windows Explorer | `\\SERVER-IP\` |
| Phone / VLC | SMB network access → server address → select share |

Replace `SERVER-IP` with the box address. Use your T95 username and **Samba
password**. Write and reopen a small file in `T95-DATA` or the chosen USB share.
Setup does not automatically change a read-only filesystem or existing ext4 permissions.

<a id="safely-eject-usb-storage"></a>

## ⏏️ Safely eject USB storage

**On the T95, normal SSH user:**

```bash
net usershare list
read -r -p 'Share name of the drive to eject: ' T95_SHARE
```

Enter its actual name from the list and press Enter. Then:

**On the T95, same terminal, normal SSH user:**

```bash
sudo usb-eject "$T95_SHARE"
```

**This ejects the entire physical drive, including its other partitions and
shares.** Other physical drives remain usable.

| Message | Meaning and next action |
| --- | --- |
| `USB-Datenträger kann entfernt werden.` | Power-off confirmed by device removal; unplug. |
| `Sicher ausgehängt; Hardware bleibt eingeschaltet. Du kannst das Laufwerk abziehen.` | Mounts/shares removed; a per-drive remount guard is active. Safe to unplug. |
| `FEHLER: Auswurf unvollständig…` | Do not unplug. Check status, close open files/terminal working directories and retry. |

An error may leave some partitions already unmounted. The guard still applies
only to this drive. Repeating the command can resume an interrupted operation.
After successful unmounting, the drive remains guarded until unplugged.
Reconnecting creates a share again; rebooting also clears runtime guards.

<a id="undo-setup"></a>
<a id="restore-configuration-and-keep-secrets-private"></a>

## ↩️ Backup and recovery

Before changes, private backups are created at
`/var/lib/t95-samba/installation-…/`, including file copies and `state.json`.
Activation failures restore backed-up project files and earlier service states.
A failed rollback is recorded as `rollback-failed`. Packages, groups and shared
linger may remain.

A later deliberate return to an older setup is a manual administrative step:
inspect the selected backup and current changes first. There is no blanket
uninstall/restore command. Backups can contain private configuration and stay
on the box.

<a id="what-does-the-samba-module-set-up"></a>
<a id="result-at-a-glance"></a>

## ⚙️ Components and boundaries

| Component | Purpose |
| --- | --- |
| Samba | Fixed data share and authenticated dynamic USB usershares |
| UDisks + udiskie | Mount supported devices using an explicit project configuration |
| Shared Python core | Device identity, name locks, atomic JSON mappings and eject |
| udev eject guard | Hold back only the selected drive's current attachment |

`T95_USER`, `DATA_PATH` and `NETBIOS_NAME` customize fresh setup.
Without `DATA_PATH`, the default is `/srv/T95-DATA/Share`; without an eMMC mount
there, that folder also resides on SD. The recommended command therefore sets
an explicit SD path. `--update` preserves the existing Samba data path.
There is no automatic filesystem repair, formatting, force-mounting or recursive
change of existing ownership/permissions.

[Technical reference](docs/SAMBA-USB-SETUP.en.md) · [Troubleshooting](docs/TROUBLESHOOTING.en.md) ·
[Acceptance checklist](docs/RESTORE-CHECKLIST.en.md) · [Audit and limits](../../docs/SAMBA_USB_AUDIT.en.md)

<!-- Compatibility anchors for older documentation links. -->
<a id="-further-documentation"></a>
<a id="-restore-configuration-and-keep-secrets-private"></a>
<a id="-result-at-a-glance"></a>
<a id="-undo-setup"></a>
<a id="-what-does-the-samba-module-set-up"></a>
<a id="1-get-the-module-and-verify-its-manifest"></a>
<a id="2-check-your-linux-user-and-network"></a>
<a id="3-run-installation"></a>
<a id="change-settings-later"></a>
<a id="customize-setup"></a>
<a id="further-documentation"></a>
<a id="t95-samba--usb-automount"></a>
<a id="what-each-script-does"></a>
<a id="which-storage-location-should-i-use"></a>

# Complete guide: Samba + dynamic USB shares on T95/Armbian

[Deutsch](SAMBA-USB-SETUP.md) | **English**

This is the technical reference for the reproducible T95 Samba/USB module.
Use the installation script in [../README.en.md](../README.en.md) for the
normal supported path; use this document to understand, audit, adapt, or
restore the components.

## 1. Target design

The running Armbian T95 publishes a fixed internal `T95-DATA` share and one
dynamic Samba usershare for each mounted USB/SSD filesystem. UDisks2 performs
mount/power operations, Polkit permits the selected user to do so without an
interactive desktop agent, and udiskie runs persistently as that user's systemd
user service. `t95-usb-share` receives udiskie events and creates/removes the
corresponding usershare.

There is deliberately no static `[USB]` share. Per-volume shares correctly
show capacity/free space and make safe eject targetable. The preferred client
entry point is `smb://<SERVER-IP>/`.

## 2. Verified server state

The reference is T95 `H616-T95MAX-AXP313A-V3.0`, Armbian 26.8.4/Debian 13,
kernel 6.18, `end0` Ethernet with DHCP, and an optional ext4 eMMC data mount at
`/srv/T95-DATA`. eMMC is a data medium here, not a supported Armbian boot
device. Ensure Linux, SD boot, Ethernet, and SSH work before installing Samba.

## 3. Packages and account

Install the package set used by the restore script:

```bash
sudo apt update
sudo apt install -y samba samba-common-bin udisks2 udiskie dbus-user-session \
  polkitd exfatprogs ntfs-3g
```

Select an existing regular Linux user and set variables:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
id "$T95_USER"
sudo smbpasswd -a "$T95_USER"
```

The user needs Samba membership and a writable usershare directory:

```bash
sudo usermod -aG sambashare "$T95_USER"
sudo install -d -o root -g sambashare -m 1770 /var/lib/samba/usershares
sudo install -d -o "$T95_USER" -g "$T95_USER" -m 2770 /srv/T95-DATA/Share
```

When the data path is on eMMC, mount it permanently before this step and verify
with `findmnt`; do not format/partition eMMC from this module.

## 4. Samba configuration

Use `config/samba/smb.conf.fragment` as the known reference. It configures
standalone Samba, SMB2 minimum protocol, usershares below
`/media/$T95_USER`, and `[T95-DATA]` at `/srv/T95-DATA/Share`. Validate and
start services:

```bash
sudo testparm -s
sudo systemctl enable --now smbd nmbd
```

Back up an existing `/etc/samba/smb.conf` before replacement. Do not create a
static `[USB]` share.

## 5. UDisks, Polkit, and udiskie service

Install `config/polkit/50-t95-udisks.rules` as
`/etc/polkit-1/rules.d/50-t95-udisks.rules`. Copy
`config/udiskie/config.json` to
`/home/$T95_USER/.config/udiskie/config.json` and
`config/systemd-user/udiskie.service` to
`/home/$T95_USER/.config/systemd/user/udiskie.service`; set ownership to
`$T95_USER:$T95_USER`.

Enable lingering so the user service starts without an interactive login, then
enable it:

```bash
sudo loginctl enable-linger "$T95_USER"
sudo -u "$T95_USER" XDG_RUNTIME_DIR="/run/user/$T95_UID" \
  systemctl --user enable --now udiskie.service
```

The service's pre-start hook runs `t95-usb-share startup` to restore valid
usershares after service restart.

## 6. Dynamic share and eject scripts

Install `scripts/t95-usb-share` and `scripts/usb-eject` as
`/usr/local/bin/t95-usb-share` and `/usr/local/bin/usb-eject`, mode `0755`.
The first script records mount/share mappings under
`~/.local/state/t95-usb-shares/`, turns labels into safe names, uses
`External-USB-N` for unlabelled media, resolves name collisions with `-2`,
`-3`, and is idempotent for repeated events.

`usb-eject SHARENAME` stops udiskie temporarily, closes only selected Samba
share connections, runs `sync`, unmounts all device partitions, removes state
only after success, calls UDisks power-off, then restarts udiskie. Use the
share name, not a guessed `/dev/sdX`.

## 7. Validation

```bash
sudo testparm -s
systemctl --no-pager --full status smbd nmbd
sudo -u "$T95_USER" net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
journalctl -t T95-USB-SHARE --no-pager -n 30
```

Insert a USB volume. A labelled filesystem should appear as a sanitized
label-derived share; an unlabelled one as `External-USB-1`. Test an
authenticated client connection at `smb://<SERVER-IP>/`, upload/download a
small file, then eject it using `sudo usb-eject SHARENAME`. Confirm the mount,
usershare, and physical device have disappeared; reinserting recreates it.

## 8. Common failure patterns

| Symptom | First check | Relevant fix |
| --- | --- | --- |
| Mount exists, no share | `net usershare list`, `journalctl -t T95-USB-SHARE` | inspect event hook and Polkit/user service |
| Duplicate `External-USB-N` | usershares pointing to same path | retain idempotent mount-point check |
| `command not found` inside script | `PATH` was overwritten | use a variable such as `SAVED_PATH` |
| `DeviceBusy` | `fuser`, `smbstatus --shares` | `smbcontrol smbd close-share SHARENAME` |
| Immediate remount | udiskie still active | stop it for unmount/power-off sequence |

See [TROUBLESHOOTING.en.md](TROUBLESHOOTING.en.md) for commands and recovery
details.

## 9. Security and publication

Do not publish Samba passwords, `passdb.tdb`, `/etc/shadow`, private SSH keys,
complete system images, local UART captures, or personal configuration. The
module templates contain no Samba credentials; `smbpasswd` creates them only
on the target T95. Verify `MANIFEST.sha256` after checkout and regenerate it
after intentional public module changes.

## 10. Restore limits

The script backs up an existing Samba configuration as
`/etc/samba/smb.conf.before-t95.<TIMESTAMP>`. Restore a selected file with
`cp -a`, validate via `testparm -s`, then restart `smbd`. A complete uninstall
of every package, Polkit rule, and user file is intentionally not supplied.

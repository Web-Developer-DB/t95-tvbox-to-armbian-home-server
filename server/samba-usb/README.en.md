# T95 Samba + USB automount

[Deutsch](README.md) | **English**

![Status: tested](https://img.shields.io/badge/Status-Samba%2FUSB%20tested-brightgreen)
![Platform: Armbian](https://img.shields.io/badge/Platform-Armbian%20%2F%20Debian-18a303)
![Protocol: SMB2%2FSMB3](https://img.shields.io/badge/Protocol-SMB2%20%2F%20SMB3-blue)
![Secrets: local](https://img.shields.io/badge/Secrets-never%20on%20GitHub-critical)

Reproducible Samba and USB configuration for a T95 running as an Armbian home
server. Run these instructions **on the running T95**, not on the PC used to
build or write the T95 image.

[Back to installation](../../docs/INSTALLATION.en.md#7-set-up-file-sharing) ·
[Troubleshooting](../../docs/TROUBLESHOOTING.en.md)

**Recommended first setup:** the fixed share explicitly uses the system SD
at `/srv/t95-sd-data/Share`. USB drives get separate shares. eMMC is a later
extension.

## Result at a glance

The server root `smb://<SERVER-IP>/` displays both the fixed internal
`T95-DATA` share and all currently attached USB/SSD shares. There is purposely
no static `[USB]` aggregate share: every volume retains its real capacity and
free-space information.

## What does the Samba module set up?

The module turns the running T95 into an authenticated file server:

- `T95-DATA` is a permanent share for the storage directory you choose.
- USB sticks and disks are mounted automatically.
- Each mounted USB filesystem gets its own share.
- Linux, Windows, Android, and VLC use the same Linux/Samba account.
- `usb-eject` safely disconnects a USB drive before you unplug it.

The fixed `T95-DATA` share and dynamic USB shares are separate. Choose the
fixed share location during setup with `DATA_PATH`. USB storage is mounted and
shared automatically; it does not need a manual path change.

### Which storage location should I use?

| Location | Example `DATA_PATH` | When to use it |
| --- | --- | --- |
| System microSD | `/srv/t95-sd-data/Share` | Small amounts of data and the simplest setup. Frequent writes may wear the SD card faster. |
| Internal eMMC | `/srv/T95-DATA/Share` | Better for regular or larger data when eMMC is already mounted persistently at `/srv/T95-DATA`. |
| USB drive | No `DATA_PATH` needed | USB storage is added automatically as a separate dynamic share. |

The default `/srv/T95-DATA/Share` assumes an eMMC filesystem is mounted at
`/srv/T95-DATA`. Without that mount, the folder is created on the SD card's
system filesystem. To deliberately use the system SD, choose a separate path
such as `/srv/t95-sd-data/Share`. If using eMMC, set it up, mount it
persistently, and verify it with `findmnt` first. The Samba script never
formats, partitions, or moves existing files.

| Area | Tested reference |
| --- | --- |
| Hardware | T95 `H616-T95MAX-AXP313A-V3.0`, Allwinner AC300 Ethernet |
| System | Armbian 26.8.4, Debian 13 Trixie, kernel 6.18 |
| Network | `end0`, DHCP, SMB2/SMB3 |
| Automount | UDisks2 + udiskie + dynamic Samba usershares |
| Acceptance | `T95-DATA`, USB automount, safe eject/reinsert, VLC over SMB |

Other Debian/Armbian systems may work, but are not automatically validated by
this project.

## Requirements

- T95 has booted fully from the working microSD and is reachable by SSH. eMMC
  boot is not supported here.
- eMMC may be mounted as an ext4 data drive. Its mount must already exist
  before Samba access; the restore script never formats or partitions eMMC.
- An ordinary Linux user exists, for example `serveruser`, and may use `sudo`.
- Internet is available during package installation.
- USB disks have adequate external power.
- Existing Samba configuration is backed up or may be replaced.

> [!WARNING]
> The restore script installs packages/services, enables `smbd`, `nmbd`, and
> the `udiskie` user service. It backs up `/etc/samba/smb.conf` with a timestamp
> and replaces it with the known minimal configuration. Read the
> [technical setup guide](docs/SAMBA-USB-SETUP.en.md) first on a production
> Samba server.

## Quick start: reproducible restore

The script replaces `/etc/samba/smb.conf` after a timestamped backup. For
an existing customized Samba installation, first read the
[technical reference](docs/SAMBA-USB-SETUP.en.md).

Run these commands **on the T95 as your normal SSH user with sudo**.
`T95_USER` automatically selects that user; `id` must show your normal
username, not `root`. First apply the
[kernel holds](../../docs/INSTALLATION.en.md#5-protect-the-kernel-and-dtb-before-updates)
and back up the SD. This checkout uses the review branch; it is separate from
the release-tools directory on your PC. If Git is missing, run on the T95:

```bash
sudo apt update
sudo apt install -y git
```

```bash
git clone --branch codex/archive-ssh-dashboard --depth 1 \
  https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git
cd t95-tvbox-to-armbian-home-server/server/samba-usb
sha256sum -c MANIFEST.sha256

export T95_USER="$(id -un)"
id "$T95_USER"
ip -brief address

sudo T95_USER="$T95_USER" DATA_PATH=/srv/t95-sd-data/Share \
  ./scripts/restore-samba-usb-setup.sh
```

The manifest check must complete without `FAILED`. This invocation puts
`T95-DATA` on the SD. The script installs Samba,
UDisks2, udiskie, Polkit, and exFAT/NTFS support. If needed, it asks
interactively for the Samba password of `T95_USER`.

When it prints `Fertig.`, first open `smb://<SERVER-IP>/T95-DATA` in the
**client PC file manager**, or `\\<SERVER-IP>\T95-DATA` in Windows Explorer.
Replace `<SERVER-IP>` with the current router address and sign in with your
Linux username and Samba password. Write/read a small test file; no USB drive
is required yet. Then attach USB storage and inspect its separate share in
the server root `smb://<SERVER-IP>/`.

<details>
<summary>Optional customization and script overview</summary>

### Customize setup

These alternatives replace the quick-start installation command. Use them
only to deliberately choose a different storage location or server name.

Set the username, server name, and fixed share path when running the script.
Replace `serveruser` with your ordinary Linux username. `DATA_PATH` selects
where the fixed `T95-DATA` share points:

```bash
sudo T95_USER=serveruser \
  NETBIOS_NAME=T95-SERVER \
  DATA_PATH=/srv/t95-sd-data/Share \
  ./scripts/restore-samba-usb-setup.sh
```

| Variable | Required | Default | Meaning |
| --- | :---: | --- | --- |
| `T95_USER` | **yes** | – | existing Linux and Samba user |
| `NETBIOS_NAME` | no | `T95-SERVER` | SMB network server name |
| `DATA_PATH` | no | `/srv/T95-DATA/Share` | fixed-share directory |

Example: place the fixed share on the SD system filesystem:

```bash
sudo T95_USER=serveruser \
  DATA_PATH=/srv/t95-sd-data/Share \
  ./scripts/restore-samba-usb-setup.sh
```

Example: use eMMC already mounted at `/srv/T95-DATA`:

```bash
findmnt /srv/T95-DATA
sudo T95_USER=serveruser \
  DATA_PATH=/srv/T95-DATA/Share \
  ./scripts/restore-samba-usb-setup.sh
```

Run the eMMC command only after `findmnt` shows the expected eMMC mount. If it
does not, the directory would be created on the filesystem underneath it,
usually the system SD.

The script also uses `/media/<T95_USER>` as the USB mount base and
`~/.local/state/t95-usb-shares` for dynamic USB mappings.

### Change settings later

Change to the cloned module directory and rerun the restore script with the new
values. For example, to move the `T95-DATA` share location from eMMC to the SD:

```bash
cd ~/t95-tvbox-to-armbian-home-server/server/samba-usb
sudo T95_USER=serveruser \
  DATA_PATH=/srv/t95-sd-data/Share \
  ./scripts/restore-samba-usb-setup.sh
```

The script saves `/etc/samba/smb.conf` with a timestamp and generates a new
configuration. It does **not** move your files to the new location. Copy or
move them yourself and verify the new path before deleting old data. Direct
changes to `/etc/samba/smb.conf` are replaced when the script runs again;
backups are kept at `/etc/samba/smb.conf.before-t95.*`.

### What each script does

| Script | What it does | Do I run it myself? |
| --- | --- | --- |
| `scripts/restore-samba-usb-setup.sh` | Installs packages and services, creates `T95-DATA`, and configures Samba and USB automount. | Yes, once during setup; run again only to change configuration. |
| `scripts/t95-usb-share` | Creates or removes the dynamic share for a mounted USB filesystem. | No, `udiskie` invokes it automatically. |
| `scripts/usb-eject` | Disconnects the selected share, syncs writes, unmounts the drive, and powers it off. | Yes, before physically unplugging a USB drive. |

Use the share name to eject safely:

```bash
sudo usb-eject SunDiskUSB
```

The share name normally matches the drive label. The sections below cover
verification and troubleshooting if something does not work as expected.

</details>

## Verify after installation

```bash
sudo testparm -s
systemctl --no-pager --full status smbd
systemctl --no-pager --full status nmbd
sudo -u "$T95_USER" net usershare list
T95_UID="$(id -u "$T95_USER")"
sudo -u "$T95_USER" XDG_RUNTIME_DIR="/run/user/$T95_UID" \
  systemctl --user --no-pager --full status udiskie.service
```

Expect valid `testparm` output containing `[T95-DATA]` and your selected
path, active `smbd`/where available `nmbd`, and active `udiskie.service`.
`net usershare list` shows dynamic USB shares only; it may be empty when no
USB drive is mounted. The fixed `T95-DATA` share does not belong in that list.

On the client, open `smb://<SERVER-IP>/T95-DATA`, create a small test file,
and read it back to confirm actual access.

After inserting USB storage:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u "$T95_USER" net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 30
```

A labelled volume uses a sanitized label such as `SunDiskUSB`; unlabelled
media use `Extern-USB-1`, then `Extern-USB-2`, and so on. A published mount
point must not create a duplicate share.

## Client and VLC access

Use the server root first:

```text
smb://<SERVER-IP>/
```

Direct paths include `T95-DATA`, label-derived shares, or `Extern-USB-1`.
Linux file managers use `smb://<SERVER-IP>/`; Windows Explorer uses
`\\<SERVER-IP>\`; Android file managers add an SMB share; VLC opens the network
share and selects a compatible file. Use the Samba password of `T95_USER`; no
guest account or clear-text credentials are configured.

## Safely eject USB storage

Use the share name, never guess a `/dev/sdX` device:

```bash
sudo usb-eject SunDiskUSB
sudo usb-eject Extern-USB-1
```

`usb-eject` temporarily stops udiskie, closes Samba connections to the selected
share, syncs writes, unmounts every partition of the physical device, removes
state only after successful unmount, powers the device off through UDisks, and
restarts udiskie. Verify with:

```bash
findmnt "/media/$T95_USER/<MOUNTNAME>"
sudo -u "$T95_USER" net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

After power-off the device should disappear from `lsblk`; reinserting it
creates its share again automatically.

## Restore configuration and keep secrets private

Before replacement, the script saves `/etc/samba/smb.conf.before-t95.<TIMESTAMP>`.
Restore a selected backup using `cp -a`, then `testparm -s` and restart `smbd`.
The module deliberately has no full uninstall for packages, Polkit rules, and
user files.

Never publish Samba passwords, `/var/lib/samba/private/passdb.tdb`,
`/etc/shadow`, private SSH keys, full system backups, local images, UART logs,
or personal configuration. Templates contain no Samba password; `smbpasswd`
sets it only on the T95.

## Further documentation

- [Complete technical setup](docs/SAMBA-USB-SETUP.en.md)
- [Restore checklist](docs/RESTORE-CHECKLIST.en.md)
- [Troubleshooting](docs/TROUBLESHOOTING.en.md)
- [GitHub publishing](docs/GITHUB-PUBLISH.en.md)
- [Changelog](CHANGELOG.en.md)

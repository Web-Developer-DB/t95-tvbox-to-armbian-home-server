# File sharing and USB drives on the T95

<a id="t95-samba--usb-automount"></a>

[Deutsch](README.md) | **English**

Share files with PCs, phones, and VLC on your home network. The module uses
regular Samba packages with a **custom project configuration tailored to
this TV box and its USB ports**, together with USB helpers. Once set up,
USB sticks, SSDs, external hard drives, and other USB storage with supported
filesystems are mounted automatically and made available as separate SMB
network shares. **Everyday use needs no manual mounting or share creation.**

The recommended fixed **`T95-DATA` share uses the system SD** at
`/srv/t95-sd-data/Share`, independently of the USB shares.
Internal eMMC is not formatted or configured.

[Set up](#set-up-file-sharing) · [Open files](#client-and-vlc-access) · [Eject USB](#safely-eject-usb-storage)

[Base installation](../../docs/INSTALLATION.en.md#7-set-up-file-sharing) · [Daily use](../../docs/DAILY_USE.en.md) · [Troubleshooting](../../docs/TROUBLESHOOTING.en.md)

## Requirements

- T95 runs from the verified SD and you are logged in over SSH as a normal user.
- [Kernel/DTB holds](../../docs/INSTALLATION.en.md#5-protect-the-kernel-and-dtb-before-updates) and a private SD backup are complete.
- Your T95 user can use `sudo`; installation requires internet access.
- USB disks have adequate external power when needed.

> [!WARNING]
> Existing Samba configuration is backed up and replaced. For a customized
> installation, read the [technical reference](docs/SAMBA-USB-SETUP.en.md) first.

<a id="quick-start-reproducible-restore"></a>

## Set up file sharing

Run installation commands **on the T95**, not the PC, in the same SSH window.
Install Git first if it is missing:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo apt update
sudo apt install -y git
```

### 1. Get the module and verify its manifest

**On the T95, normal SSH user; `sudo` where shown:**

```bash
git clone --branch main --depth 1 \
  https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git
cd t95-tvbox-to-armbian-home-server/server/samba-usb
sha256sum -c MANIFEST.sha256
```

**Success:** all check lines end with `OK`. Stop for any `FAILED` entry.
If the destination exists, inspect that checkout and its local changes rather
than overwriting it. The PC's release-tools folder is separate from current server modules.

### 2. Check your Linux user and network

**On the T95, normal SSH user; `sudo` where shown:**

```bash
export T95_USER="$(id -un)"
id "$T95_USER"
ip -brief address
```

**Success:** `id` shows your normal T95 user, not `root`. Note the IPv4 address
for file access from your PC.

### 3. Run installation

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo T95_USER="$T95_USER" DATA_PATH=/srv/t95-sd-data/Share \
  ./scripts/restore-samba-usb-setup.sh
```

`sudo` asks for your Linux password. If no Samba account exists, the script
then asks for a **Samba password** for file access. No characters appear while
typing. The passwords have different roles even if you choose the same text.

**Success:** setup finishes with `Fertig.`. In the **client PC file manager**,
open `smb://<SERVER-IP>/T95-DATA`; in Windows Explorer use
`\\<SERVER-IP>\T95-DATA`. Replace `<SERVER-IP>` with the box address;
this address is not a terminal command. Log in with your T95 username and
Samba password. Write and reopen a small test file; no USB drive is needed yet.

**File writes and reads work?** Continue with everyday controls below.
For errors, [check shares and authentication](../../docs/TROUBLESHOOTING.en.md#share-missing-or-access-denied).

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

An attached USB drive appears as a separate share. Close client files and
finish transfers before unplugging it. List USB shares first:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
T95_USER="$(id -un)"
sudo -u "$T95_USER" net usershare list
```

**Example response — read only:**

```text
SunDiskUSB
```

An empty list is normal without mounted USB storage. The fixed SD share
`T95-DATA` does not belong in this USB list. For a listed drive, start this prompt:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
read -r -p 'Share name of the USB drive to eject: ' T95_SHARE
```

Enter the actual name from your list and press Enter. Then eject
**that one drive**:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo usb-eject "$T95_SHARE"
```

**Success:** `USB-Datenträger kann entfernt werden.` or `Der Datenträger kann entfernt werden.`
means safe to unplug; the second message can follow unsupported USB power-off. For `DeviceBusy`, close
open files and playback; a terminal must not be inside the USB folder either.
Retry, or use [USB help](../../docs/TROUBLESHOOTING.en.md#usb-drive-missing-or-busy).

Check afterward:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo -u "$T95_USER" net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

The share is gone; after power-off the device should disappear from `lsblk`.
Reinsertion creates the share again.

<details>
<summary>What ejection does</summary>

`usb-eject` temporarily stops udiskie, closes connections to the selected share,
syncs writes, unmounts all partitions of that USB device, and powers it off.
State is removed only after successful unmount, then udiskie starts again.

</details>

## Undo setup

An earlier Samba configuration can be restored from its backup. The module
has no full uninstaller for all packages and user files. Instructions are
under “Technical details and restoration” below.

<details>
<summary>Technical details and restoration</summary>

All following shell commands run on the T95 as your normal SSH user; `sudo`
is shown where needed. Customization examples replace the recommended
installation command; they are not additional required steps.

## Result at a glance

The server root `smb://<SERVER-IP>/` displays both the fixed
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

### Customize setup

These alternatives replace the quick-start installation command. Use them
only to deliberately choose a different storage location or server name.

Set the username, server name, and fixed share path when running the script.
Replace `serveruser` with your ordinary Linux username. `DATA_PATH` selects
where the fixed `T95-DATA` share points:

**On the T95, normal SSH user; `sudo` where shown:**

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

For the recommended SD path, use the command in [Set up file sharing](#set-up-file-sharing).

Example: use eMMC already mounted at `/srv/T95-DATA`:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
findmnt /srv/T95-DATA
```

Continue only when the expected eMMC mount is shown. Then run:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
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

**On the T95, normal SSH user; `sudo` where shown:**

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

Use [safe USB ejection](#safely-eject-usb-storage) to select the actual drive.

## Verify after installation

**On the T95, normal SSH user; `sudo` where shown:**

```bash
T95_USER="$(id -un)"
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

**On the T95, normal SSH user; `sudo` where shown:**

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u "$T95_USER" net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 30
```

A labelled volume uses a sanitized label such as `SunDiskUSB`; unlabelled
media use `Extern-USB-1`, then `Extern-USB-2`, and so on. A published mount
point must not create a duplicate share.

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

</details>

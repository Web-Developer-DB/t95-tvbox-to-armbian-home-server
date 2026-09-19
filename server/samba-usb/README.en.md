# T95 Samba + USB automount

[Deutsch](README.md) | **English**

![Status: tested](https://img.shields.io/badge/Status-Samba%2FUSB%20tested-brightgreen)
![Platform: Armbian](https://img.shields.io/badge/Platform-Armbian%20%2F%20Debian-18a303)
![Protocol: SMB2%2FSMB3](https://img.shields.io/badge/Protocol-SMB2%20%2F%20SMB3-blue)
![Secrets: local](https://img.shields.io/badge/Secrets-never%20on%20GitHub-critical)

Reproducible Samba and USB configuration for a T95 running as an Armbian home
server. Run these instructions **on the running T95**, not on the PC used to
build or write the T95 image.

## Result at a glance

The server root `smb://<SERVER-IP>/` displays both the fixed internal
`T95-DATA` share and all currently attached USB/SSD shares. There is purposely
no static `[USB]` aggregate share: every volume retains its real capacity and
free-space information.

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

Run these commands **on the T95**. Replace `serveruser` with a real local Linux
user.

```bash
git clone https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git
cd t95-tvbox-to-armbian-home-server/server/samba-usb
sha256sum -c MANIFEST.sha256

export T95_USER=serveruser
id "$T95_USER"
ip -brief address

sudo T95_USER="$T95_USER" ./scripts/restore-samba-usb-setup.sh
```

The manifest check must complete without `FAILED`. The script installs Samba,
UDisks2, udiskie, Polkit, and exFAT/NTFS support. If needed, it asks
interactively for the Samba password of `T95_USER`.

Optional invocation values:

```bash
sudo T95_USER=serveruser \
  NETBIOS_NAME=T95-SERVER \
  DATA_PATH=/srv/T95-DATA/Share \
  ./scripts/restore-samba-usb-setup.sh
```

| Variable | Required | Default | Meaning |
| --- | :---: | --- | --- |
| `T95_USER` | **yes** | – | existing Linux and Samba user |
| `NETBIOS_NAME` | no | `T95-SERVER` | SMB network server name |
| `DATA_PATH` | no | `/srv/T95-DATA/Share` | fixed-share directory |

The derived mount base is `/media/<T95_USER>` and dynamic state lives below
`~/.local/state/t95-usb-shares`. Mount an eMMC `DATA_PATH` persistently first,
for example with `/etc/fstab`, and verify it with `findmnt`.

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

Expect valid `testparm` output, active `smbd`/where available `nmbd`, active
`udiskie.service`, and at least `T95-DATA` in the usershare list.

After inserting USB storage:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u "$T95_USER" net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 30
```

A labelled volume uses a sanitized label such as `SunDiskUSB`; unlabelled
media use `External-USB-1`, then `External-USB-2`, and so on. A published mount
point must not create a duplicate share.

## Client and VLC access

Use the server root first:

```text
smb://<SERVER-IP>/
```

Direct paths include `T95-DATA`, label-derived shares, or `External-USB-1`.
Linux file managers use `smb://<SERVER-IP>/`; Windows Explorer uses
`\\<SERVER-IP>\`; Android file managers add an SMB share; VLC opens the network
share and selects a compatible file. Use the Samba password of `T95_USER`; no
guest account or clear-text credentials are configured.

## Safely eject USB storage

Use the share name, never guess a `/dev/sdX` device:

```bash
sudo usb-eject SunDiskUSB
sudo usb-eject External-USB-1
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

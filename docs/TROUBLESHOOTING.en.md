<a id="installation-and-daily-use-troubleshooting"></a>

# 🛟 Installation and daily-use troubleshooting

[Deutsch](TROUBLESHOOTING.md) | **English**

Start with the visible symptom and simple checks. Change one thing at a time.
Stop using the T95 image for an unknown/different board:
[identify the hardware](HARDWARE_IDENTIFICATION.en.md).

[Installation](INSTALLATION.en.md) · [Everyday use](DAILY_USE.en.md) · [Home](../README.en.md)

> [!TIP]
> **Start with the problem you see.** Choose a symptom below and check simple causes first. Each section identifies whether to work on the PC or T95.

| Symptom | Start here |
| --- | --- |
| 🛠️ Missing command or failed download | [PC preparation](#missing-tool) |
| 💾 Card reader absent from the selection | [SD detection](#sd-card-not-detected) |
| 🌐 No router address for the box | [Network and boot](#no-ip-address) |
| 🔑 SSH timeout, rejection, or changed key | [SSH access](#ssh-login-fails) |
| 🔒 Unexpected kernel or missing holds | [Kernel state](#kernel-version-mismatch) |
| 📂 Missing share or rejected password | [Samba](#share-missing-or-access-denied) |
| 🔌 USB drive absent or busy | [USB](#usb-drive-missing-or-busy) |
| 🧩 Dashboard or Bluetooth problem | [Optional modules](#dashboard-or-bluetooth-fails) |

<a id="missing-tool"></a>

## 🛠️ Missing tool

**Linux PC · normal user with `sudo`.** For `Werkzeug fehlt: ...`, install the
[PC packages](INSTALLATION.en.md#1-prepare-the-hardware-and-pc).
`debugfs`/`e2fsck` come from `e2fsprogs`; `partprobe` comes from `parted`.
Run Bash blocks in Bash, not PowerShell.

For failed downloads, check Internet access and free space. Do not write an
image with a failed SHA-256 check. Rerun the recommended installer in the same
working directory: it verifies existing files, preserves invalid files under
different names, and downloads again. Do not bypass TLS errors with `curl -k`.

**Expected:** all tools exist and image verification passes. Resume the
installation path that stopped.

<a id="sd-card-not-detected"></a>

## 💾 SD card not detected

**On the Linux PC, normal user; `sudo` where shown:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
```

The installer accepts the whole USB device, such as `/dev/sdb`, with
`TRAN=usb`, `RM=1`, and `TYPE=disk`. A partition like `/dev/sdb1` is not the
target. `/dev/sdX` is a placeholder, not an actual device path.

1. Reconnect the reader and inspect the output again.
2. Try another USB port or USB card reader if available.
3. Internal readers using `/dev/mmcblk*` and readers showing `RM=0` are
   unsupported. Do not disable the safety checks.
4. In WSL2, the device must really appear in Linux. Use native Linux if
   passthrough is unreliable.

**Expected:** size and identity match the card. Reselect it in the installer;
device names can change whenever storage is reconnected.

<a id="no-ip-address"></a>

## 🌐 No IP address

**Location: box, router, and PC; no boot-system changes yet.**

1. Check the exact PCB, SD insertion while powered off, and successful writer completion.
2. Check Ethernet cable, router port, and the correct power supply. This path does not use Wi-Fi.
3. Find a new DHCP lease in the router. Guest-network or client isolation must not block PC-to-box access.
4. A black HDMI screen alone does not establish a boot failure.

On Ubuntu, you can also [search your home network for the T95](INSTALLATION.en.md#ubuntu-alternative-find-the-t95-on-your-home-network).
A missing scan entry alone does not establish a boot failure: network
isolation or selecting the wrong network range can hide the box.

**Expected:** return to [SSH login](INSTALLATION.en.md#4-first-ssh-login-and-normal-user)
with the address. If none appears, [diagnose boot over UART](BOOT_TROUBLESHOOTING.en.md)
after verifying the adapter and wiring using [UART setup](UART_BRINGUP.en.md).
Do not erase eMMC to repair booting.

<a id="ssh-login-fails"></a>

## 🔑 SSH login fails

**On the Linux PC, normal user; `sudo` where shown:**

```bash
read -r -p 'T95 IP address: ' T95_IP
```

Enter the router address and press Enter. Then connect:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
ssh -v "root@$T95_IP"
```

This diagnostic invocation is for the **initial** login. After first-run
setup, use your normal username instead of `root`.

| Message | Next check |
| --- | --- |
| `Connection timed out` / `No route to host` | Address, Ethernet, shared LAN, complete boot |
| `Connection refused` | Confirm this is the box's address. Initial boot generates SSH keys; for a persistent failure inspect the SSH service over UART |
| `Permission denied` | Initial login: personal-image root password. Later: normal Linux password. The unchanged public image has no password login |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Establish whether the box was reinstalled or another machine received the address; compare the new fingerprint through a trusted UART console |

Only after confirming a known reinstall and the new key, remove the old
entry on the **PC**:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
ssh-keygen -R "$T95_IP"
```

Reconnect and check the confirmed key. Do not disable SSH host-key checking.

**Expected:** login as the intended user and `sudo -v` work. Keep passwords,
private keys, and unredacted diagnostic output private.

<a id="kernel-version-mismatch"></a>

## 🔒 Kernel version mismatch

**On the T95, normal SSH user; `sudo` where shown:**

```bash
uname -r
apt-mark showhold
dpkg-query -W linux-image-current-sunxi64 linux-dtb-current-sunxi64
```

Expect `6.18.48-current-sunxi64` and both packages held. If only holds are
missing with the correct kernel, follow [step 5](INSTALLATION.en.md#5-protect-the-kernel-and-dtb-before-updates).
For a different kernel, stop updates and avoid arbitrary DTB changes.
[Restore a working SD backup](BACKUP.en.md#restore-a-card) or prepare a
separate card from the verified release. Preserve needed files beforehand.

<a id="share-missing-or-access-denied"></a>

## 📂 Share missing or access denied

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo testparm -s
systemctl --no-pager --full status smbd
findmnt -T /srv/t95-sd-data/Share
```

**Expected:** `[T95-DATA]` has your chosen path and `smbd` is active. For the
recommended setup, `findmnt` shows the SD system filesystem. For deliberate
eMMC use, check its actual path and mount instead. A share name does not
identify the underlying disk.

On the **client PC in its file manager**, open `smb://<T95-IP>/T95-DATA`, or
`\\<T95-IP>\T95-DATA` in Windows. Replace `<T95-IP>` with the router address.
Use the normal Linux username and its **Samba password**. Replace an incorrect
saved client password if necessary.

To set the Samba password again, run on the **T95 as the affected normal user**:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo smbpasswd -a "$(id -un)"
```

`net usershare list` shows **dynamic user shares only**, excluding fixed
`T95-DATA`. Empty output is normal without mounted USB storage. For USB
problems, continue below.

**Expected:** write and read a small file from the client. See
[Samba verification](../server/samba-usb/README.en.md#verify-after-installation)
for further checks. Reinstalling the module replaces its Samba configuration;
it is not the first diagnostic step.

<a id="usb-drive-missing-or-busy"></a>

## 🔌 USB drive missing or busy

**On the T95, normal SSH user; `sudo` where shown:**

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u "$(id -un)" net usershare list
sudo journalctl -t T95-USB-SHARE --no-pager -n 30
systemctl --user --no-pager --full status udiskie.service
```

A mounted drive should appear under `/media/<username>/...` with its own
share. Unlabelled shares are named `Extern-USB-1`, etc.; labelled drives use a
sanitized label. For missing hardware, check cables and power. USB disks may
need external power. Do not format existing data as a troubleshooting step.

To eject, select the actual share name from the list:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
read -r -p 'USB share name from the list: ' T95_SHARE
```

Enter the name of the drive you intend to unplug, then press Enter. Eject only that drive:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo usb-eject "$T95_SHARE"
```

For `DeviceBusy`, close client files and VLC playback; terminals must also
leave the USB directory. Retry ejection. Do not force unmount or unplug
during writes.

**Expected:** unplug only after successful ejection. Reinsertion creates the
share again. Further help: [Samba/USB troubleshooting](../server/samba-usb/docs/TROUBLESHOOTING.en.md).

<a id="dashboard-or-bluetooth-fails"></a>

## 🧩 Dashboard or Bluetooth fails

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-dashboard status
t95-bluetooth status
```

`command not found` means that helper is not installed. Local calls to
`server/setup/t95_setup.py` require a **`main` checkout**; the
PC's release-tag checkout does not contain the current modules. See
[local setup checkout](../server/setup/README.en.md#local-checkout).

A full [SD backup](BACKUP.en.md) is an optional recovery path. Instructions, removal, and audio diagnosis:
[dashboard](SSH_DASHBOARD.en.md), [Bluetooth](../server/bluetooth/README.en.md),
[music player](MUSIKPLAYER_CHEATSHEET.en.md).

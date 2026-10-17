# Install the home server

[Deutsch](INSTALLATION.md) | **English**

Follow this guide from a matching TV box to your first file transfer.
The steps explain terminal use and the connection to your box. Use the recommended installer; the
[manual alternative](#manual-alternative-for-sd-preparation) replaces only
step 2. Do not perform both paths in sequence.

**Route:** hardware → Linux PC → SD → SSH → kernel holds → backup → Samba.

[Home](../README.en.md) · [Troubleshooting by symptom](TROUBLESHOOTING.en.md)

## How to use the commands

Open **Terminal** from the Linux PC's application menu. A command is one line
you paste and run with **Enter**. You do not need to memorize it.

- **On the Linux PC** means your computer, including image preparation.
- **On the T95** means the SSH connection opened in step 4. SSH is remote
  access to the box; its commands run on the box even though the window is on the PC.
- **Normal user** means your personal account rather than `root`.
  `sudo` permits an administrative action and may ask for that user's password.
- Password entry shows no letters or stars. Type the password and press Enter.
- Run blocks in order. If a command asks a question, answer it before copying
  the next block. Text labelled **Expected** describes the response; do not type it.
- After an error, use the linked help before continuing. Keep related commands
  in the same window so selected addresses and paths remain available.

## 1. Prepare the hardware and PC

**Location: powered-off box and Linux PC; no writing yet.**

- Compare the exact PCB marking **`H616-T95MAX-AXP313A-V3.0`** with the
  [hardware photos](../README.en.md#hardware-photos). “T95” on the case is not
  enough. Stop for a different or unknown board and use the
  [developer porting path](PORTING.en.md).
- Prepare an expendable microSD, a **USB card reader**, Ethernet to your
  router, and the box's correct, reliable power supply. The writer requires
  `/dev/sdX`, `TRAN=usb`, `RM=1`, and `TYPE=disk`. Internal readers appearing
  as `/dev/mmcblk*` are unsupported.
- The card must exceed the raw image size, **1,535,115,264 bytes**, with
  additional space for packages and data. The reference used 128 GB; that is
  not a minimum. Allow **at least 6 GB free** on the PC for the download, raw
  image, personal copy, and temporary filesystem; `/tmp` also needs about
  1.6 GB free.
- **Backup space is additional:** reserve at least the entire SD card's size
  on another drive. A 128-GB card may require close to that amount of free
  backup space; the 6 GB above only covers image preparation.
- This server path uses **Ethernet and SSH**. Wi-Fi and an HDMI display are
  not verified prerequisites.

**On the Linux PC, normal user; `sudo` where shown:**

```bash
sudo apt update
sudo apt install -y bash git curl xz-utils coreutils util-linux e2fsprogs openssl parted udev sudo gawk openssh-client
df -h "$HOME" /tmp
```

`e2fsprogs` supplies `debugfs`/`e2fsck`; `parted` supplies `partprobe`.
Check the tools:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
for tool in bash git curl xz sha256sum lsblk dd debugfs e2fsck openssl partprobe udevadm sudo awk ssh scp; do
  command -v "$tool" || { printf "Missing: %s\n" "$tool"; break; }
done
```

**Expected:** every command resolves to a path and home/temp storage has
enough free space. For missing commands, [see help](TROUBLESHOOTING.en.md#missing-tool).

### Windows and WSL2

Native Linux is recommended. Windows requires an Ubuntu/Debian WSL2 shell
and reliable USB card-reader passthrough. `lsblk` must show `/dev/sdX`,
`TRAN=usb`, `RM=1`, and `TYPE=disk`; a Windows drive letter is insufficient.
Do not paste Bash blocks into PowerShell. If this mapping is unavailable,
perform SD preparation on native Linux. After writing SD, Windows can be an
SSH client. UART/FEL require their own serial/USB access; see
[UART setup](UART_BRINGUP.en.md). The PC scripts are not documented for macOS.

## 2. Create your personal SD card

> [!CAUTION]
> The selected USB medium is overwritten completely. Disconnect other USB
> storage where practical. Check size, model, and serial before confirming
> the exact device path.

**On the Linux PC, normal user; `sudo` where shown:**

```bash
mkdir -p "$HOME/t95-install"
cd "$HOME/t95-install"
export T95_WORKDIR="$PWD"
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/install-t95-release.sh)
```

The launcher is downloaded from `main`; it downloads base image **`v1.0.1`**
and explicitly obtains its image tools from **tag `v1.0.1`**. Optional server
modules are obtained separately from `main`; see [source versions](../README.en.md#source-versions).

The installer downloads/verifies the image, asks twice for your own **initial
root password** with hidden input, and creates a personal copy. Answer `Y` to
the SD-writing question, then enter the exact displayed device path. Without
confirmation, it only prepares the personal image file.

**Expected:** after writing, `ERFOLG: SD-Karte ist vorbereitet.` confirms that
the card was read back and checked. Remove it safely only afterward. On
failure, use [the matching troubleshooting entry](TROUBLESHOOTING.en.md).

On another run, reuse a matching personal copy or create a timestamped new
copy. Reusing a copy preserves its password; a new directory is unnecessary.

> [!IMPORTANT]
> The public image has **no default password** and password login is disabled
> before personalization. Do not flash the unchanged `.img.xz` with a generic
> flashing program. Keep personal `.img` and `.t95-provisioned-manifest` files private.

## 3. Boot the box and find its network address

**Location: powered-off T95 and router interface on the PC.**

1. Insert the verified SD while the T95 is fully powered off.
2. Connect Ethernet to the router, then power on.
3. Find the new DHCP address in the router's device list. DHCP means the
   router assigns an IP address automatically. PC and box must be in the same
   reachable LAN for the following access.

**Expected:** a network address for the box in the router. A TV display is not
an acceptance criterion. A guaranteed first-boot duration has not been
measured. If no address appears, [check cables, router, and SD](TROUBLESHOOTING.en.md#no-ip-address)
before escalating to UART diagnostics.

## 4. First SSH login and normal user

**On the Linux PC, normal user; `sudo` where shown:**

```bash
read -r -p 'T95 IP address: ' T95_IP
```

Enter the address from the router and press Enter. Then connect:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
ssh "root@$T95_IP"
```

SSH shows a new host-key fingerprint on first contact. This identifies the
box's key; it is not your password. Check the device in the router. An
independent comparison is possible from a trusted local UART console using
`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`. Accept the key only after
identifying the box. For a changed-key warning after an earlier login,
[see help](TROUBLESHOOTING.en.md#ssh-login-fails).

Use the root password chosen during step 2. Password entry shows no
characters. Finish Armbian's first-run dialog, including password changes
and creation of a normal user; retain that username privately.

**Expected:** a normal user with `sudo` exists. Exit the root session with
`exit` if necessary. If the dialog already ended the session, reconnect
directly. Run the next block on the PC:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
read -r -p 'T95 IP address: ' T95_IP
```

Answer with the box address and press Enter. Next ask for your new username:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
read -r -p 'Normal Linux user on the T95: ' T95_LOGIN
```

Enter the username created in the first-run dialog, then connect:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
ssh "$T95_LOGIN@$T95_IP"
```

**On the T95, normal SSH user; `sudo` where shown:**

```bash
whoami
sudo -v
```

`whoami` must show your normal username, not `root`. `sudo` requests that
user's Linux password. For problems, [check access](TROUBLESHOOTING.en.md#ssh-login-fails).

| Access | Password |
| --- | --- |
| Initial root login | Image-personalization password; a first-run password change supersedes it |
| SSH as normal user | That user's Linux password |
| `sudo` as normal user | The same Linux password |
| Samba file shares | Separate Samba password, set during Samba setup |

## 5. Protect the kernel and DTB before updates

> [!CAUTION]
> Do not run `apt upgrade`, `apt full-upgrade`, or `armbian-upgrade` first.
> The kernel and DTB hardware description must match the tested board.
> Replacing them can break booting or Ethernet.

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo apt-mark hold linux-image-current-sunxi64 linux-dtb-current-sunxi64
apt-mark showhold
uname -r
```

**Expected:** both package names appear and the kernel is
`6.18.48-current-sunxi64`. On a mismatch, [stop and check](TROUBLESHOOTING.en.md#kernel-version-mismatch).
Normal Debian/Armbian packages may then be updated. Deliberate kernel/DTB
updates require a backup and renewed hardware checks; see the
[release handbook](RELEASE.en.md).

## 6. Back up the base system

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo poweroff
```

After full shutdown, remove the card and create/verify a
[complete SD backup](BACKUP.en.md) on the Linux PC. This captures the working
base system before adding services and contains private credentials.

**Expected:** the backup and checksum are saved on another drive. Reinsert
the SD while the box is off, connect Ethernet, boot, and reconnect as the
normal SSH user from step 4.

## 7. Set up file sharing

**T95 · normal SSH user with `sudo`:** follow the
[File server setup](../server/samba-usb/README.en.md#quick-start-reproducible-restore).
It is the authoritative installation and client-test guide; commands are not
duplicated here.

The recommended invocation explicitly sets `DATA_PATH=/srv/t95-sd-data/Share`:
the fixed **`T95-DATA` share is on the system SD**. USB storage appears as
additional independent shares. The script does not partition or format eMMC.

**Expected:** the script prints `Fertig.`. On your PC, open
`smb://<T95-IP>/T95-DATA` in a file manager, authenticate with your normal
username and Samba password, and write/read a small test file. The address is
a file-manager location, not a terminal command. For problems,
[check shares and authentication](TROUBLESHOOTING.en.md#share-missing-or-access-denied).

## 8. Daily use and optional extensions

Use [everyday use](DAILY_USE.en.md) to reconnect, reboot, or shut down.

- [Eject USB safely](../server/samba-usb/README.en.md#safely-eject-usb-storage)
  before unplugging; reinsert and test access afterward.
- Make another [SD backup](BACKUP.en.md) after setup. SD backups exclude USB
  and eMMC data; back up those separately and regularly.
- Add the [dashboard](SSH_DASHBOARD.en.md) and
  [Bluetooth player](../server/bluetooth/README.en.md) after the base system.
  The project maintainer tested the documented steps on 2026-10-17 and
  confirmed they work.
- [eMMC data storage](TECHNICAL_REFERENCE.en.md#emmc-as-an-internal-data-drive)
  is a later extension requiring its own backup, partitioning, and mounting.

A complete run of this newly organized guide on a separate SD is still open.
Use the [acceptance checklist](VALIDATION.en.md#installation-guide-acceptance).

## Manual alternative for SD preparation

**Linux PC · normal user with `sudo` for writing.** This replaces **step 2
only**, for a new preparation. Do not repeat it after a successful installer
run. Step 1 hardware and PC requirements still apply.

### A. Download and verify the release

**On the Linux PC, normal user; `sudo` where shown:**

```bash
mkdir -p "$HOME/t95-install"
cd "$HOME/t95-install"
git clone --branch v1.0.1 --depth 1 \
  https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git t95-release-tools
curl -fL --retry 3 -O https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/download/v1.0.1/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
curl -fL --retry 3 -O https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/download/v1.0.1/SHA256SUMS
grep -F '  T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz' SHA256SUMS | sha256sum -c -
```

**Expected:** image verification prints `OK`. The checksum list also contains
developer files; this path checks only the downloaded image. If
`t95-release-tools` already exists, use the recommended installer or a new
working directory rather than overwriting it.

### B. Create a personal copy

In the same PC terminal:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
cd "$HOME/t95-install"
xz -dk --keep T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
mkdir -p t95-private
bash t95-release-tools/tools/provision-t95-release-image.sh \
  T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img \
  t95-private/t95-personal.img PROVISION-T95-ROOT-PASSWORD
```

**Expected:** after entering your password twice,
`ERFOLG: persönliche lokale Image-Kopie erzeugt.`. The fixed confirmation
token `PROVISION-T95-ROOT-PASSWORD` stays unchanged. For existing files, choose
new names or reuse them through the recommended installer; this manual path
does not overwrite a personal image.

### C. Select the card and write with verification

**On the Linux PC, normal user; `sudo` where shown:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
```

Check the whole card using the criteria from step 1. Then enter this prompt:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
read -r -p 'Verified SD device, e.g. /dev/sdb: ' T95_SD
```

Answer with your checked device path, press Enter, then run the writer:

**On the Linux PC, normal user; `sudo` where shown:**

```bash
bash "$HOME/t95-install/t95-release-tools/tools/write-t95-provisioned-image-to-sd.sh" \
  "$T95_SD" \
  "$HOME/t95-install/t95-private/t95-personal.img" \
  "$HOME/t95-install/t95-private/t95-personal.img.t95-provisioned-manifest" \
  WRITE-T95-PROVISIONED-TO-SDX
```

**Expected:** `ERFOLG: Personalisierte SD wurde vollständig zurückgelesen und geprüft.`
Keep `WRITE-T95-PROVISIONED-TO-SDX` unchanged; the prompted device path
identifies your card. Continue with [step 3](#3-boot-the-box-and-find-its-network-address).
This PC writing path does not access eMMC.

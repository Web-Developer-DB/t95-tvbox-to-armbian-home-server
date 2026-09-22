# Release guide: T95 H616 / AXP313A

[Deutsch](RELEASE.md) | **English**

Status: 2026-09-22. This **stable, hardware-specific** SD release is only for
`H616-T95MAX-AXP313A-V3.0`. It is not a universal T95 image and does not modify
Android eMMC. See [hardware photos](../README.en.md#hardware-photos).

## Release identity

| Property | Value |
|---|---|
| Release channel | `v1.0.1`, final hardware-specific release |
| System | Armbian 26.8.4 Trixie |
| Kernel | `6.18.48-current-sunxi64` |
| Boot medium | microSD; one ext4 partition at byte 4 MiB |
| Bootloader | signed T95 TOC0 loader at byte 8192 |
| DRAM / Ethernet | 2 GiB DDR3L, DCDC3 1.36 V / AC300 EPHY (`end0`, 100 Mbit/s) |
| eMMC in release path | no read or write access |

eMMC works as internal storage and may be mounted as an ext4 data drive, but
the Armbian eMMC installation/boot attempt did not succeed. microSD is the
documented supported boot path.

The hardened generic raw image is 1,535,115,264 bytes and has SHA-256
`849ec697bca90c07537b4b71bad350c9a05854ac8287fc960483d3bf0d0b7cf4`.
It contains no usable root password, SSH host keys, `authorized_keys`, user
directories, or `machine-id`.

Root is locked in the public download. A systemd dependency generates unique
host keys **before** `ssh.service`; Armbian's later host-key regeneration is
disabled so these keys remain in use.

`v1.0.1` keeps the AXP313A `dcdc3` regulator at 1.36 V in the Linux DTB. This
matches SPL DRAM initialization and was verified by complete cold boots on two
boxes with the exact PCB revision.

## Verified status and boundaries

UART verified TOC0 SPL, 2 GiB DRAM, AXP313/AC300 pre-initialization, ext4 boot,
kernel, systemd, `end0`, link, DHCP, and SSH. A RP2040-Zero 3.3 V TTL adapter
at 115200 baud/8N1 was used; see the
[UART adapter project](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter).

Offline hardening verified locked root, removed host-key files, absence of the
source root hash and three source private host-key payloads from the full raw
image, and readable ext4. The personalized SD passed microSD boot, clean
shutdown, SSH, and file-access testing. This does not guarantee other T95
revisions, long-term operation, Wi-Fi, audio, remote control, HDMI server use,
or kernel/bootloader updates.

## Create public release assets

Only package a hardened image audited against its private source artifact. All
commands operate on host files only and open no block device, FEL, or eMMC.

```bash
export REPO=/path/to/t95-h616-axp313a-project
export SOURCE_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"
export HARDENED_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-hardened-20260915-120000"
bash "$REPO/build/audit-t95-generic-release-image.sh" \
  "$HARDENED_ARTIFACT" "$SOURCE_ARTIFACT"
T95_RELEASE_ARTIFACT="$HARDENED_ARTIFACT" \
  bash "$REPO/build/create-t95-release-asset.sh" v1.0.1
```

The release directory contains exactly:

```text
T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
RELEASE-MANIFEST.txt
HARDENING-METADATA.txt
T95-H616-AXP313A-u-boot-sunxi-with-spl.bin
T95-H616-AXP313A-tanix-6.18.dtb
SHA256SUMS
```

```bash
cd "$REPO/release-assets/v1.0.1"
sha256sum -c SHA256SUMS
xz -t T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
```

## Local personalization and SD writing

The public image cannot be logged into directly. Personalize it locally outside
the repository. The tool asks twice, without echoing, for a non-empty password
and writes only its SHA-512 hash to the private image. Password and hash do not
appear in the shell command or manifest.

```bash
export DOWNLOAD=/path/to/GitHub-release-download
mkdir -p "$HOME/t95-private"
(cd "$DOWNLOAD" && sha256sum -c SHA256SUMS)
xz -dk --keep "$DOWNLOAD/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz"
bash "$REPO/tools/provision-t95-release-image.sh" \
  "$DOWNLOAD/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img" \
  "$HOME/t95-private/t95-personal.img" PROVISION-T95-ROOT-PASSWORD
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
bash "$REPO/tools/write-t95-provisioned-image-to-sd.sh" /dev/sdX \
  "$HOME/t95-private/t95-personal.img" \
  "$HOME/t95-private/t95-personal.img.t95-provisioned-manifest" \
  WRITE-T95-PROVISIONED-TO-SDX
```

`/dev/sdX` must be replaced after every insertion using `lsblk`. The writer
accepts only a removable USB SD card, verifies read-back hash, and opens neither
eMMC nor FEL. Never publish the personal image or manifest.

Insert the SD only while the T95 is powered off, connect Ethernet, boot, find
its DHCP address, verify the new SSH fingerprint, log in as `root` using the
local password, and complete Armbian first-run setup.

## Protect kernel and DTB

```bash
sudo apt-mark hold linux-image-current-sunxi64 linux-dtb-current-sunxi64
apt-mark showhold
uname -r
```

Before deliberate kernel/DTB changes, make a full backup, have UART ready,
remove holds, update, and retest cold boot, DTB, AC300, and networking:

```bash
sudo apt-mark unhold linux-image-current-sunxi64 linux-dtb-current-sunxi64
sudo apt update
sudo apt full-upgrade
```

The hold protects this verified state; it does not replace security assessment
or disable general Debian security updates.

## Rebuild boundary

The source uses U-Boot `v2024.04`/`25049ad560826f7dc1c4740883b0016014a59789`
and TF-A `v2.10`/`b6c0948400594e3cc4dbb5a4ef04b815d2675808`. The final TOC0
loader was signed by a private experimental key that is intentionally excluded;
the hash-backed release loader is authoritative. For source/build details see
[../build/README.en.md](../build/README.en.md). On failure, rebuild SD from the
verified asset and retain UART evidence privately; do not use eMMC as repair.

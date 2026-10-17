# T95 → Armbian home server v1.0.1

Stable, hardware-specific SD release for **`H616-T95MAX-AXP313A-V3.0`**,
Allwinner H616, 2 GiB DDR3L, Armbian 26.8.4 / Debian 13 Trixie /
`6.18.48-current-sunxi64`. Other boxes sold as “T95” are not automatically compatible.

> [!IMPORTANT]
> **Local personalization is mandatory before writing SD.** The public image
> has no default password: root is locked. Flashing the unchanged image does
> not provide password login. Use the installation guide below to create a
> private copy with your own password and write it with verification.

## Installation

**[→ Complete English installation guide](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/INSTALLATION.en.md)** ·
**[Deutsche Installationsanleitung](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/INSTALLATION.md)**

1. Check the exact PCB; prepare a Linux PC and USB card reader.
2. Use the installer to download/verify the release and create a personal
   image with your own initial root password.
3. Select the SD by size/model/serial. Writing erases the entire target card;
   the writer reads it back and verifies it.
4. Insert SD only while the T95 is off, connect Ethernet, boot, and locate its
   router DHCP address. Log in over SSH as root with the step-2 password;
   identify the box before accepting its host key.
5. Finish Armbian first-run setup, reconnect as a normal user, hold kernel/DTB
   packages before updates, and create a private SD backup.
6. Optionally install Samba and test file access. The recommended fixed
   storage path is explicitly on the system SD; USB shares are separate.

The guide uses the base image and image tools from `v1.0.1`. Dashboard and
Bluetooth are optional modules from `main`. The project maintainer tested
their documented steps on 2026-10-17 and confirmed they work.

## v1.0.1 change: DRAM stability

The Linux DTB keeps AXP313A `dcdc3` minimum/maximum at **1.36 V**, matching
SPL initialization and preventing the earlier reduction to 1.20 V during
kernel startup. Full cold boots to login passed on two boxes of the exact PCB revision.

## Verified behavior and limits

- SD boot, Ethernet/DHCP, SSH, clean shutdown, and file access passed on the
  target board. Samba/USB/VLC were separately verified on the reference setup.
- Image hardening was checked offline: no usable root password, no host keys,
  empty machine identity. Unique host keys are generated before SSH starts.
- **The SD installation route does not clean or overwrite Android eMMC.**
  Later data-drive use requires separate preparation. eMMC Armbian boot is
  not the supported path.
- Wi-Fi, HDMI as a server function, remote control, further stress testing,
  and long-term measurements are outside base acceptance.
  `clk_ignore_unused nohz=off` remains a diagnostic configuration.
- Deliberate kernel/bootloader updates require backup and renewed hardware checks.
- Full acceptance of the newly organized guide on a separate SD remains open
  and is distinct from existing hardware results.

[Troubleshooting](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/TROUBLESHOOTING.en.md) ·
[Test matrix](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/VALIDATION.en.md)

## Download files

The recommended installer downloads required files automatically. The manual
alternative only needs the image and its image checksum; the complete set
also includes developer/evidence files:

- `T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz`
- `SHA256SUMS`
- `RELEASE-MANIFEST.txt`
- `HARDENING-METADATA.txt`
- `T95-H616-AXP313A-u-boot-sunxi-with-spl.bin`
- `T95-H616-AXP313A-tanix-6.18.dtb`

Keep personal images, password data, SSH keys, and SD backups private.

# GitHub release `v1.0.1`

[Deutsch](GITHUB_RELEASE_NOTES.md) | **English**

## T95 H616 / AXP313A: hardened SD Armbian

This stable, hardware-specific SD release is for the exactly tested
`H616-T95MAX-AXP313A-V3.0` board. It boots from microSD and never reads or
writes Android eMMC.

U-Boot, 2 GiB RAM, AC300 Ethernet, DHCP, and SSH were verified on the target
board. Booting, clean shutdown, and file access also passed in practical use.
UART diagnostics used an external
[RP2040-Zero UART adapter](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
at 3.3 V TTL and 115200 baud/8N1.

### DRAM stability

The Linux DTB keeps the AXP313A `dcdc3` regulator at **1.36 V** for both its
minimum and maximum. It matches SPL initialization and prevents Linux from
lowering the DRAM rail later. Complete cold boots to login were verified on two
`H616-T95MAX-AXP313A-V3.0` T95 boxes.

### Security changes

The public download contains **no default password** and **no SSH host keys**:

- Root is locked in the generic image.
- Before writing SD, create a private local copy with your own password.
- The T95 creates its own host keys at its first SSH start, before
  `ssh.service` accepts connections.
- The previous root hash and the three private source host-key payloads were
  checked against the complete hardened raw image and were not found.

### Installation

1. Download all six assets and run `sha256sum -c SHA256SUMS`.
2. Extract the image, personalize it outside the repository using
   `tools/provision-t95-release-image.sh`, and retain the resulting private
   manifest.
3. Use only `tools/write-t95-provisioned-image-to-sd.sh` with a removable
   `/dev/sdX` freshly verified with `lsblk`.
4. Insert the card only while the box is powered off, connect Ethernet before
   booting, determine the DHCP address, and verify the new SSH fingerprint.
5. Log in as `root` with the locally chosen password and complete Armbian
   first-run setup.

Full guide: [RELEASE.en.md](RELEASE.en.md).

### Important limitations

- Only this board revision is supported. Other “T95” boxes can use different
  SoCs, RAM, PMICs, or network hardware.
- `clk_ignore_unused nohz=off` remains a diagnostic configuration.
- Wi-Fi, audio, remote control, additional USB/SMB stress testing, and
  long-term operation are outside the stability commitment. Basic
  Samba/USB/VLC functionality was tested separately on the T95.
- Update kernel and bootloader only after a backup and renewed UART/network
  validation.
- The asset build was hardened offline; the stable state refers to the tested
  board and documented personalized SD installation.

### Assets

- `T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz`
- `RELEASE-MANIFEST.txt`
- `HARDENING-METADATA.txt`
- `T95-H616-AXP313A-u-boot-sunxi-with-spl.bin`
- `T95-H616-AXP313A-tanix-6.18.dtb`
- `SHA256SUMS`

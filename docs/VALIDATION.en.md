# Public test matrix: stable tested T95 state

[Deutsch](VALIDATION.md) | **English**

The final asset channel is `v1.0.0`. Historical experimental assets are kept
in the private laboratory collection and are not promoted as final downloads.

This summary contains generic results only. Raw UART logs, local IP and MAC
addresses, router data, SD backups, and Android forensics stay outside the
public repository.

## Hardware and boot path

| Test | Result | Meaning |
|---|---|---|
| Board match | passed | `H616-T95MAX-AXP313A-V3.0` |
| FEL detection | passed | SoC identified as Allwinner H616 |
| TOC0 from microSD | passed | custom loader starts autonomously from SD |
| DRAM | passed | U-Boot reports 2048 MiB |
| AXP313/AC300 | passed | EPHY responds; reset and pre-initialization successful |
| Ext4 boot script | passed | kernel and initramfs loaded from SD |
| Linux userspace | passed | systemd and multi-user target reached |
| End-user boot | passed | T95 starts from powered-off state using microSD |
| Clean shutdown | passed | system shuts down cleanly and restarts |
| File access | passed | files reachable through configured server path |
| Ethernet | passed | `end0`, 100 Mbit/s full duplex |
| DHCP and SSH | passed | lease and Armbian first-run setup on source image |
| Samba `T95-DATA` | passed | authenticated SMB2/SMB3 share on T95 |
| USB automount/usershares | passed | dynamic shares, safe eject, re-insertion |
| VLC over SMB | passed | local network playback tested |
| eMMC as ext4 data drive | passed | internal storage usable as data medium |
| Armbian boot from eMMC | failed | SD remains the verified boot path |
| Android eMMC | unchanged | no read/write operation in release path |

UART capture used an external
[RP2040-Zero UART adapter project](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
at 3.3 V TTL and 115200 baud/8N1.

## Hardening the public image

| Offline check | Result |
|---|---|
| Root account | locked; no published initial hash |
| SSH host keys | absent from the image |
| SSH startup order | key generation before `ssh.service` |
| Armbian first run | later host-key regeneration disabled |
| Source root hash | absent from complete raw image |
| Three source host-key payloads | absent from complete raw image |
| `machine-id` | empty |
| Ext4 | `e2fsck -fn` passed |

The result is a generic image that cannot be logged into directly. A local
password hash is inserted before writing; that resulting copy is not a release
asset.

## Release files

| File | SHA-256 |
|---|---|
| hardened raw image, extracted | `e2c1fad50f6bc138332de8ef944b9e83462a882414cc736e9537450de759df4c` |
| T95 TOC0 loader | `6c408cc237f7e7514ed4307f087f9305f3447f70f9893ae52e1f290f6613ed6a` |
| T95/Tanix 6.18 DTB | `ab5021cbbdc5df0eb96021ec014fa86bf8d93cc5b4e7f197ab8bb2031d7f6131` |
| Armbian source image, XZ | `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` |

The loader was compared at byte 8192 with the separate loader file. The
release asset was compressed with `xz --check=sha256`; its six files are
verified through `SHA256SUMS`.

## Optional future work

- Additional USB/SMB stress testing, cold boots, and long-term stability.
- Wi-Fi, HDMI, audio, and remote control.
- A permanent replacement for `clk_ignore_unused nohz=off`.
- Kernel or bootloader updates.

The documented baseline may be described as a **stable tested home-server
release** for the verified board. The open items are extensions, not known bugs
in the accepted functional scope.

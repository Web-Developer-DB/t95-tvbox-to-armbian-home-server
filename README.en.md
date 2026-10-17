# T95 TV box → Armbian home server

[Deutsch](README.md) | **English**

Reuse a T95 with **Allwinner H616 and PCB `H616-T95MAX-AXP313A-V3.0`** as a
small file/media server. Armbian boots from microSD, Ethernet connects it to
your home network, and SSH provides administration. Optional Samba shares
serve files to PCs, Android, and VLC.

![Base release: hardware tested](https://img.shields.io/badge/Base_release-hardware_tested-brightgreen)
![System: Armbian 26.8.4](https://img.shields.io/badge/Armbian-26.8.4-18a303)
![Boot: microSD](https://img.shields.io/badge/Boot-microSD-blue)

> [!WARNING]
> **Check the PCB first.** “T95” covers different hardware. Only
> `H616-T95MAX-AXP313A-V3.0` is tested for this image. Stop for a different or
> unknown board: [identify hardware](docs/HARDWARE_IDENTIFICATION.en.md) and
> use the [developer path](docs/PORTING.en.md).

## Install the home server

**[→ Open the complete installation guide](docs/INSTALLATION.en.md)**

The recommended route assumes basic terminal/SSH knowledge and a Linux PC
with a USB card reader. It covers requirements, download, verification, your
own local password, SD writing, first login, and file sharing.

**Check hardware → prepare PC → create SD → SSH → hold kernel → backup
→ Samba → verify file access**

> [!IMPORTANT]
> The download has **no default password**. Create a personal copy with your
> own password before writing. The guide handles this with the verified
> installer. Writing erases the selected SD completely; the internal Android
> eMMC is not written by this route.

**Already installed?** [Troubleshooting](docs/TROUBLESHOOTING.en.md) ·
[Samba and USB](server/samba-usb/README.en.md) · [SD backup](docs/BACKUP.en.md)

## Hardware photos

Compare the **PCB marking**, not just the case. On the connector side it is
immediately above the heatsink. The AI-assisted orientation
view marks its location; use the unchanged original photos below as the
authoritative source for hardware comparison. Disconnect all power before opening the box.

![AI-assisted orientation view of PCB inscription H616-T95MAX-AXP313A-V3.0](docs/images/t95-board-identification.png)

<p>
  <a href="docs/images/t95-board-connectors.jpg"><img src="docs/images/t95-board-connectors.jpg" alt="Original connector side of the tested PCB" width="320"></a>
  <a href="docs/images/t95-board-memory.jpg"><img src="docs/images/t95-board-memory.jpg" alt="Original memory side of the PCB" width="240"></a>
</p>
<p>
  <a href="docs/images/t95-box-top.jpg"><img src="docs/images/t95-box-top.jpg" alt="T95 case from above" width="200"></a>
  <a href="docs/images/t95-case-bottom-redacted.jpg"><img src="docs/images/t95-case-bottom-redacted.jpg" alt="Case underside with individual sticker covered" width="200"></a>
</p>

Click original photos to enlarge. They do not replace hardware inspection.
EXIF/GPS data was removed and individual stickers are covered.

## What works?

| Function | Documented status |
| --- | --- |
| Armbian SD boot, Ethernet, DHCP, SSH, clean shutdown | Tested on the exact PCB |
| Samba shares, USB automount/eject, VLC over SMB | Tested on the reference installation; separate setup |
| eMMC as a data drive | Tested on the reference installation; separate preparation required |
| Armbian boot from eMMC | Unsuccessful; microSD remains the supported boot path |
| SSH dashboard: setup and display | Tested and confirmed working by the project maintainer (2026-10-17) |
| Bluetooth player: setup and operation | Tested and confirmed working by the project maintainer (2026-10-17) |
| Wi-Fi, HDMI as a server function, remote control, further long-term tests | Outside base acceptance |

The base is Armbian **26.8.4 / Debian 13 Trixie / kernel
`6.18.48-current-sunxi64`**. The guide protects kernel and DTB from
uncontrolled replacement after first login. Ethernet is limited to 100 Mbit/s;
the reference measured approximately 11–12 MB/s payload throughput.

[Test evidence and remaining individual checks](docs/VALIDATION.en.md) ·
[Hardware details, measurements, SSH example](docs/TECHNICAL_REFERENCE.en.md)

## Optional extensions

After the working base system and a private SD backup:

| Goal | Guide |
| --- | --- |
| Share home-network files and USB drives | [Samba module](server/samba-usb/README.en.md) |
| Show system information on SSH login | [Dashboard](docs/SSH_DASHBOARD.en.md) |
| Send music to Bluetooth headphones | [Bluetooth and music player](server/bluetooth/README.en.md) |
| Set up both optional modules through a menu | [Shared setup entry](server/setup/README.en.md) |
| Later use eMMC as a data drive | [Requirements and reference](docs/TECHNICAL_REFERENCE.en.md#emmc-as-an-internal-data-drive) |

## Source versions

| Component | Source |
| --- | --- |
| Base image | [Release `v1.0.1`](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/tag/v1.0.1) |
| SD preparation launcher | `main`; explicitly obtains image tools from tag `v1.0.1` |
| Documentation and optional server modules | `main` |
| Local server-module checkout on the T95 | `main`; see [setup guide](server/setup/README.en.md#local-checkout) |

The base image is a release asset. A Git checkout contains tools and docs.
The PC's release-tools folder is not a checkout of the current server modules.
Each guide owns its installation commands; do not mix files from different
source versions.

## Documentation and developer path

| Task | Start here |
| --- | --- |
| Set up a new box | [Installation](docs/INSTALLATION.en.md) |
| Resolve a visible error | [Troubleshooting](docs/TROUBLESHOOTING.en.md) |
| Back up or restore the system | [SD backup](docs/BACKUP.en.md) |
| Understand hardware and changes | [Technical reference](docs/TECHNICAL_REFERENCE.en.md), [Armbian changes](docs/CHANGES_FROM_ARMBIAN.en.md) |
| Inspect release layout or deliberate kernel updates | [Release handbook](docs/RELEASE.en.md) |
| Investigate another H616 board | [Porting](docs/PORTING.en.md), [UART](docs/UART_BRINGUP.en.md), [boot diagnostics](docs/BOOT_TROUBLESHOOTING.en.md) |
| Build or publish an image | [Build chain](build/README.en.md), [publishing](docs/PUBLISHING.en.md), [release text](docs/GITHUB_RELEASE_NOTES.en.md) |

UART is the diagnostic path for porting and early boot failures. Prepare a
**3.3 V TTL adapter** before those tasks; never connect 5 V TTL or RS-232.
Hardware details and wiring belong to the developer path.

## Project and boundaries

This private project began with an Android installation classified or
suspected as BadBox-affected. The SD conversion does not use Android as its
operating system or trust source. It does not automatically clean or remove
Android eMMC.

Keep personal images, backups, credentials, and raw diagnostic captures
private. An SD backup excludes separate USB/eMMC data. A full base-installation
run on a separate SD is tracked in the
[acceptance checklist](docs/VALIDATION.en.md#installation-guide-acceptance).
The confirmed dashboard/Bluetooth steps are documented separately there.

## License

No repository license has been selected yet. Before redistribution, review
the project license and adopted upstream licenses. Existing Armbian license
notices remain in place.

<details>
<summary>Earlier section links</summary>

<a id="uart-before-porting"></a><a id="uart-diagnostics-with-rp2040-zero"></a><a id="developer-build-and-porting"></a>

[Porting / UART](docs/PORTING.en.md)

<a id="end-user-quick-start"></a><a id="one-script-installation"></a><a id="required-after-the-first-ssh-login-hold-the-kernel-and-dtb"></a><a id="manual-installation"></a>

[Installation](docs/INSTALLATION.en.md)

<a id="optional-next-step-samba-file-server-and-usb-automount"></a><a id="samba-and-usb-file-server"></a>

[Samba / USB](server/samba-usb/README.en.md)

<a id="requirements"></a>

[Developer reference](build/README.en.md)

<a id="armbian-baseline-and-t95-changes"></a><a id="verified-status"></a><a id="emmc-as-an-internal-data-drive"></a>

[Technical reference](docs/TECHNICAL_REFERENCE.en.md)

<a id="security-backups-and-updates"></a>

[Backup](docs/BACKUP.en.md)

</details>

<a id="public-test-matrix-stable-tested-t95-state"></a>

# ✅ Public test matrix: stable tested T95 state

[Deutsch](VALIDATION.md) | **English**

The final asset channel is `v1.0.1`. Historical experimental assets are kept
in the private laboratory collection and are not promoted as final downloads.

This summary contains generic results only. Raw UART logs, local IP and MAC
addresses, router data, SD backups, and Android forensics stay outside the
public repository.

> [!NOTE]
> **Reading the results:** “passed” applies to the stated hardware and scope. Open fresh-installation and individual checks remain listed below; they are not implied to have passed.

<a id="hardware-and-boot-path"></a>

## 🔎 Hardware and boot path

| Test | Result | Meaning |
|---|---|---|
| Board match | passed | `H616-T95MAX-AXP313A-V3.0` |
| FEL detection | passed | SoC identified as Allwinner H616 |
| TOC0 from microSD | passed | custom loader starts autonomously from SD |
| DRAM | passed | U-Boot reports 2048 MiB |
| DRAM voltage in Linux DTB | passed | AXP313A DCDC3 minimum/maximum are both 1,360,000 µV |
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

<a id="hardening-the-public-image"></a>

## 🔒 Hardening the public image

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

<a id="release-files"></a>

## 📦 Release files

| File | SHA-256 |
|---|---|
| hardened raw image, extracted | `849ec697bca90c07537b4b71bad350c9a05854ac8287fc960483d3bf0d0b7cf4` |
| T95 TOC0 loader | `6c408cc237f7e7514ed4307f087f9305f3447f70f9893ae52e1f290f6613ed6a` |
| T95/Tanix 6.18 DTB | `b4b0b19d8287663f79efc59e50fc0a7408f7a5a0900d2cc162bfb8a72834857e` |
| Armbian source image, XZ | `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` |

The loader was compared at byte 8192 with the separate loader file. The
release asset was compressed with `xz --check=sha256`; its six files are
verified through `SHA256SUMS`.

<a id="dashboard-and-bluetooth"></a>

## 🧩 Dashboard and Bluetooth

**Verified and tested, confirmed on 2026-10-17.** The project maintainer
personally tested the documented Bluetooth and dashboard steps and confirmed
they work. This feedback supplements automated setup tests and earlier
reference-installation evidence.

| Check | Result | Evidence |
| --- | --- | --- |
| Documented dashboard steps | passed | Project maintainer's confirmation on 2026-10-17 |
| Documented Bluetooth steps | passed | Project maintainer's confirmation on 2026-10-17 |
| Setup installation, removal, and failures in a test environment | passed | 37 automated tests with simulated APT/systemd/BlueZ; updated 2026-10-19 |

**2026-10-19 — changed audio rollback:** configuration archives are now created
before APT; existing legacy MPD configuration and recorded service states are
restored. Automated fixtures cover these changes and failure/retry paths. The
2026-10-17 hardware confirmation applies to the earlier setup behavior, not this
new rollback. Its dedicated hardware run remains open.

**2026-10-19 — dashboard USB quick help:** the setup installer replaces rotating
Armbian tips in `/etc/update-motd.d/35-armbian-tips` with fixed USB help. Historical
archive files remain as a reference. With `usb-eject` available, the existing
Tips section shows status/eject commands, share-name selection,
whole-drive scope and the required success message before unplugging. It does
not execute these commands. Five additional setup tests cover both languages,
line width, absent tools, upgrading existing installs without APT, backups,
rollback and manual changes. This addition is not yet accepted on the T95.

The [Samba/USB audit](SAMBA_USB_AUDIT.en.md) separately records confirmed error
paths and filesystem limits; general USB acceptance is not a per-filesystem or
all-error-cases certification.

The following individual checks have no separate confirmation yet:

- [ ] Full installation and removal on a separate, freshly prepared SD followed by cold boot.
- [ ] Combined installation of both modules through menu option `0` on that separate SD.
- [ ] With headphones absent, verify in practice that MPD does not fall back to another audio output.

Preserve the working production SD as recovery for these checks. The feedback
does not specify a replacement SD or these individual checks, so they are
tracked separately from the confirmed steps.

## 🔌 New Samba/USB implementation — 2026-10-19

| Check | Status |
| --- | --- |
| 73 Samba/USB tests with simulated system effects | Passed; includes missing mount directories and historical status operations |
| 37 setup tests including dashboard USB help | Passed |
| udev rule syntax | Passed |
| Package manifests: 25 Samba + 14 dashboard entries | Passed |
| All eight audit findings addressed in code | Covered by automated tests |
| Update of an existing T95 setup at `aef4e9f` | Confirmed on hardware; see partial acceptance below |
| Existing fixed shares and Samba configuration after update | Unchanged; file comparison reported no differences |
| Already mounted exFAT drive after update | Share detected; read/write permission checks passed |
| exFAT eject with power-off and resumption after failure | Confirmed on T95 at `52b6be1`; LED off, operation `powered-off` |
| exFAT after reconnection | New diskseq, no inherited guard, automatically mounted and shared |
| exFAT: actual Samba read/write access | Confirmed by the maintainer; separate content/checksum comparison not recorded |
| Filesystem matrix, 20 ext4 cycles and multiple devices | Pending |

**Partial acceptance on 2026-10-19, revision `aef4e9f`:** The maintainer ran
the update on the existing T95 installation and provided terminal output.
All 25 module checksums matched; a private configuration backup was created
and `--update` completed with `Fertig. Bestehende Samba-Konfiguration erhalten.`
The subsequent comparison with the restored previous configuration reported
no differences, preserving both existing fixed shares (SD/home directory and
eMMC). The automounter and user service reported `active`. An already mounted
exFAT drive appeared as a usershare; status checks confirmed read/write
permissions for the configured user.

This feedback does not confirm a new USB attachment sequence or actual file
or SMB client access. Authentication with the existing Samba password,
content verification, eject, reconnection and multiple-device operation still
require separate checks. Internal SD/eMMC and ZRAM devices were correctly
reported as outside the USB manager's scope.

**Subsequent exFAT eject at `aef4e9f`: failed.** The supplied terminal output
reports `Path is not a directory` for a remaining usershare definition after
eject started. Retrying without an open Samba window produced the same error.
Status stopped before showing devices and operation history. This feedback
alone does not establish permission to unplug.

The failure was reproduced with removed mount directories and a Samba CLI
simulation. The correction reads checked stored share definitions independently
of target directory existence and continues device/operation diagnostics when
definitions fail validation. Fifteen additional tests cover cleanup, resuming
after update reconciliation, multiple partitions, neighbour drives, all four
intended filesystems, power-off and file/directory security checks. All 70
module tests and 32 setup tests passed for this correction.

**Hardware retry on 2026-10-19, revision `52b6be1`: passed for the tested exFAT
stick.** Another `--update` checked all 25 module files, created a private backup
and reported preserved Samba configuration. Eject resumed using the original
share name and completed with `USB-Datenträger kann entfernt werden.` Status
reported `powered-off`, no remaining USB share and an active automounter.
The maintainer confirmed that the LED went off. After unplugging/reconnecting,
diskseq changed from 13 to 18; the eject guard was off, exFAT was mounted again
and its usershare restored. Actual Samba reading and writing were then
explicitly confirmed. No separate content/checksum comparison was provided.

The old operation remained visible in status after reconnection. Status now
shows diskseq and distinguishes current from previous attachments, covered by
three additional tests. The display change itself is only automatically tested.
This exFAT test does not accept ext4/FAT32/NTFS, 20 ext4 cycles, Btrfs or
multiple-device operation.

Earlier USB reference acceptance applies to the earlier scripts. It does not
confirm the new implementation. [Audit and limits](SAMBA_USB_AUDIT.en.md) ·
[Hardware checklist](../server/samba-usb/docs/RESTORE-CHECKLIST.en.md).

<a id="optional-future-work"></a>

## 🔭 Optional future work

- Additional USB/SMB stress testing, cold boots, and long-term stability.
- Wi-Fi, HDMI, other audio outputs, and infrared remote control.
- A permanent replacement for `clk_ignore_unused nohz=off`.
- Kernel or bootloader updates.

The documented baseline may be described as a **stable tested home-server
release** for the verified board. The open items are extensions, not known bugs
in the accepted functional scope.

<a id="installation-guide-acceptance"></a>

## ✅ Installation guide acceptance

**2026-10-17 status: open.** The reorganized guide received editorial/static
checks; a full run of this exact user path on a separate SD is outstanding.
Existing hardware results and the confirmed dashboard/Bluetooth steps are separate.

**Documentation checks on 2026-10-17:**

| Check | Result |
| --- | --- |
| Relative links, images, language links in all 65 Markdown documents | passed; existing anchors in the edited documents preserved |
| Executable Bash examples and the 21 shell scripts | 338 example blocks and 21 scripts pass `bash -n` |
| Existing setup tests | 16 passed; simulated APT/systemd/BlueZ |
| Samba/dashboard manifests | all 34 entries match; changed documentation hashes refreshed |
| Backup examples taken directly from both guides | 22 checks passed in temporary directories |
| Local Markdown preview at 1280 px and 390 px viewport width | both languages checked; quick navigation visible without scrolling; separate adjacent hardware/kernel alerts; original photo 320 px; no page overflow |

The backup checks cover portable checksum creation, unchanged/moved archives,
legacy absolute-path manifests after moving, and a damaged selected copy while
the original still exists. Missing/empty/invalid checksums, missing archives,
invalid zstd data, and a different subsequently selected path are rejected.
The write block was tested only for refusal after failed checks; privileged
commands were stubbed. No real disk, formatting, installation, or development-PC
service operations were performed. The corrected compression option is `zstd --check`.

These are documentation and test-environment results. The maintainer's earlier
hardware confirmation for dashboard/Bluetooth remains recorded separately above.
A complete run on a separate SD remains open.

The added Ubuntu network-discovery guide was checked for command options,
Bash syntax, links, and layout; no real home-network scan was performed.

A reviewer with basic terminal/SSH skills should follow
[installation](INSTALLATION.en.md) without extra verbal instructions. Preserve
the working production card as recovery.

- [ ] Record exact PCB, date, reviewer, and image version.
- [ ] Prepare the Linux PC; identify source versions and SD target without help.
- [ ] Complete download/checks, password personalization, and verified SD writing.
- [ ] Cold boot, locate router address, log in as root, and finish Armbian first-run setup.
- [ ] Reconnect as normal user; check sudo, kernel version, and both holds.
- [ ] Optional backup path: create the base-system backup and verify archive/checksum.
- [ ] Install Samba with explicit SD storage; test the fixed share without USB.
- [ ] Write/read a client test file; identify the Samba password correctly.
- [ ] Attach USB, check its dynamic share, eject safely, reinsert, and access again.
- [ ] Shut down cleanly, cold boot, and recheck SSH/file access.
- [ ] Optional backup path: back up the configured SD; separately verify restoring a replacement and booting it.
- [ ] Optional player: follow the new first-file guide, check SCP to the configured music folder, headphone output, pause, and stop.

Record actual card/client types, outcome, and deviations without private
credentials. Leave unchecked items open; hashes and syntax checks do not count
as hardware acceptance. Confirmed dashboard/Bluetooth steps and their remaining
individual checks are recorded under [Dashboard and Bluetooth](#dashboard-and-bluetooth).
[Setup verification](../server/setup/README.en.md#verify-before-publishing)
describes the automated checks.

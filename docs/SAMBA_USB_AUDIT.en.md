<a id="sambausb-audit-2026-10-19"></a>

# 🔎 Samba/USB audit, 2026-10-19

[Deutsch](SAMBA_USB_AUDIT.md) | **English**

Reviewed repository revision `4f97a5d`: Samba installation, udiskie configuration,
event hook, safe eject, and audio rollback. Source inspection and isolated
simulations do not replace tests with physical storage.

> [!IMPORTANT]
> **Fix status, 2026-10-19:** all eight findings are addressed in code and covered
> by automated tests. Eject is now per-drive; udiskie keeps running.
> **Hardware acceptance has started; the full run remains pending.** An existing
> setup update and exFAT status are partially confirmed. The originally reported
> intermittent ext4 issue is not yet proven fixed on physical hardware.
> The subsequent exFAT eject exposed an additional missing-mount-directory bug.
> At `52b6be1`, corrected eject/power-off, reconnection and actual Samba
> read/write access are confirmed for the exFAT stick.

[Set up Samba](../server/samba-usb/README.en.md) · [Troubleshooting](TROUBLESHOOTING.en.md#usb-drive-missing-or-busy)

<a id="separate-the-failure-layers"></a>

## 🧭 Separate the failure layers

| Observation | Investigate first |
| --- | --- |
| Device absent from `lsblk` | USB/block-device detection, cable, power, kernel, previous power-off |
| Device present, no mount | udiskie/UDisks, kernel driver, filesystem state, mount error |
| Mounted, no share | Event hook, group membership, configuration, usershare creation |
| Share present, writes fail | Samba credentials and actual Unix/filesystem permissions |

In the accompanying diagnosis, `ntfs3` rejected a dirty NTFS volume while a
second exFAT volume was mounted. This does not establish the cause of the
separately reported ext4 case, nor explain how the NTFS dirty state originated.
The [kernel documentation](https://docs.kernel.org/filesystems/ntfs3.html) advises
against forcing NTFS mounts. Repairs require a separate decision, a backup,
and an unambiguously identified volume.

<a id="open-sambausb-findings"></a>

## 🛠️ Samba/USB findings and fix status

| Original finding | Code correction | Automated | Hardware |
| --- | --- | --- | --- |
| Every power-off error treated as unsupported | Distinguish errors; per-drive guard and final checks | Passed | Pending |
| Enumeration failure lost | Structured inventory; errors/empty inventory prevent unsafe steps | Passed | Pending |
| Automounter restart error hidden | No automounter stop/start during eject; other drives keep working | Passed | Pending |
| Concurrent share names collide | Short common lock, reserved names and atomic JSON state | Passed | Pending |
| YAML overrides project JSON | Explicit service config path; existing files backed up | Passed | Pending |
| Repeated setup retains old running config | Deliberate restart and reconciliation of existing mounts | Passed | Partial: update, active service and exFAT share confirmed |
| Samba error prevents state fallback | Explicit error handling; only validated current mappings accepted | Passed | Pending |
| Btrfs source suffix is unsuitable as a device | Resolve block source without FSROOT suffix; handle anonymous Btrfs/FUSE mount numbers | Passed | Pending |

Additional coverage includes all partitions/shares of a physical drive,
interruption/resumption, reused names, foreign mounts and sibling drives.
Share names remain reserved during eject. Repeated events do not rewrite
unchanged mappings to SD.

Implementation: [shared core](../server/samba-usb/lib/t95_usb.py),
[installer](../server/samba-usb/lib/t95_install.py),
[udev rule](../server/samba-usb/config/udev/99-t95-usb-eject.rules), and
[regression tests](../server/samba-usb/tests/test_usb.py).
Existing shell entry points remain available.

The [udiskie 2.5.7 source](https://github.com/coldfix/udiskie/tree/v2.5.7) documents
the underlying config selection and device hints. The new per-drive guard still
needs practical acceptance on the T95.

<a id="filesystem-boundaries"></a>

## 💾 Filesystem boundaries

| Type | Assessment |
| --- | --- |
| ext4 | No explicit hook rejection. Stored UID/GID, modes, and ACLs still apply; share ACLs do not override Unix permissions. The reported intermittent mount failure remains open without its own logs. |
| exFAT / FAT | Driver and volume state govern mounting. Ownership/mask options differ from ext4; filename and file-size limits still apply. |
| NTFS | UDisks may select `ntfs3` even with `ntfs-3g` installed. Dirty or unclean volumes must not be handled by a blanket force-mount fallback. |
| Btrfs subvolumes | Block sources and anonymous mount device numbers are handled for one physical drive; hardware acceptance remains pending. |
| LUKS, LVM, RAID, other paths | The hook rejects `/dev/mapper/*` and `/dev/dm-*`. Unlocking, mapper resolution, and complex disk topologies are outside the promised scope. |

UDisks documents its [filesystem-specific mount options](https://storaged.org/udisks/docs/mount_options.html).
Samba explains that [Unix permissions limit share permissions](https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html).
Automatic ownership changes or recursive `chmod` are not a general solution.

<a id="audio-rollback-corrected-separately"></a>

## 🎧 Audio rollback: corrected separately

Old removal ignored individual service errors and intentionally disabled the
player rather than restoring every previous service state. Globally enabled
user units can also start after local disabling; see
[systemd documentation](https://www.freedesktop.org/software/systemd/man/256/systemctl.html).

The revised [audio setup](../server/bluetooth/README.en.md) backs up configuration
before APT and restores the recorded service baseline. A previously active
`mpris-proxy` may be active again under this explicitly selected rollback mode.
This differs from removing preexisting audio packages too. A new hardware test
of this changed rollback remains outstanding.

<a id="method-and-limits"></a>

## 🧪 Method and limits

**Baseline audit at `4f97a5d`, before the fixes:** the following records describe the original inspection. Current regression results are listed separately below.

- All three Samba shell scripts pass `bash -n`; udiskie JSON parses correctly.
- All 20 Samba and 14 dashboard checksums matched at the audited baseline.
- The existing 16 setup tests passed; they cover dashboard/Bluetooth rather
  than real Samba access or a filesystem matrix.
- Thirteen isolated audit cases confirmed normal/busy eject, repeated events,
  and modeled failure paths. A successful defect reproduction establishes
  the defect; it does not mean the USB bug has been fixed.
- Real `findmnt` output from a temporary mountinfo file confirmed the Btrfs
  source suffix without mounting a partition.
- These simulations performed no formatting, repair, package installation,
  or actual service changes on the development PC or T95.

Hardware acceptance still needs client read/write checks per filesystem,
multiple partitions, simultaneous events, eject with files open, unsupported
power-off, reboot, and reinsertion.

<a id="new-usb-implementation-acceptance"></a>

## ✅ New USB implementation acceptance

- **73 automated module tests pass:** shares/eject, parsers and update/rollback fixtures, including 15 cases following the hardware finding and three tests for historical attachment status. All 37 setup tests, including the new dashboard USB hint, also pass.
- **udev rule syntax verified**; guard verification completed during the confirmed exFAT eject. Other persistence/multiple-device cases remain pending.
- **Simulations modify no physical storage or services.** They use temporary directories and system doubles.
- **Partial T95 acceptance at `aef4e9f`:** an existing setup was updated successfully; a private backup was created, Samba configuration including custom fixed shares remained unchanged, the automounter was active and an existing exFAT share was detected with positive user permission checks. Evidence: maintainer-provided terminal output dated 2026-10-19; no file/SMB access or eject confirmed yet. [Details and limits](VALIDATION.en.md#-new-sambausb-implementation--2026-10-19).
- **Subsequent eject at `aef4e9f` failed:** `net usershare info` refuses the query if it cannot open the share path as a directory. This blocked cleanup and status; retrying without an open Samba window failed too. The previous dictionary-only share simulation did not model this Samba check. New file-backed CLI fixtures reproduce the failure with a removed mount directory.
- **Correction of this additional finding:** read owner/format-checked usershare definitions independently of target existence; confirm new shares individually through Samba; retain device/operation diagnostics when definition validation fails and still return failure for incomplete status. No replacement directories or blanket ignoring of query failures. Resumption after update reconciliation passes automated tests and is confirmed by the exFAT hardware retry below. The underlying path check is in the [Samba parser](https://github.com/samba-team/samba/blob/samba-4.22.4/source3/param/loadparm.c), used by info/list in the [usershare command](https://github.com/samba-team/samba/blob/samba-4.22.4/source3/utils/net_usershare.c).
- **Hardware retry passed at `52b6be1`:** exFAT eject resumed after update, the share was cleaned up and power-off confirmed (`powered-off`, LED off). udiskie remained active. Reconnection gave a new diskseq without a guard and restored the share. The maintainer confirmed Samba reading/writing; a separate content comparison is missing. Status now labels historical operations using diskseq.
- **Hardware pending:** content comparison for the exFAT stick; client read/write and eject for ext4, FAT32 and NTFS; Btrfs subvolumes; 20 ext4 reconnect/eject cycles; multiple devices on both ports and with a hub; unsupported power-off and additional interruption cases.

The [acceptance checklist](../server/samba-usb/docs/RESTORE-CHECKLIST.en.md)
tracks these cases separately. Mark hardware cases passed only after executing
them. [Update guide](../server/samba-usb/README.en.md#update-an-existing-setup).

<a id="-open-sambausb-findings"></a>

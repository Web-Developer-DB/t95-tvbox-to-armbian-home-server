<a id="sambausb-audit-2026-10-19"></a>

# 🔎 Samba/USB audit, 2026-10-19

[Deutsch](SAMBA_USB_AUDIT.md) | **English**

Reviewed repository revision `4f97a5d`: Samba installation, udiskie configuration,
event hook, safe eject, and audio rollback. Source inspection and isolated
simulations do not replace tests with physical storage.

> [!IMPORTANT]
> **Result:** the normal path is understandable, but errors and concurrent
> events are not fully handled. A promise of support for every filesystem
> would not be justified. These Samba findings remain open; this audit does
> not modify the USB scripts.

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

## 🛠️ Open Samba/USB findings

| Priority | Finding | Impact and proposed correction |
| --- | --- | --- |
| High | `usb-eject` treats every power-off failure as unsupported power-off | Restarting udiskie may remount the still-attached volume after the script says it is safe to unplug. Distinguish errors, verify final mounts, and prevent remount until removal. |
| High | Device-enumeration failure disappears inside process substitution | If partition enumeration fails, the loop can be empty, yet shares/state are removed and a success message may follow. Check output and exit status first. |
| High | Automounter restart errors are hidden by `|| true` | Successful exit can leave udiskie stopped, preventing later automounts. Check restart outcome and report failure. |
| Medium | Share-name allocation and state updates lack a common lock | Simultaneous mount events can select the same free name, after which `net usershare add` replaces a mapping. Serialize allocation, publication, and state writing. |
| Medium | udiskie starts without an explicit configuration file | An existing `config.yml` takes precedence over the installed `config.json`, changing automount and hook behavior. Select the project config explicitly and back up existing settings. |
| Medium | `enable --now` does not reload an already running udiskie process | Repeating setup can retain the old process/configuration. Restart deliberately and reconcile existing mounts. |
| Medium | Failed Samba query prevents the intended state fallback | `set -e` with `pipefail` aborts `MOUNTPOINT=...` before fallback. Handle query failure explicitly; distinguish this from a successful empty result. |
| Medium | Btrfs subvolume source is passed as a block-device name | A source such as `/dev/sda1[/@]` is unsuitable for `lsblk`. Use `--nofsroot` or another unambiguous device identity. |

Affected locations:

- [usb-eject](../server/samba-usb/scripts/usb-eject): Samba query 46–50,
  source selection 87–102, restart 125–130, enumeration 144–161, power-off 181–194.
- [t95-usb-share](../server/samba-usb/scripts/t95-usb-share): allocation 122–157;
  cleanup and state updates have no shared lock.
- [udiskie service](../server/samba-usb/config/systemd-user/udiskie.service):
  launch without `--config`.
- [Samba installer](../server/samba-usb/scripts/restore-samba-usb-setup.sh):
  configuration copy followed by `enable --now` only.

The [udiskie 2.5.7 source](https://github.com/coldfix/udiskie/tree/v2.5.7) confirms
YAML precedence, asynchronous hooks, and startup mounting of available media.
The remount simulation models that behavior. Frequency on the T95 was not measured.

<a id="filesystem-boundaries"></a>

## 💾 Filesystem boundaries

| Type | Assessment |
| --- | --- |
| ext4 | No explicit hook rejection. Stored UID/GID, modes, and ACLs still apply; share ACLs do not override Unix permissions. The reported intermittent mount failure remains open without its own logs. |
| exFAT / FAT | Driver and volume state govern mounting. Ownership/mask options differ from ext4; filename and file-size limits still apply. |
| NTFS | UDisks may select `ntfs3` even with `ntfs-3g` installed. Dirty or unclean volumes must not be handled by a blanket force-mount fallback. |
| Btrfs subvolumes | Mounting may work while the current eject source handling fails. |
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

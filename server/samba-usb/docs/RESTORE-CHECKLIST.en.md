# ✅ Hardware acceptance: new Samba/USB implementation

[Deutsch](RESTORE-CHECKLIST.md) | **English**

**Partial acceptance started:** this checklist is for the implementation updated 2026-10-19.
Earlier hardware acceptance does not complete these checks. Use spare media
with backed-up data. No formatting or repair is part of the acceptance run.

**Confirmed at `aef4e9f` on 2026-10-19:** update of the existing T95 setup,
unchanged Samba configuration including custom fixed shares, active
automounter and detection of an already mounted exFAT share with positive
read/write permission checks. The feedback does not yet confirm actual file/SMB
access or eject. [Evidence and limits](../../../docs/VALIDATION.en.md#-new-sambausb-implementation--2026-10-19).

**Subsequent eject failed:** at `aef4e9f`, a share path no longer accessible as
a directory blocked cleanup and status. Retrying without an open Samba window
also failed. The correction is covered by file-backed Samba fixtures.

**Retry at `52b6be1`: passed.** The failed exFAT eject resumed and completed
with `powered-off`, removed share and LED off; udiskie remained active.
Reconnection confirmed a new diskseq, no inherited guard, mount and share.
Actual Samba reading/writing was also confirmed. A separate content comparison
is not yet recorded.

| Filesystem | Client read/write with content verification | Eject and reconnect | Result |
| --- | --- | --- | --- |
| ext4 | ☐ | ☐ 20 cycles | Not tested |
| exFAT | Read/write confirmed; content comparison pending | ✅ | Partial acceptance at `52b6be1` |
| FAT32 | ☐ | ☐ | Not tested |
| NTFS | ☐ | ☐ | Not tested |
| Single-drive Btrfs with subvolumes | ☐ | ☐ | Not tested |

## 🧪 Required scenarios

- [ ] Fresh setup; password prompt and `T95-DATA` read/write without USB.
- [x] Update an existing setup; backup created and Samba configuration including custom fixed shares unchanged.
- [x] Already mounted exFAT share detected after update; automounter active and user permission checks passed.
- [x] Actual Samba reading and writing confirmed for the tested exFAT stick.
- [x] Failed exFAT eject resumed after update; share removed and power-off confirmed by LED off.
- [x] Reconnected exFAT automatically mounted/shared; new diskseq without inherited guard.
- [ ] Separately confirm the existing Samba password and content comparison.
- [ ] Existing YAML configuration; confirm the explicit project JSON is selected.
- [ ] Drive A ejects while B stays readable/writable and newly attached C is mounted/shared.
- [ ] Repeat on both built-in ports and with a powered USB hub.
- [ ] Multiple partitions: all shares closed and mounts removed on the selected drive.
- [ ] Unsupported power-off: guarded unmount permits unplugging; other drives keep working.
- [ ] Busy/open file: failure reported without an unsafe-unplug message; retry works.
- [ ] Interrupted eject and udiskie restart: target remains guarded; other devices still mount.
- [ ] Replug and reboot: no obsolete guard or conflicting usershare names.
- [ ] Permission-limited ext4 and read-only media: clear diagnosis, unchanged ownership/data.
- [ ] Check kernel/UDisks logs for I/O, disconnect and filesystem errors.

Record date, revision, hardware, filesystem/driver, outcome and error details in
[validation](../../../docs/VALIDATION.en.md). Keep personal logs private.
[User guide](../README.en.md) · [Technical reference](SAMBA-USB-SETUP.en.md)

<!-- Compatibility anchors for older documentation links. -->
<a id="-check-manual-restoration"></a>
<a id="-prepare"></a>
<a id="-restore-checklist"></a>
<a id="check-manual-restoration"></a>
<a id="prepare"></a>
<a id="restore-checklist"></a>

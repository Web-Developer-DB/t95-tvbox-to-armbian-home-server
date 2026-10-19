# ✅ Hardware acceptance: new Samba/USB implementation

[Deutsch](RESTORE-CHECKLIST.md) | **English**

**Pending:** this checklist is for the implementation updated 2026-10-19.
Earlier hardware acceptance does not complete these checks. Use spare media
with backed-up data. No formatting or repair is part of the acceptance run.

| Filesystem | Client read/write with content verification | Eject and reconnect | Result |
| --- | --- | --- | --- |
| ext4 | ☐ | ☐ 20 cycles | Not tested |
| exFAT | ☐ | ☐ | Not tested |
| FAT32 | ☐ | ☐ | Not tested |
| NTFS | ☐ | ☐ | Not tested |
| Single-drive Btrfs with subvolumes | ☐ | ☐ | Not tested |

## 🧪 Required scenarios

- [ ] Fresh setup; password prompt and `T95-DATA` read/write without USB.
- [ ] Update an existing setup; compare Samba configuration and passwords before/after.
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

# Changelog

## 2026-10-20

- USB status focuses on connected USB drives; internal SD/eMMC and ZRAM devices no longer appear as unmanaged.
- Hide operations from earlier connections and powered-off devices; keep current eject failures and USB validation/mount warnings visible. Stored operations are not deleted.
- Explicitly report an empty USB overview. Six additional regression tests; all 79 module tests pass.

## 2026-10-19

- Hardware confirmation at `52b6be1`: exFAT eject/power-off, reconnection and Samba read/write access. Historical eject operations now show diskseq and are distinguished from the current attachment; 73 module tests pass.
- Corrected the exFAT eject hardware finding: share definitions remain readable after the mount directory disappears; cleanup/resumption do not require an existing share target.
- Newly created shares are confirmed individually by Samba. Malformed definitions no longer hide device/operation diagnostics; incomplete status still returns failure.
- Regression tests model Samba definition files and disappearing mount directories; the first correction passed 70 tests; see the later hardware confirmation above.
- Shared Python core for device identity, atomic mappings and locked share-name allocation.
- Per-attachment udev guards replace stopping the automounter during eject.
- Whole-drive eject covers all partitions, Btrfs/FUSE sources, sibling protection and resumable failures.
- Private configuration backups and checked rollback; `--update` preserves Samba settings/passwords.
- Read-only `usb-eject --status`; automated regression tests and separate pending hardware checklist.

[Deutsch](CHANGELOG.md) | **English**

## 2026-09-16

- Reworked integrated home-server README with installation, verification,
  client, VLC, and rollback guidance.
- Documented eMMC as internal ext4 data drive and clarified unsuccessful eMMC
  boot attempt.
- Added confirmed Samba/USB/VLC acceptance status to the main README.
- Updated publishing notes to the actual module path.
- Set `smb://SERVER-IP/` as preferred client entry point.
- Removed static `[USB]` aggregate share and added a dynamic Samba usershare
  for every USB/SSD filesystem.
- Labelled media use sanitized label names; unlabelled media use
  `External-USB-1`, `External-USB-2`, and so on; name collisions use `-2`,
  `-3`, and so on.
- Integrated `t95-usb-share` through the udiskie event hook and state mappings
  under `~/.local/state/t95-usb-shares/`.
- Fixed duplicate-event shares, unsuitable usershare existence testing, and
  accidental overwriting of the shell `PATH` variable.
- Extended safe eject with temporary udiskie stop/start, `smbcontrol smbd
  close-share`, and deletion of share/state only after successful unmount.
- Full test passed: share removed, mount gone, `/dev/sdX` absent from `lsblk`
  after power-off, and reinsertion recreated the share automatically.

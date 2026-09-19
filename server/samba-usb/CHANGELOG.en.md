# Changelog

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

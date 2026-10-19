# 🔎 Samba/USB troubleshooting

[Deutsch](TROUBLESHOOTING.md) | **English**

Identify the failing layer first. This guide assumes the [current project
installation](../README.en.md).

| Observation | Next check |
| --- | --- |
| Device absent from `lsblk` | Cable, USB port, power and kernel messages. |
| Device present, no mount | udiskie/kernel logs, filesystem state and eject guard. |
| Mounted, no share | Event hook and Samba settings. |
| Readable share, writes fail | Samba account and actual permissions; ext4 retains UID/GID/ACLs. |
| Eject failed | Do not unplug; inspect status/mounts and retry. |
| `Path is not a directory` after eject | Update the older implementation; a removed mount directory could block share cleanup. See below. |

## 📋 Collect status

**On the T95, normal SSH user; these commands do not change settings:**

```bash
sudo usb-eject --status
lsblk -o NAME,TYPE,SIZE,FSTYPE,TRAN,MOUNTPOINTS
net usershare list
systemctl --user status udiskie.service --no-pager -l
sudo journalctl -t T95-USB-SHARE -b --no-pager -n 60
sudo journalctl -b -u udisks2.service --no-pager -n 60
sudo journalctl -k -b --no-pager -n 80
```

If the user journal is unavailable, query the system journal using your actual UID:

**On the T95, normal SSH user:**

```bash
sudo journalctl -b "_UID=$(id -u)" --no-pager -n 80
```

Logs can contain serials, UUIDs and usernames; inspect them before public sharing.
Empty usershare output is normal without mounted USB storage. Fixed `T95-DATA`
is not listed there.

## 💾 Filesystems and permissions

- ext4: mounting and write permission are separate. Inspect rights deliberately; do not recursively replace ownership indiscriminately.
- NTFS: dirty state, hibernation or Fast Startup can prevent mounting. Back up data and plan an appropriate repair separately. The script does not force a mount.
- Read-only media remain read-only. Status checks access as the actual Samba user.
- If the device is absent from `lsblk`, the share hook cannot process it yet. This differs from a missing SMB share.

## ⏏️ Eject remains incomplete

Close open files, VLC and terminals working inside the drive. Select its actual
share name:

**On the T95, normal SSH user:**

```bash
read -r -p 'Share name of the affected USB drive: ' T95_SHARE
```

Enter its name and press Enter. Then in the same T95 terminal:

```bash
sudo usb-eject "$T95_SHARE"
```

`failed` may mean partial completion. The guard applies only to that drive;
other storage continues automounting. Do not stop the entire automounter or
manually delete guard files. After a successful eject, unplug/reconnect to use
the drive again. Rebooting also clears runtime guards.

### 🛠️ `Path is not a directory` after unmount

During the T95 test of revision `aef4e9f`, Samba could no longer open the share
path as a directory after exFAT eject started. The `net usershare info` query
validates that directory, blocking outstanding share cleanup. The old status command also
stopped there. An open Samba window alone does not explain this failure.

The correction reads stored usershare definitions with directory, owner, file
type, size and format checks; missing mount directories no longer prevent
cleanup. Device identity and mount boundaries are still checked independently.
Samba still confirms newly created shares individually.

Update the repository copy and run
[update mode](../README.en.md#update-an-existing-setup), keeping the drive
connected. Then run `sudo usb-eject --status` and retry eject using the original
share name. The root-protected operation journal permits resumption even if the
update reconciliation has already removed the stale share.
Do not create empty replacement mount directories or delete guard files.
Permission to unplug requires a successful completion of the new eject attempt.

## 🔄 Setup or update fails

`--update` preserves Samba configuration. For missing settings, inspect the
reported values; do not use a full fresh setup as the first troubleshooting
step. If the user manager does not yet know `sambashare`, reboot the box in a
controlled manner and repeat setup.

Private backups and `state.json` are at `/var/lib/t95-samba/installation-…/`.
`rolled-back` confirms verified restoration. `rollback-failed` requires inspecting
the given backup and error message. Keep backups private.

<!-- Compatibility anchors for older documentation links. -->
<a id="-command-not-found-for-rmloggerheadsync-in-a-script"></a>
<a id="-device-remounts-immediately-after-unmount"></a>
<a id="-devicebusy-during-eject"></a>
<a id="-duplicate-extern-usb-n-share"></a>
<a id="-troubleshooting"></a>
<a id="-usb-mounts-but-no-samba-share-appears"></a>
<a id="-verify-a-successful-eject"></a>
<a id="command-not-found-for-rmloggerheadsync-in-a-script"></a>
<a id="device-remounts-immediately-after-unmount"></a>
<a id="devicebusy-during-eject"></a>
<a id="duplicate-extern-usb-n-share"></a>
<a id="troubleshooting"></a>
<a id="usb-mounts-but-no-samba-share-appears"></a>
<a id="verify-a-successful-eject"></a>

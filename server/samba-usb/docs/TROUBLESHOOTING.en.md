<a id="troubleshooting"></a>

# 🛟 Troubleshooting

[Deutsch](TROUBLESHOOTING.md) | **English**

> [!NOTE]
> **Technical diagnosis on the T95.** Beginners should start with [simple USB help](../../../docs/TROUBLESHOOTING.en.md#usb-drive-missing-or-busy). These examples need your actual user, device, mount, and share names; hook tests change usershares.

| Your symptom | Start here |
| --- | --- |
| 📂 USB mounted, share absent | [Check events and service](#usb-mounts-but-no-samba-share-appears) |
| 🔁 Duplicate share | [Compare mount points](#duplicate-extern-usb-n-share) |
| 🛠️ Script commands missing | [Check PATH](#command-not-found-for-rmloggerheadsync-in-a-script) |
| 🔒 Drive busy | [Investigate DeviceBusy](#devicebusy-during-eject) |
| 🔌 Drive remounts immediately | [Check udiskie during eject](#device-remounts-immediately-after-unmount) |
| ✅ Confirm eject | [Check mount, share, and device](#verify-a-successful-eject) |

Commands use anonymized `$T95_USER` and `$T95_UID`; set them before testing:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

<a id="usb-mounts-but-no-samba-share-appears"></a>

## 📂 USB mounts but no Samba share appears

```bash
sudo -u $T95_USER net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 50
sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  journalctl --user -u udiskie.service --no-pager -n 100
sudo -u $T95_USER /usr/local/bin/t95-usb-share \
  device_mounted /dev/sda1 /media/$T95_USER/NAME LABEL UUID
```

<a id="duplicate-extern-usb-n-share"></a>

## 🔁 Duplicate `Extern-USB-N` share

```bash
for s in $(sudo -u $T95_USER net usershare list); do
  sudo -u $T95_USER net usershare info "$s"
done
```

The reference `t95-usb-share` is idempotent and must not publish one mount
point twice.

<a id="command-not-found-for-rmloggerheadsync-in-a-script"></a>

## 🛠️ `command not found` for rm/logger/head/sync in a script

Check whether the shell `PATH` variable was overwritten:

```bash
grep -n '\bPATH\b' /usr/local/bin/t95-usb-share
grep -n '\bPATH\b' /usr/local/bin/usb-eject
```

`PATH` is only the command search path. Use names such as `SAVED_PATH` for file
paths.

<a id="devicebusy-during-eject"></a>

## 🔒 `DeviceBusy` during eject

```bash
fuser -vm /media/$T95_USER/MOUNTNAME
smbstatus --shares
sudo smbcontrol smbd close-share SHARENAME
```

The reference `usb-eject` performs the close-share step automatically.

<a id="device-remounts-immediately-after-unmount"></a>

## 🔌 Device remounts immediately after unmount

udiskie must not run while unmount/power-off occurs. The reference script stops
the user service temporarily and starts it again afterward.

<a id="verify-a-successful-eject"></a>

## ✅ Verify a successful eject

```bash
findmnt /media/$T95_USER/MOUNTNAME
sudo -u $T95_USER net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

After successful `udisksctl power-off`, physical `/dev/sdX` should disappear
from `lsblk`.

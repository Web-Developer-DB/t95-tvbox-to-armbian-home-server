# Troubleshooting

[Deutsch](TROUBLESHOOTING.md) | **English**

Commands use anonymized `$T95_USER` and `$T95_UID`; set them before testing:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

## USB mounts but no Samba share appears

```bash
sudo -u $T95_USER net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 50
sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  journalctl --user -u udiskie.service --no-pager -n 100
sudo -u $T95_USER /usr/local/bin/t95-usb-share \
  device_mounted /dev/sda1 /media/$T95_USER/NAME LABEL UUID
```

## Duplicate `External-USB-N` share

```bash
for s in $(sudo -u $T95_USER net usershare list); do
  sudo -u $T95_USER net usershare info "$s"
done
```

The reference `t95-usb-share` is idempotent and must not publish one mount
point twice.

## `command not found` for rm/logger/head/sync in a script

Check whether the shell `PATH` variable was overwritten:

```bash
grep -n '\bPATH\b' /usr/local/bin/t95-usb-share
grep -n '\bPATH\b' /usr/local/bin/usb-eject
```

`PATH` is only the command search path. Use names such as `SAVED_PATH` for file
paths.

## `DeviceBusy` during eject

```bash
fuser -vm /media/$T95_USER/MOUNTNAME
smbstatus --shares
sudo smbcontrol smbd close-share SHARENAME
```

The reference `usb-eject` performs the close-share step automatically.

## Device remounts immediately after unmount

udiskie must not run while unmount/power-off occurs. The reference script stops
the user service temporarily and starts it again afterward.

## Verify a successful eject

```bash
findmnt /media/$T95_USER/MOUNTNAME
sudo -u $T95_USER net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

After successful `udisksctl power-off`, physical `/dev/sdX` should disappear
from `lsblk`.

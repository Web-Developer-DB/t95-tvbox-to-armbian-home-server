# Troubleshooting

Die Befehle verwenden die anonymisierten Shell-Variablen `$T95_USER` und
`$T95_UID`. Vor dem Test setzen:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

## USB wird gemountet, aber keine Samba-Freigabe erscheint

```bash
sudo -u $T95_USER net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 50
sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  journalctl --user -u udiskie.service --no-pager -n 100
```

Manueller Hook-Test:

```bash
sudo -u $T95_USER /usr/local/bin/t95-usb-share \
  device_mounted /dev/sda1 /media/$T95_USER/NAME LABEL UUID
```

## Doppelte `Extern-USB-N`-Freigabe

Prüfen, ob mehrere Shares auf denselben Pfad zeigen:

```bash
for s in $(sudo -u $T95_USER net usershare list); do
  sudo -u $T95_USER net usershare info "$s"
done
```

Die Referenzversion von `t95-usb-share` ist idempotent und darf denselben Mountpunkt nicht doppelt veröffentlichen.

## `command not found` für rm/logger/head/sync innerhalb eines Skripts

Prüfen, ob die Shell-Systemvariable `PATH` überschrieben wurde:

```bash
grep -n '\bPATH\b' /usr/local/bin/t95-usb-share
grep -n '\bPATH\b' /usr/local/bin/usb-eject
```

`PATH` darf nur der Kommando-Suchpfad sein. Für Dateipfade Namen wie `SAVED_PATH` verwenden.

## `DeviceBusy` beim Auswerfen

```bash
fuser -vm /media/$T95_USER/MOUNTNAME
smbstatus --shares
```

Wenn `smbd` den Mount hält:

```bash
sudo smbcontrol smbd close-share SHARENAME
```

Die Referenzversion von `usb-eject` führt diesen Schritt automatisch aus.

## Gerät wird direkt nach Unmount wieder gemountet

`udiskie` darf während der Unmount/Power-Off-Sequenz nicht weiterlaufen. Die Referenzversion von `usb-eject` stoppt den User-Service temporär und startet ihn anschließend wieder.

## Auswurf erfolgreich prüfen

```bash
findmnt /media/$T95_USER/MOUNTNAME
sudo -u $T95_USER net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

Nach erfolgreichem `udisksctl power-off` sollte das physische `/dev/sdX` aus `lsblk` verschwinden.

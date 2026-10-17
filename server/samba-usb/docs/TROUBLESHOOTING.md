<a id="troubleshooting"></a>

# 🛟 Troubleshooting

**Deutsch** | [English](TROUBLESHOOTING.en.md)

> [!NOTE]
> **Technische Diagnose auf der T95.** Beginne als Einsteiger mit der [einfachen USB-Fehlerhilfe](../../../docs/TROUBLESHOOTING.md#usb-laufwerk-fehlt-oder-ist-belegt). Die Beispiele hier erfordern den tatsächlichen Benutzer sowie passende Geräte-, Mount- und Freigabenamen; Hook-Tests verändern Usershares.

| Dein Symptom | Hier beginnen |
| --- | --- |
| 📂 USB gemountet, Freigabe fehlt | [Event und Dienst prüfen](#usb-wird-gemountet-aber-keine-samba-freigabe-erscheint) |
| 🔁 Doppelte Freigabe | [Mountpunkte vergleichen](#doppelte-extern-usb-n-freigabe) |
| 🛠️ Befehle im Skript fehlen | [PATH prüfen](#command-not-found-für-rmloggerheadsync-innerhalb-eines-skripts) |
| 🔒 Laufwerk belegt | [DeviceBusy untersuchen](#devicebusy-beim-auswerfen) |
| 🔌 Laufwerk kommt sofort zurück | [udiskie beim Auswurf prüfen](#gerät-wird-direkt-nach-unmount-wieder-gemountet) |
| ✅ Auswurf kontrollieren | [Mount, Freigabe und Gerät prüfen](#auswurf-erfolgreich-prüfen) |

Die Befehle verwenden die anonymisierten Shell-Variablen `$T95_USER` und
`$T95_UID`. Vor dem Test setzen:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

<a id="usb-wird-gemountet-aber-keine-samba-freigabe-erscheint"></a>

## 📂 USB wird gemountet, aber keine Samba-Freigabe erscheint

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

<a id="doppelte-extern-usb-n-freigabe"></a>

## 🔁 Doppelte `Extern-USB-N`-Freigabe

Prüfen, ob mehrere Shares auf denselben Pfad zeigen:

```bash
for s in $(sudo -u $T95_USER net usershare list); do
  sudo -u $T95_USER net usershare info "$s"
done
```

Die Referenzversion von `t95-usb-share` ist idempotent und darf denselben Mountpunkt nicht doppelt veröffentlichen.

<a id="command-not-found-für-rmloggerheadsync-innerhalb-eines-skripts"></a>

## 🛠️ `command not found` für rm/logger/head/sync innerhalb eines Skripts

Prüfen, ob die Shell-Systemvariable `PATH` überschrieben wurde:

```bash
grep -n '\bPATH\b' /usr/local/bin/t95-usb-share
grep -n '\bPATH\b' /usr/local/bin/usb-eject
```

`PATH` darf nur der Kommando-Suchpfad sein. Für Dateipfade Namen wie `SAVED_PATH` verwenden.

<a id="devicebusy-beim-auswerfen"></a>

## 🔒 `DeviceBusy` beim Auswerfen

```bash
fuser -vm /media/$T95_USER/MOUNTNAME
smbstatus --shares
```

Wenn `smbd` den Mount hält:

```bash
sudo smbcontrol smbd close-share SHARENAME
```

Die Referenzversion von `usb-eject` führt diesen Schritt automatisch aus.

<a id="gerät-wird-direkt-nach-unmount-wieder-gemountet"></a>

## 🔌 Gerät wird direkt nach Unmount wieder gemountet

`udiskie` darf während der Unmount/Power-Off-Sequenz nicht weiterlaufen. Die Referenzversion von `usb-eject` stoppt den User-Service temporär und startet ihn anschließend wieder.

<a id="auswurf-erfolgreich-prüfen"></a>

## ✅ Auswurf erfolgreich prüfen

```bash
findmnt /media/$T95_USER/MOUNTNAME
sudo -u $T95_USER net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

Nach erfolgreichem `udisksctl power-off` sollte das physische `/dev/sdX` aus `lsblk` verschwinden.

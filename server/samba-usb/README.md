# T95 Samba + USB-Automount für Armbian

Reproduzierbare Dokumentation der Samba-/USB-Konfiguration eines
T95-Armbian-Servers. Die Beispiele verwenden bewusst keine persönlichen
Benutzernamen oder festen Heimnetz-Adressen.

Stand: 2026-09-16

## Ziel

Der Server soll sich auf Clients wie ein zentraler Netzwerkspeicher verhalten. Der bevorzugte Zugriff ist auf die Samba-Serverwurzel, z. B.:

```text
smb://<SERVER-IP>/
```

Dort erscheinen gemeinsam:

- die feste interne Freigabe `T95-DATA`
- automatisch erzeugte Freigaben für eingesteckte USB-Sticks/SSDs
- Medien mit Label unter ihrem Label, z. B. `SunDiskUSB`
- Medien ohne Label als `Extern-USB-1`, `Extern-USB-2`, ...

Es gibt **keine statische `[USB]`-Sammelfreigabe** auf `/media/$T95_USER`. Jeder Datenträger bekommt eine eigene Samba-Freigabe. Dadurch meldet Samba für jedes USB-Medium die korrekte Kapazität und den korrekten freien Speicherplatz.

## Verzeichnisstruktur dieses Archivs

```text
T95-Samba-USB-Setup/
├── README.md
├── CHANGELOG.md
├── docs/
│   ├── SAMBA-USB-SETUP.md
│   ├── RESTORE-CHECKLIST.md
│   └── TROUBLESHOOTING.md
├── config/
│   ├── polkit/50-t95-udisks.rules
│   ├── samba/smb.conf.fragment
│   ├── systemd-user/udiskie.service
│   └── udiskie/config.json
└── scripts/
    ├── restore-samba-usb-setup.sh
    ├── t95-usb-share
    └── usb-eject
```

## Schnellwiederherstellung

Für eine frische Debian-/Armbian-Installation kann das Restore-Skript verwendet werden:

> [!CAUTION]
> Das Restore-Skript installiert Pakete, aktiviert `smbd`/`udiskie` und ersetzt
> `/etc/samba/smb.conf` nach einer Sicherung durch eine minimale Konfiguration.
> Auf einem bereits produktiven Samba-Server zuerst die vollständige
> Dokumentation lesen und die lokale Sicherung prüfen.

```bash
cd server/samba-usb
sudo T95_USER=serveruser ./scripts/restore-samba-usb-setup.sh
```

Standardwerte:

```text
Linux-/Samba-Benutzer: der mit T95_USER angegebene Benutzer
NetBIOS-Name:          T95-SERVER
Interne Datenfreigabe: /srv/T95-DATA/Share
USB-Mountbasis:        /media/<LINUX_USER>
```

Abweichende Werte können vor dem Aufruf gesetzt werden:

```bash
sudo T95_USER=serveruser NETBIOS_NAME=MY-SERVER DATA_PATH=/srv/data/share \
  ./scripts/restore-samba-usb-setup.sh
```

Der Wert `serveruser` ist nur ein Beispiel. Er muss als Linux-Benutzer bereits
existieren; das Skript setzt keinen Standardbenutzer voraus.

**Achtung:** Das Restore-Skript sichert eine vorhandene `/etc/samba/smb.conf` und schreibt anschließend eine minimale bekannte Samba-Konfiguration neu. Vor Einsatz auf einem bereits produktiven Samba-Server zuerst `docs/SAMBA-USB-SETUP.md` lesen.

## Wichtige Bedienung

Aktuelle dynamische USB-Freigaben anzeigen:

```bash
sudo -u "$T95_USER" net usershare list
```

Datenträger sicher auswerfen:

```bash
sudo usb-eject SunDiskUSB
sudo usb-eject Extern-USB-1
```

Das Auswurfskript:

1. stoppt `udiskie` vorübergehend,
2. trennt aktive Samba-Verbindungen nur für die gewählte Freigabe,
3. synchronisiert Schreibpuffer,
4. hängt alle Partitionen des physischen USB-Geräts aus,
5. entfernt erst nach erfolgreichem Unmount den Samba-Usershare und die State-Datei,
6. schaltet das USB-Gerät per UDisks ab,
7. startet `udiskie` wieder.

## Sicherheit / GitHub

Nicht in ein öffentliches Repository übernehmen:

- `/var/lib/samba/private/passdb.tdb`
- Samba-Passwörter oder Klartext-Zugangsdaten
- private Schlüssel
- komplette Systembackups

Die in diesem Archiv enthaltenen Dateien enthalten keine Samba-Passwörter.

Ausführliche technische Dokumentation: [docs/SAMBA-USB-SETUP.md](docs/SAMBA-USB-SETUP.md)

# T95 Samba + USB-Automount

![Status: getestet](https://img.shields.io/badge/Status-Samba%2FUSB%20getestet-brightgreen)
![Platform: Armbian](https://img.shields.io/badge/Platform-Armbian%20%2F%20Debian-18a303)
![Protocol: SMB2%2FSMB3](https://img.shields.io/badge/Protocol-SMB2%20%2F%20SMB3-blue)
![Secrets: lokal](https://img.shields.io/badge/Secrets-nie%20in%20GitHub-critical)

Reproduzierbare Samba-/USB-Konfiguration für den als Armbian-Home-Server
betriebenen T95. Die Anleitung richtet sich an eine laufende T95-Armbian-Box,
nicht an den Linux-PC, auf dem das T95-Image gebaut wird.

## Ergebnis auf einen Blick

```mermaid
flowchart LR
    A["T95-Armbian<br/>Ethernet / end0"] --> B["restore-samba-usb-setup.sh"]
    B --> C["T95-DATA<br/>feste Freigabe"]
    B --> D["udiskie"]
    D --> E["t95-usb-share<br/>eine Freigabe je USB-Dateisystem"]
    C --> F["smb://&lt;SERVER-IP&gt;/"]
    E --> F
    F --> G["Linux · Windows · Android · VLC"]
```

Die geprüfte Bedienung ist die Serverwurzel `smb://<SERVER-IP>/`. Dort werden
die interne Freigabe `T95-DATA` und alle aktuell eingesteckten USB-/SSD-
Freigaben gemeinsam angezeigt.

Es gibt absichtlich **keine** statische `[USB]`-Sammelfreigabe. Jedes Medium
zeigt dadurch seine echte Kapazität und den korrekten freien Speicherplatz.

### Getestete Referenzplattform

| Bereich | Referenz |
| --- | --- |
| Hardware | T95 `H616-T95MAX-AXP313A-V3.0` mit Allwinner AC300 Ethernet |
| System | Armbian 26.8.4, Debian 13 Trixie, Kernel 6.18 |
| Netzwerk | Ethernet über `end0`, DHCP, SMB2/SMB3 |
| Automount | UDisks2 + udiskie + dynamische Samba-Usershares |
| Abnahme | `T95-DATA`, USB-Automount, sicherer Auswurf, Wiedereinstecken und VLC über SMB |

Andere Debian-/Armbian-Systeme können funktionieren, sind aber durch diese
Projektabnahme nicht automatisch bestätigt.

## Voraussetzungen

Vor der Installation:

- T95 ist vollständig von microSD oder eMMC gestartet und per SSH erreichbar.
- Ein normaler Linux-Benutzer existiert bereits, zum Beispiel `serveruser`.
- Dieser Benutzer darf `sudo` verwenden; das Skript selbst läuft als root.
- Die Box hat während der Paketinstallation Internetzugang.
- Für USB-Platten ist eine ausreichende externe Stromversorgung vorhanden.
- Eine bestehende Samba-Konfiguration ist gesichert oder darf ersetzt werden.

> [!WARNING]
> Das Restore-Skript installiert Pakete und Dienste, aktiviert `smbd`, `nmbd`
> und den Benutzerdienst `udiskie`. Eine vorhandene `/etc/samba/smb.conf` wird
> zunächst mit Zeitstempel gesichert und anschließend durch eine bekannte
> Minimal-Konfiguration ersetzt. Auf einem produktiven Samba-Server zuerst
> [die technische Dokumentation](docs/SAMBA-USB-SETUP.md) lesen.

## Schnellstart: reproduzierbare Wiederherstellung

Die folgenden Befehle werden **auf der T95** ausgeführt. `serveruser` ist nur
ein Beispiel und muss durch einen tatsächlich vorhandenen Linux-Benutzer
ersetzt werden.

### 1. Modul beziehen und Manifest prüfen

```bash
git clone https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git
cd t95-tvbox-to-armbian-home-server/server/samba-usb
sha256sum -c MANIFEST.sha256
```

Bei lokaler Kopie genügt der Wechsel in das vorhandene Verzeichnis. Die
Manifestprüfung muss vor einer Wiederherstellung ohne `FAILED`-Zeile enden.

### 2. Linux-Benutzer und Netzwerk prüfen

```bash
export T95_USER=serveruser
id "$T95_USER"
ip -brief address
```

`id` muss den Benutzer auflösen. Die aktuelle IPv4-Adresse wird später als
`<SERVER-IP>` für den Clientzugriff verwendet.

### 3. Installation ausführen

```bash
sudo T95_USER="$T95_USER" ./scripts/restore-samba-usb-setup.sh
```

Das Skript installiert unter anderem Samba, UDisks2, udiskie, Polkit und die
Dateisystemwerkzeuge für exFAT/NTFS. Falls noch kein Samba-Konto existiert,
fragt es interaktiv nach dem Samba-Passwort für `T95_USER`.

Optionale Werte können beim Aufruf gesetzt werden:

```bash
sudo T95_USER=serveruser \
  NETBIOS_NAME=T95-SERVER \
  DATA_PATH=/srv/T95-DATA/Share \
  ./scripts/restore-samba-usb-setup.sh
```

| Variable | Pflicht | Standard | Bedeutung |
| --- | :---: | --- | --- |
| `T95_USER` | **ja** | – | vorhandener Linux- und Samba-Benutzer |
| `NETBIOS_NAME` | nein | `T95-SERVER` | Name des Servers im SMB-Netz |
| `DATA_PATH` | nein | `/srv/T95-DATA/Share` | Verzeichnis der festen Freigabe |

Das Skript verwendet daraus abgeleitet `/media/<T95_USER>` als Mountbasis und
`~/.local/state/t95-usb-shares` für die dynamischen Zuordnungen.

## Nach der Installation prüfen

Alle Prüfungen laufen auf der T95, außer dem abschließenden Clienttest.

```bash
sudo testparm -s
systemctl --no-pager --full status smbd
systemctl --no-pager --full status nmbd
sudo -u "$T95_USER" net usershare list
T95_UID="$(id -u "$T95_USER")"
sudo -u "$T95_USER" XDG_RUNTIME_DIR="/run/user/$T95_UID" \
  systemctl --user --no-pager --full status udiskie.service
```

Erwartet werden:

- `testparm` meldet eine gültige Konfiguration ohne Syntaxfehler.
- `smbd` und – sofern auf der Distribution vorhanden – `nmbd` laufen.
- `udiskie.service` ist für `T95_USER` aktiv.
- Die Liste enthält mindestens `T95-DATA`.

### USB-Datenträger anschließen

Nach dem Einstecken:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u "$T95_USER" net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 30
```

Ein gelabeltes Medium erhält einen bereinigten Namen aus seinem Label, zum
Beispiel `SunDiskUSB`. Ein Medium ohne Label erhält `Extern-USB-1`, danach
`Extern-USB-2` usw. Ein bereits veröffentlichter Mountpunkt erzeugt keine
doppelte Freigabe.

## Zugriff von Clients und VLC

Bevorzugt wird die Serverwurzel:

```text
smb://<SERVER-IP>/
```

Direkte Pfade sind ebenfalls möglich:

```text
smb://<SERVER-IP>/T95-DATA
smb://<SERVER-IP>/SunDiskUSB
smb://<SERVER-IP>/Extern-USB-1
```

| Client | Zugriff |
| --- | --- |
| Linux-Dateimanager | `smb://<SERVER-IP>/` öffnen und Samba-Benutzer anmelden |
| Windows-Explorer | `\\<SERVER-IP>\` öffnen |
| Android-Dateimanager | SMB-/Netzwerkfreigabe mit Server-IP und Samba-Konto anlegen |
| VLC | Netzwerkfreigabe öffnen und die gewünschte SMB-Datei auswählen |

Für VLC wird das Samba-Passwort des zuvor festgelegten Benutzers verwendet.
Das Projekt setzt bewusst kein Gastkonto und keine Klartext-Zugangsdaten voraus.

## USB sicher auswerfen

Immer den Freigabenamen verwenden, nicht blind ein `/dev/sdX`-Gerät angeben:

```bash
sudo usb-eject SunDiskUSB
sudo usb-eject Extern-USB-1
```

`usb-eject` führt in dieser Reihenfolge aus:

1. `udiskie` vorübergehend anhalten;
2. aktive Samba-Verbindungen nur für die ausgewählte Freigabe schließen;
3. Schreibpuffer synchronisieren;
4. alle Partitionen des physischen USB-Geräts aushängen;
5. Usershare und State-Datei erst nach erfolgreichem Unmount entfernen;
6. das Gerät über UDisks ausschalten;
7. `udiskie` wieder starten.

Erfolg kontrollieren:

```bash
findmnt "/media/$T95_USER/<MOUNTNAME>"
sudo -u "$T95_USER" net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

Nach dem Power-off sollte das physische USB-Gerät nicht mehr in `lsblk`
erscheinen. Beim erneuten Einstecken wird die Freigabe automatisch neu erzeugt.

## Konfiguration wiederherstellen

Vor dem Überschreiben legt das Restore-Skript eine Sicherung an:

```text
/etc/samba/smb.conf.before-t95.<YYYYMMDD-HHMMSS>
```

Verfügbare Sicherungen anzeigen und die gewünschte Sicherung kontrolliert
wiederherstellen:

```bash
sudo ls -1t /etc/samba/smb.conf.before-t95.*
sudo cp -a "/etc/samba/smb.conf.before-t95.<TIMESTAMP>" /etc/samba/smb.conf
sudo testparm -s
sudo systemctl restart smbd
```

Dies stellt die Samba-Konfigurationsdatei wieder her. Ein vollständiges
Deinstallations- oder Rückbauprogramm für alle installierten Pakete, Polkit-
Regeln und Benutzerdateien ist absichtlich nicht Bestandteil dieses Moduls.

## Sicherheit und Veröffentlichung

> [!CAUTION]
> Niemals produktive Geheimnisse in dieses Repository kopieren.

Nicht veröffentlichen:

- `/var/lib/samba/private/passdb.tdb`;
- Samba-Passwörter oder Klartext-Zugangsdaten;
- `/etc/shadow`, SSH-Private-Keys und komplette Systembackups;
- lokale Images, UART-Captures oder persönliche Konfigurationsdateien.

Die Vorlagen und Skripte im Modul enthalten keine Samba-Passwörter. Das
Passwort wird erst auf der T95 mit `smbpasswd` gesetzt.

## Weiterführende Dokumentation

- [Vollständige technische Dokumentation](docs/SAMBA-USB-SETUP.md)
- [Restore-Checkliste](docs/RESTORE-CHECKLIST.md)
- [Fehlerdiagnose](docs/TROUBLESHOOTING.md)
- [Hinweise zur GitHub-Veröffentlichung](docs/GITHUB-PUBLISH.md)
- [Änderungsverlauf](CHANGELOG.md)

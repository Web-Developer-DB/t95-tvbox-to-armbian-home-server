# Vollständige Dokumentation: Samba + dynamische USB-Freigaben auf T95/Armbian

Stand: **2026-09-16**

Diese Dokumentation beschreibt den tatsächlich getesteten Aufbau des T95-Armbian-Servers und die Fehler, die während der Einrichtung gefunden und behoben wurden.

Die Beispiele sind anonymisiert. Vor dem Ausführen in einer Shell den eigenen
Linux-Benutzer und dessen UID setzen:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

`serveruser` ist nur ein Platzhalter. Konfigurationsblöcke mit
`$T95_USER` oder `/media/$T95_USER` sind Vorlagen; das Restore-Skript erzeugt
die konkreten Werte automatisch.

## 1. Zielbild

Der T95 dient als leichter Datei- und Medienserver. Samba stellt die interne Datenpartition sowie wechselbare USB-Datenträger im LAN bereit.

Gewünschte Client-Bedienung:

```text
smb://<SERVER-IP>/
```

Statt jede Freigabe einzeln als URL zu speichern, wird die Serverwurzel geöffnet. Dort zeigt Samba alle gerade verfügbaren Freigaben gemeinsam an.

Beispiele:

```text
T95-DATA
SunDiskUSB
Extern-USB-1
Extern-USB-2
```

### Warum keine `[USB]`-Sammelfreigabe?

Eine frühere Konfiguration hatte:

```ini
[USB]
    path = /media/$T95_USER
```

Das war funktional, hatte aber einen wichtigen Nachteil: Die freie/gesamte Kapazität wurde vom Dateisystem geliefert, auf dem `/media/$T95_USER` selbst liegt, also von der System-SD-Karte. Die Kapazität des tatsächlich eingehängten USB-Datenträgers wurde dadurch im Client falsch dargestellt.

Die endgültige Lösung verwendet deshalb pro USB-Dateisystem einen eigenen Samba-Usershare. Dadurch verweist jede Freigabe direkt auf den echten Mountpunkt des Datenträgers.

## 2. Relevanter Serverzustand

Getestete Installation:

```text
System:      Armbian / Debian 13 (trixie)
Architektur: arm64
Servername:  T95-SERVER
LAN-IP:      <SERVER-IP> (Beispiel aus der Installation)
Benutzer:    $T95_USER
```

Interne Datenpartition:

```text
/dev/mmcblk2p1
Label: T95-DATA
Mount: /srv/T95-DATA
```

Struktur:

```text
/srv/T95-DATA/
├── Backup/       # lokal, nicht per Samba freigegeben
└── Share/        # Samba-Freigabe T95-DATA
```

Samba veröffentlicht nur:

```text
/srv/T95-DATA/Share
```

## 3. Benötigte Pakete

```bash
sudo apt update
sudo apt install samba samba-common-bin \
  udisks2 udiskie dbus-user-session polkitd \
  exfatprogs ntfs-3g
```

Relevante Werkzeuge daraus bzw. aus dem Basissystem:

```text
smbd / nmbd
net usershare
smbcontrol
udisksctl
udiskie
findmnt
lsblk
logger
systemctl --user
```

## 4. Samba-Benutzer und Usershare-Gruppe

Der Linux-Benutzer `$T95_USER` muss existieren.

Samba-Benutzer anlegen:

```bash
sudo smbpasswd -a $T95_USER
```

Prüfen:

```bash
sudo pdbedit -L
```

`$T95_USER` zur Gruppe `sambashare` hinzufügen:

```bash
sudo usermod -aG sambashare $T95_USER
```

Danach muss die Gruppenmitgliedschaft in einer neuen Session aktiv sein. Prüfen:

```bash
id $T95_USER
```

Das Usershare-Verzeichnis:

```bash
sudo chown root:sambashare /var/lib/samba/usershares
sudo chmod 1770 /var/lib/samba/usershares
```

## 5. Samba-Konfiguration

Die wichtigen Einstellungen in `/etc/samba/smb.conf` sind:

```ini
[global]
    netbios name = T95-SERVER
    server min protocol = SMB2

    usershare path = /var/lib/samba/usershares
    usershare max shares = 20
    usershare owner only = no
    usershare allow guests = no
    usershare prefix allow list = /media/$T95_USER

[T95-DATA]
    path = /srv/T95-DATA/Share
    browseable = yes
    read only = no
    guest ok = no
    valid users = $T95_USER
    create mask = 0660
    directory mask = 0770
```

Wichtig:

```text
Keine statische [USB]-Freigabe auf /media/$T95_USER verwenden.
```

Konfiguration prüfen und Samba neu starten:

```bash
sudo testparm
sudo systemctl restart smbd
```

Der Server kann vom Client direkt über die IP geöffnet werden:

```text
smb://<SERVER-IP>/
```

NetBIOS-Namensauflösung kann je nach Client/Netzwerk unzuverlässig sein. Der Zugriff per IP war in dieser Installation zuverlässig.

## 6. Interne T95-DATA-Berechtigungen

Empfohlene Rechte:

```bash
sudo chown $T95_USER:$T95_USER /srv/T95-DATA/Share
sudo chmod 2770 /srv/T95-DATA/Share
```

Der Backup-Bereich bleibt lokal und wird nicht als Samba-Share angelegt.

## 7. UDisks/Polkit: USB ohne Passwort mounten und auswerfen

Datei:

```text
/etc/polkit-1/rules.d/50-t95-udisks.rules
```

Inhalt siehe:

```text
config/polkit/50-t95-udisks.rules
```

Die Regel erlaubt ausschließlich dem Benutzer `$T95_USER` die für UDisks benötigten Mount-/Unmount-/Eject-/Power-Off-Aktionen.

Hinweis: `polkit.service` ist auf Debian typischerweise statisch. Ein `systemctl enable polkit` ist daher nicht nötig. Polkit wird über D-Bus aktiviert.

## 8. udiskie als dauerhafter Benutzer-Service

Damit der Automounter auch ohne interaktive SSH-/Desktop-Sitzung läuft:

```bash
sudo loginctl enable-linger $T95_USER
```

User-Manager starten:

```bash
sudo systemctl start user@1000.service
```

Die UID darf nicht fest angenommen werden. Allgemein:

```bash
id -u $T95_USER
```

### User-Service

Datei:

```text
/home/$T95_USER/.config/systemd/user/udiskie.service
```

Inhalt:

```ini
[Unit]
Description=udiskie USB Automounter
After=default.target

[Service]
Type=simple
ExecStartPre=/usr/local/bin/t95-usb-share startup
ExecStart=/usr/bin/udiskie --no-notify
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
```

Aktivieren:

```bash
sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  systemctl --user daemon-reload

sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  systemctl --user enable --now udiskie.service
```

Prüfen:

```bash
sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  systemctl --user status udiskie.service --no-pager
```

## 9. udiskie Event-Hook

Datei:

```text
/home/$T95_USER/.config/udiskie/config.json
```

```json
{
  "program_options": {
    "automount": true,
    "notify": false,
    "file_manager": "",
    "event_hook": [
      "/usr/local/bin/t95-usb-share",
      "{event}",
      "{device_file}",
      "{mount_path}",
      "{id_label}",
      "{id_uuid}"
    ]
  }
}
```

Bei `device_mounted` bekommt das Share-Skript u. a. Gerät, Mountpunkt, Label und UUID übergeben.

## 10. Dynamisches Share-Skript

Installationspfad:

```text
/usr/local/bin/t95-usb-share
```

Referenzversion:

```text
scripts/t95-usb-share
```

Aufgabe:

- veraltete State-Dateien aufräumen
- nur `/dev/sd*` unter `/media/$T95_USER/*` verarbeiten
- Datenträgerlabel zu einem Samba-Namen normalisieren
- bei vorhandenem Label z. B. `SunDiskUSB` erzeugen
- bei fehlendem Label `Extern-USB-1`, `Extern-USB-2`, ... vergeben
- doppelte Label-Namen mit `-2`, `-3`, ... auflösen
- denselben Mountpunkt niemals doppelt freigeben
- Usershare mit ACL `$T95_USER:F` und `guest_ok=n` erzeugen
- Mapping als `.map` speichern
- Aktionen über `logger -t T95-USB-SHARE` protokollieren

State-Verzeichnis:

```text
/home/$T95_USER/.local/state/t95-usb-shares/
```

Beispiel:

```text
sdb1.map
```

Inhalt:

```text
Extern-USB-1    /media/$T95_USER/6BBF-FE93    /dev/sdb1    6BBF-FE93
```

Die Felder sind tab-separiert.

### Wichtige Eigenschaft: Idempotenz

`udiskie` kann dasselbe Mount-Ereignis mehr als einmal melden. Das Skript prüft daher zuerst, ob bereits irgendein Usershare auf denselben Mountpunkt zeigt.

Getestet:

```text
1. Aufruf  -> Extern-USB-1
2. Aufruf  -> weiterhin nur Extern-USB-1
```

Dadurch entsteht kein falsches `Extern-USB-2` für dasselbe physische Medium.

## 11. Sicheres Auswerfen

Installationspfad:

```text
/usr/local/bin/usb-eject
```

Referenzversion:

```text
scripts/usb-eject
```

Benutzung:

```bash
sudo usb-eject SunDiskUSB
sudo usb-eject Extern-USB-1
```

Die Reihenfolge ist absichtlich genau so:

```text
udiskie stoppen
-> aktive Samba-Verbindungen dieser Freigabe schließen
-> sync
-> unmount
-> NUR BEI ERFOLGREICHEM UNMOUNT Usershare + State löschen
-> udisksctl power-off
-> udiskie wieder starten
```

### Warum `udiskie` vorübergehend stoppen?

Ohne diesen Schritt entstand ein Race Condition:

```text
udisksctl unmount
-> udiskie sieht weiterhin das angeschlossene Medium
-> udiskie mountet es sofort erneut
-> power-off kommt zu spät
```

Mit temporär gestopptem `udiskie` verschwindet das Gerät nach `power-off` vollständig aus `lsblk`.

### Warum `smbcontrol smbd close-share`?

Ein Client kann einen Samba-Share offen halten, selbst wenn gerade keine Datei aktiv kopiert wird.

Diagnose aus dem Test:

```text
fuser -vm /media/$T95_USER/6BBF-FE93
root 1920 ..c.. smbd
```

Dann verweigerte UDisks das Unmount mit:

```text
org.freedesktop.UDisks2.Error.DeviceBusy
```

Die Lösung:

```bash
smbcontrol smbd close-share Extern-USB-1
```

Das trennt nur aktive Verbindungen zu dieser Freigabe. Andere Samba-Freigaben bleiben bestehen.

## 12. Vollständig validierter Auswurf-Test

Vorher:

```text
/media/$T95_USER/6BBF-FE93 -> /dev/sdb1
Extern-USB-1 vorhanden
```

Auswurf:

```text
Stoppe USB-Automounter kurzzeitig ...
Trenne aktive Samba-Verbindungen ...
Schreibe gepufferte Daten ...
Hänge /dev/sdb1 aus ...
Unmounted /dev/sdb1.
Entferne Samba-Freigabe ...
Schalte USB-Gerät ab ...
USB-Datenträger kann entfernt werden.
```

Nachher:

```bash
findmnt /media/$T95_USER/6BBF-FE93
```

keine Ausgabe.

```bash
sudo -u $T95_USER net usershare list
```

`Extern-USB-1` ist verschwunden; andere Medien wie `SunDiskUSB` bleiben erhalten.

```bash
lsblk
```

`/dev/sdb` ist nach erfolgreichem Power-Off vollständig verschwunden.

Beim physischen Wiedereinstecken:

```text
udiskie mountet automatisch
-> t95-usb-share läuft
-> Samba-Usershare wird automatisch neu angelegt
```

## 13. Unterstützte Namenslogik

### Medium mit Label

```text
Label: SunDiskUSB
Mount: /media/$T95_USER/SunDiskUSB
Share: SunDiskUSB
```

Doppeltes Label:

```text
SunDiskUSB
SunDiskUSB-2
SunDiskUSB-3
```

### Medium ohne Label

UDisks kann als Mountverzeichnis z. B. die UUID verwenden:

```text
/media/$T95_USER/6BBF-FE93
```

Der Samba-Name ist bewusst lesbarer:

```text
Extern-USB-1
```

Ein zweites gleichzeitig angeschlossenes namenloses Medium erhält:

```text
Extern-USB-2
```

Wird `Extern-USB-1` entfernt, kann die Nummer später wieder frei werden.

## 14. Gefundene und behobene Fehler

### Fehler 1: Endlosschleife bei Usershare-Prüfung

Ursprünglich wurde nur der Exit-Code von

```bash
net usershare info NAME
```

als Existenztest benutzt. Das Verhalten war dafür ungeeignet und führte dazu, dass das Skript glaubte, `Name-2`, `Name-3`, ... existierten alle. Ergebnis: Endlosschleife.

Lösung:

```bash
net usershare info "$name" | grep -Fxq "[$name]"
```

### Fehler 2: Shell-Systemvariable `PATH` überschrieben

In State-Parsing-Code wurde `PATH` versehentlich als normale Variable verwendet:

```bash
read -r SHARE PATH DEV UUID
```

Danach konnten Befehle wie `rm`, `logger`, `head` und `sync` nicht mehr gefunden werden.

Lösung:

```text
SAVED_PATH statt PATH
```

Zusätzlich setzen beide Skripte explizit einen sicheren Kommando-PATH.

### Fehler 3: Doppelte Freigaben bei mehrfachem Event

Ein Medium ohne Label erhielt plötzlich gleichzeitig:

```text
Extern-USB-1
Extern-USB-2
```

Beide zeigten auf denselben Mountpunkt.

Lösung: vor dem Erzeugen eines neuen Namens alle bestehenden Usershares auf denselben Mountpfad prüfen.

### Fehler 4: Sofortiges Remount nach Unmount

`udiskie` mountete das Gerät zwischen `unmount` und `power-off` sofort wieder.

Lösung: `udiskie` während des Auswurfs temporär stoppen.

### Fehler 5: `DeviceBusy` durch Samba

`smbd` hielt den Mountpunkt geöffnet.

Lösung: vor dem Unmount:

```bash
smbcontrol smbd close-share "$NAME"
```

### Fehler 6: Usershare zu früh gelöscht

Eine frühe Version löschte Usershare und State **vor** dem Unmount. Schlug das Unmount mit `DeviceBusy` fehl, blieb das Laufwerk gemountet, aber der Share war bereits verschwunden.

Endgültige Lösung: Usershare und State erst **nach erfolgreichem Unmount** löschen.

## 15. Tests nach Wiederherstellung

Samba:

```bash
sudo testparm -s
sudo systemctl status smbd --no-pager
sudo -u $T95_USER net usershare list
```

udiskie:

```bash
sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$T95_UID \
  systemctl --user status udiskie.service --no-pager
```

USB einstecken:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u $T95_USER net usershare list
journalctl -t T95-USB-SHARE --no-pager -n 30
```

Auswerfen:

```bash
sudo usb-eject <Freigabename>
```

Danach:

```bash
findmnt /media/$T95_USER/<Mountname>
sudo -u $T95_USER net usershare list
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
```

## 16. Client-Zugriff

Bevorzugt:

```text
smb://<SERVER-IP>/
```

Direkter Zugriff bleibt möglich:

```text
smb://<SERVER-IP>/T95-DATA
smb://<SERVER-IP>/SunDiskUSB
smb://<SERVER-IP>/Extern-USB-1
```

Die Serverwurzel ist jedoch die gewünschte Standardbedienung, weil alle aktuell verfügbaren Freigaben dort zusammen angezeigt werden.

## 17. Was nicht ins öffentliche GitHub-Repository gehört

Nicht committen:

```text
/var/lib/samba/private/passdb.tdb
/etc/shadow
SSH-Private-Keys
komplette Images/Backups
Passwörter oder Tokens
```

Die hier dokumentierte Konfiguration benötigt für GitHub keine geheimen Samba-Zugangsdaten. Das Samba-Passwort wird nach einer Wiederherstellung mit `smbpasswd -a` neu gesetzt.

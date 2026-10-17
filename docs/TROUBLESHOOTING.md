# Hilfe bei Installations- und Alltagsproblemen

**Deutsch** | [English](TROUBLESHOOTING.en.md)

Suche das sichtbare Symptom. Prüfe jeweils zuerst die einfachen Ursachen;
ändere nur eine Sache gleichzeitig. Bei abweichender oder unbekannter
Platine nicht mit dem T95-Image weiterarbeiten: [Hardware prüfen](HARDWARE_IDENTIFICATION.md).

[Zur Installation](INSTALLATION.md) · [Startseite](../README.md)

| Symptom | Einstieg |
| --- | --- |
| Werkzeug fehlt oder Download bricht ab | [PC-Vorbereitung](#werkzeug-fehlt) |
| Kartenleser erscheint nicht in der Auswahl | [SD-Erkennung](#sd-karte-wird-nicht-erkannt) |
| Box hat keine Adresse im Router | [Netzwerk und Start](#keine-ip-adresse) |
| SSH meldet Timeout, Ablehnung oder Schlüsselwarnung | [SSH-Zugang](#ssh-anmeldung-scheitert) |
| Kernelversion oder Paketsperren passen nicht | [Kernelstand](#kernelstand-weicht-ab) |
| Freigabe fehlt oder Passwort wird abgelehnt | [Samba](#freigabe-fehlt-oder-zugriff-wird-abgelehnt) |
| USB-Laufwerk fehlt oder lässt sich nicht auswerfen | [USB](#usb-laufwerk-fehlt-oder-ist-belegt) |
| Dashboard oder Bluetooth funktioniert nicht | [Zusatzmodule](#dashboard-oder-bluetooth-funktioniert-nicht) |

## Werkzeug fehlt

**Linux-PC · normaler Benutzer mit `sudo`.** Bei `Werkzeug fehlt: ...` zuerst
die [PC-Pakete installieren](INSTALLATION.md#1-hardware-und-pc-vorbereiten).
`debugfs`/`e2fsck` gehören zu `e2fsprogs`, `partprobe` zu `parted`.
Führe Bash-Blöcke in Bash aus; PowerShell versteht sie nicht.

Bei einem Downloadfehler Internetzugang und freien Speicher prüfen. Bei
einer fehlgeschlagenen SHA-256-Prüfung nicht schreiben. Starte den empfohlenen
Installer erneut im selben Arbeitsordner: Er prüft vorhandene Dateien,
bewahrt ungültige Dateien unter einem anderen Namen und lädt neu.
Fehlermeldungen zum TLS-Zertifikat nicht mit `curl -k` umgehen.

**Ergebnis:** Alle Werkzeuge sind vorhanden und das Image besteht die
Prüfsummenprüfung. Danach den abgebrochenen Installationsweg fortsetzen.

## SD-Karte wird nicht erkannt

**Linux-PC · normaler Benutzer · rein lesende Prüfung:**

```bash
lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
```

Der Installer akzeptiert nur das vollständige USB-Gerät, etwa `/dev/sdb`,
mit `TRAN=usb`, `RM=1` und `TYPE=disk`. Eine Partition wie `/dev/sdb1` ist
kein Ziel. `/dev/sdX` ist ein Platzhalter und kein tatsächlicher Gerätename.

1. Kartenleser neu anschließen und die Ausgabe erneut prüfen.
2. Falls möglich einen anderen USB-Port oder USB-Kartenleser verwenden.
3. Ein interner Leser mit `/dev/mmcblk*` oder ein Leser mit `RM=0` wird nicht
   unterstützt. Die Sicherheitsprüfung nicht abschalten.
4. Unter WSL2 muss das Gerät in Linux tatsächlich sichtbar sein. Wenn das
   Passthrough nicht zuverlässig funktioniert, natives Linux verwenden.

**Ergebnis:** Größe und Gerätekennung passen zur Karte. Im Installer erneut
wählen; nach jedem Einstecken kann sich der Gerätename ändern.

## Keine IP-Adresse

**Ort: Box, Router und PC; noch keine Änderungen am Bootsystem.**

1. Exakte Platinenrevision, SD-Einsetzen bei ausgeschalteter Box und
   erfolgreiches Ende des Schreibwerkzeugs kontrollieren.
2. Ethernet-Kabel, Router-Port und passende Stromversorgung prüfen. Der
   dokumentierte Weg verwendet kein WLAN.
3. Im Router nach einer neuen DHCP-Lease suchen. PC und Box dürfen nicht
   durch ein Gastnetz oder Client-Isolation voneinander getrennt sein.
4. Ein schwarzer HDMI-Bildschirm allein beweist keinen Bootfehler.

**Ergebnis:** Mit einer gefundenen Adresse zur
[SSH-Anmeldung](INSTALLATION.md#4-erstes-ssh-login-und-normalen-benutzer-einrichten)
zurückkehren. Bleibt die Box ohne Adresse, den
[Bootfehler mit UART eingrenzen](BOOT_TROUBLESHOOTING.md). Adapter und
Verdrahtung müssen zuerst nach [UART-Anleitung](UART_BRINGUP.md) geprüft sein.
Die eMMC wird zur Reparatur nicht gelöscht.

## SSH-Anmeldung scheitert

**PC · normaler Benutzer · Adresse aus dem Router eingeben:**

```bash
read -r -p 'IP-Adresse der T95: ' T95_IP
ssh -v "root@$T95_IP"
```

Dieser Diagnoseaufruf gilt für das **erste** Login. Nach der Ersteinrichtung
verwende deinen normalen Benutzernamen anstelle von `root`.

| Meldung | Nächster Schritt |
| --- | --- |
| `Connection timed out` / `No route to host` | Adresse, Ethernet, gemeinsames LAN und vollständigen Start prüfen |
| `Connection refused` | Adresse der richtigen Box zuordnen; beim Erststart werden SSH-Schlüssel erzeugt. Bei dauerhaftem Fehler SSH-Dienst über UART prüfen |
| `Permission denied` | Erstlogin: Root-Passwort der persönlichen Kopie; später: normales Linux-Passwort. Unveränderte öffentliche Images haben keinen Passwortzugang |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Erst klären, ob die Box neu installiert wurde oder eine andere Maschine diese IP erhalten hat; Fingerprint über vertrauenswürdige UART-Konsole vergleichen |

Nur wenn eine bekannte Neuinstallation und der neue Schlüssel bestätigt sind,
kann auf dem **PC** der alte Eintrag entfernt werden:

```bash
ssh-keygen -R "$T95_IP"
```

Danach erneut verbinden und den bestätigten Schlüssel prüfen. Eine pauschale
Deaktivierung der SSH-Schlüsselprüfung ist kein Reparaturschritt.

**Ergebnis:** Login als vorgesehener Benutzer und `sudo -v` funktionieren.
Passwörter, private Schlüssel und unbereinigte Diagnoseausgaben nicht veröffentlichen.

## Kernelstand weicht ab

**T95 · normaler SSH-Benutzer · rein lesende Prüfung:**

```bash
uname -r
apt-mark showhold
dpkg-query -W linux-image-current-sunxi64 linux-dtb-current-sunxi64
```

Erwartet: `6.18.48-current-sunxi64` und beide Pakete in der Hold-Liste.
Fehlen nur die Sperren beim richtigen Kernel, mit
[Schritt 5](INSTALLATION.md#5-kernel-und-dtb-vor-updates-schützen) fortfahren.
Bei einer anderen Kernelversion keine weitere Aktualisierung und keine
zufälligen DTB-Wechsel durchführen. Ein bekannt funktionierendes
[SD-Backup wiederherstellen](BACKUP.md#wiederherstellung-auf-dieselbe-oder-eine-ersatzkarte)
oder eine separate SD aus dem geprüften Release vorbereiten. Vorher benötigte
Dateien sichern.

## Freigabe fehlt oder Zugriff wird abgelehnt

**T95 · normaler SSH-Benutzer mit `sudo`:**

```bash
sudo testparm -s
systemctl --no-pager --full status smbd
findmnt -T /srv/t95-sd-data/Share
```

**Ergebnis:** `[T95-DATA]` verweist auf deinen gewählten Ordner und `smbd`
ist aktiv. Beim empfohlenen Erststart zeigt `findmnt` das System-Dateisystem
der SD. Bei bewusst gewählter eMMC stattdessen deren tatsächlichen Pfad und
Mount prüfen. Der Freigabename allein sagt nichts über den Datenträger aus.

Öffne auf dem **Client-PC im Dateimanager** die Serveradresse
`smb://<T95-IP>/T95-DATA`, unter Windows `\\<T95-IP>\T95-DATA`.
Ersetze `<T95-IP>` durch die Routeradresse. Verwende den normalen
Linux-Benutzernamen und dessen **Samba-Passwort**. Ein falsches gespeichertes
Clientpasswort gegebenenfalls im Dateimanager ersetzen.

Wenn das Samba-Passwort neu gesetzt werden muss, auf der **T95** als
betroffener normaler Benutzer ausführen:

```bash
sudo smbpasswd -a "$(id -un)"
```

`net usershare list` zeigt **nur dynamische Benutzerfreigaben**, keine feste
`T95-DATA`-Freigabe. Ohne eingehängtes USB-Laufwerk ist eine leere Ausgabe
normal. Für USB-Probleme den nächsten Abschnitt verwenden.

**Ergebnis:** Eine kleine Testdatei lässt sich vom Client schreiben und lesen.
Für weitere Prüfungen siehe [Samba-Modul](../server/samba-usb/README.md#nach-der-installation-prüfen).
Eine Neuinstallation des Moduls ersetzt dessen Samba-Konfiguration und ist
kein erster Diagnoseschritt.

## USB-Laufwerk fehlt oder ist belegt

**T95 · normaler SSH-Benutzer · rein lesende Prüfung:**

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS
sudo -u "$(id -un)" net usershare list
sudo journalctl -t T95-USB-SHARE --no-pager -n 30
systemctl --user --no-pager --full status udiskie.service
```

Ein eingebundenes Laufwerk sollte unter `/media/<Benutzer>/...` stehen und
eine eigene Freigabe besitzen. Ohne Label heißen diese beispielsweise
`Extern-USB-1`; mit Label wird der Name daraus abgeleitet. Bei fehlendem
Gerät Kabel und Stromversorgung prüfen. USB-Festplatten können externe
Versorgung benötigen. Vorhandene Daten nicht zur Fehlerbehebung formatieren.

Zum Auswerfen auf der **T95 mit `sudo`** den tatsächlichen Freigabenamen aus
der Liste verwenden, beispielsweise:

```bash
sudo usb-eject Extern-USB-1
```

Bei `DeviceBusy` auf Clients geöffnete Dateien und VLC-Wiedergaben schließen,
auch ein Terminal darf nicht im USB-Verzeichnis stehen. Dann den Auswurf
wiederholen. Kein erzwungenes Aushängen und kein Abziehen während Schreibzugriffen.

**Ergebnis:** Erst nach erfolgreichem Auswurf abziehen. Wiedereinstecken
erzeugt die Freigabe erneut. Weitere Diagnose:
[Samba-/USB-Fehlerhilfe](../server/samba-usb/docs/TROUBLESHOOTING.md).

## Dashboard oder Bluetooth funktioniert nicht

**T95 · normaler SSH-Benutzer · nach Installation des jeweiligen Moduls:**

```bash
t95-dashboard status
t95-bluetooth status
```

`command not found` bedeutet, dass der jeweilige Helfer noch nicht installiert
ist. Lokale Aufrufe mit `server/setup/t95_setup.py` benötigen einen Checkout
von **`main`**; der PC-Checkout vom Release-Tag enthält die aktuellen
Zusatzmodule nicht. Siehe [Setup-Quellstand](../server/setup/README.md#lokaler-checkout).

Vor Änderungen ein Backup verwenden. Einzelheiten, Rücknahme
und Audio-Diagnose stehen in [Dashboard](SSH_DASHBOARD.md),
[Bluetooth](../server/bluetooth/README.md) und [Musikplayer](MUSIKPLAYER_CHEATSHEET.md).

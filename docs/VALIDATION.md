# Öffentliche Testmatrix: stabil getesteter T95-Stand

**Deutsch** | [English](VALIDATION.en.md)

Der finale Asset-Kanal ist `v1.0.1`. Historische Experiment-Assets bleiben
im privaten Laborbestand dokumentiert und werden nicht als finaler Download
beworben.

Diese Zusammenfassung enthält nur generische Prüfergebnisse. Rohe UART-Logs,
lokale IP- und MAC-Adressen, Routerdaten, SD-Backups und die Android-Forensik
bleiben außerhalb des öffentlichen Repositorys.

## Hardware- und Startpfad

| Test | Ergebnis | Aussage |
|---|---|---|
| Board-Abgleich | bestanden | `H616-T95MAX-AXP313A-V3.0` |
| FEL-Erkennung | bestanden | SoC als Allwinner H616 erkannt |
| TOC0 von microSD | bestanden | eigener Loader startet autonom von SD |
| DRAM | bestanden | U-Boot meldet 2048 MiB |
| DRAM-Spannung in Linux-DTB | bestanden | AXP313A DCDC3 Minimum/Maximum jeweils 1.360.000 µV |
| AXP313/AC300 | bestanden | EPHY antwortet, Reset und Vorinitialisierung erfolgreich |
| Ext4-Bootskript | bestanden | Kernel und Initramfs von SD geladen |
| Linux-Userspace | bestanden | systemd und multi-user target erreicht |
| Endanwender-Start | bestanden | T95 startet aus dem ausgeschalteten Zustand von microSD |
| Sauberes Herunterfahren | bestanden | System kontrolliert beendet und erneut gestartet |
| Dateizugriff | bestanden | Dateien über den eingerichteten Serverpfad erreichbar |
| Ethernet | bestanden | `end0`, 100 Mbit/s Full Duplex |
| DHCP und SSH | bestanden | Lease und Armbian-Ersteinrichtung auf Ausgangsimage |
| Samba `T95-DATA` | bestanden | authentifizierte SMB2/SMB3-Freigabe auf der T95 |
| USB-Automount/Usershares | bestanden | dynamische Shares, sicherer Auswurf und Wiedereinstecken |
| VLC über SMB | bestanden | lokale Netzwerk-Wiedergabe geprüft |
| eMMC als ext4-Datenlaufwerk | bestanden | interner Speicher als Datenmedium nutzbar |
| Armbian-Boot von eMMC | fehlgeschlagen | SD bleibt der nachgewiesene Bootweg |
| Android-eMMC | unverändert | kein Lese- oder Schreibvorgang im Releaseweg |

Die UART-Aufzeichnung erfolgte mit einem externen
[RP2040-Zero-UART-Adapterprojekt](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
bei 3,3-V-TTL und 115200 Baud/8N1.

## Härtung des öffentlichen Images

| Offline-Prüfung | Ergebnis |
|---|---|
| Rootkonto | gesperrt; kein veröffentlichter Anfangshash |
| SSH-Hostkeys | im Image nicht vorhanden |
| SSH-Startreihenfolge | Schlüsselgenerierung vor `ssh.service` |
| Armbian-Erststart | spätere Hostkey-Neuerzeugung deaktiviert |
| Quell-Root-Hash | im vollständigen Rohimage nicht auffindbar |
| Drei Quellhostkey-Payloads | im vollständigen Rohimage nicht auffindbar |
| `machine-id` | leer |
| Ext4 | `e2fsck -fn` bestanden |

Das Ergebnis ist ein generisches, nicht direkt loginfähiges Image. Vor dem
Schreiben wird lokal ein eigener Passwort-Hash eingetragen; die dabei erzeugte
Kopie ist kein Release-Asset.

## Release-Dateien

| Datei | SHA-256 |
|---|---|
| gehärtetes Rohimage, entpackt | `849ec697bca90c07537b4b71bad350c9a05854ac8287fc960483d3bf0d0b7cf4` |
| T95-TOC0-Loader | `6c408cc237f7e7514ed4307f087f9305f3447f70f9893ae52e1f290f6613ed6a` |
| T95/Tanix-6.18-DTB | `b4b0b19d8287663f79efc59e50fc0a7408f7a5a0900d2cc162bfb8a72834857e` |
| Armbian-Quellimage, XZ | `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` |

Der Loader wurde bei Byte 8192 gegen die separate Loaderdatei verglichen. Das
Release-Asset wurde mit `xz --check=sha256` komprimiert; seine sechs Dateien
werden über `SHA256SUMS` geprüft.

## Dashboard und Bluetooth

**Geprüft und getestet, bestätigt am 17.10.2026.** Der Projektbetreiber hat
die dokumentierten Schritte für Bluetooth und Dashboard selbst geprüft und
als funktionsfähig bestätigt. Diese Rückmeldung ergänzt die automatisierten
Setup-Tests und die bisherigen Funktionsnachweise der Referenzinstallation.

| Prüfung | Ergebnis | Nachweis |
| --- | --- | --- |
| Dokumentierte Dashboard-Schritte | bestanden | Funktionsbestätigung des Projektbetreibers am 17.10.2026 |
| Dokumentierte Bluetooth-Schritte | bestanden | Funktionsbestätigung des Projektbetreibers am 17.10.2026 |
| Setup-Installation, Rücknahme und Fehlerfälle in Testumgebung | bestanden | 16 automatisierte Tests mit simuliertem APT/systemd/BlueZ |

Für folgende Einzelprüfungen liegt noch keine gesonderte Bestätigung vor:

- [ ] Vollständige Neuinstallation und Rücknahme auf einer separaten, frisch eingerichteten SD mit anschließendem Kaltstart.
- [ ] Gemeinsame Einrichtung beider Module über Menüpunkt `0` auf dieser separaten SD.
- [ ] Bei fehlendem Kopfhörer praktisch prüfen, dass MPD nicht auf einen anderen Audio-Ausgang ausweicht.

Für diese Prüfungen die funktionierende Produktiv-SD als Rückweg erhalten.
Die Rückmeldung enthält keine Angaben zu einer Ersatz-SD oder diesen
Einzelprüfungen; sie werden daher getrennt von den bestätigten Schritten geführt.

## Optionale Weiterentwicklung

- zusätzliche USB-/SMB-Dauerlast, weitere Kaltstarts und Langzeitstabilität;
- WLAN, HDMI, weitere Audio-Ausgänge und Infrarot-Fernbedienung;
- dauerhafter Ersatz für `clk_ignore_unused nohz=off`;
- Kernel- oder Bootloader-Aktualisierungen.

Der dokumentierte Grundstand darf für die geprüfte Platine als **stabil
getesteter Home-Server-Release** bezeichnet werden. Die offenen Punkte sind
Erweiterungen und keine bekannten Fehler im abgenommenen Funktionsumfang.

## Abnahme der Installationsanleitung

**Stand 17.10.2026: offen.** Die neu geordnete Anleitung wurde redaktionell
und statisch geprüft. Ein vollständiger Durchlauf genau dieses Nutzerwegs
auf einer separaten SD ist noch nicht durchgeführt. Vorhandene Hardwaretests
oben und die bestätigten Dashboard-/Bluetooth-Schritte sind davon getrennt.

**Dokumentationsprüfung am 17.10.2026:** Alle 16 vorhandenen Setup-Tests,
21 Shell-Syntaxprüfungen und 34 Samba-/Dashboard-Prüfsummeneinträge bestehen.
Relative Dokumentationsverweise, Bildziele, Übersetzungslinks und die früheren
README-Sprungmarken wurden geprüft. Startseite und Übergang zur Installation
und Samba-Anleitung wurden in einer lokalen Markdown-Vorschau kontrolliert.
Die Befehlsblöcke wurden bei dieser statischen Prüfung auf Bash-Syntax geprüft.
Der Funktionsnachweis des Projektbetreibers für Dashboard und Bluetooth ist
im vorigen Abschnitt dokumentiert.

Ein Prüfer mit grundlegenden Terminal-/SSH-Kenntnissen soll der
[Installation](INSTALLATION.md) ohne zusätzliche mündliche Anleitung folgen.
Die funktionierende Produktiv-SD bleibt als Rückweg erhalten.

- [ ] Exakten Boardaufdruck, Datum, Prüfer und Image-Version festhalten.
- [ ] Linux-PC vorbereiten; Quellstände und SD-Ziel ohne Hilfe erkennen.
- [ ] Download/Prüfung, Passwort-Personalisierung und verifiziertes SD-Schreiben abschließen.
- [ ] Kaltstart, Routeradresse, erstes Root-Login und Armbian-Ersteinrichtung prüfen.
- [ ] Als normaler Benutzer erneut anmelden; `sudo`, Kernelversion und beide Holds prüfen.
- [ ] Grundsystem-Backup erstellen und Archiv/Prüfsumme prüfen.
- [ ] Samba mit ausdrücklich gewähltem SD-Pfad installieren; feste Freigabe ohne USB prüfen.
- [ ] Testdatei vom Client schreiben und lesen; Samba-Passwort richtig zuordnen.
- [ ] USB anschließen, dynamische Freigabe prüfen, sicher auswerfen, erneut anschließen und zugreifen.
- [ ] Sauber herunterfahren, kalt starten und SSH/Dateizugriff erneut prüfen.
- [ ] Konfiguriertes SD-Backup erstellen; Wiederherstellung auf Ersatzkarte und Boot separat prüfen.

Ergebnis, tatsächlich verwendete Karten-/Clienttypen und Abweichungen ohne
private Zugangsdaten protokollieren. Ungeprüfte Punkte bleiben offen; eine
Prüfsummen- oder Syntaxprüfung zählt nicht als Hardwareabnahme. Die bestätigten
Dashboard-/Bluetooth-Schritte und ihre offenen Einzelprüfungen stehen unter
[Dashboard und Bluetooth](#dashboard-und-bluetooth). Die
[Setup-Prüfanleitung](../server/setup/README.md#prüfen-vor-veröffentlichung)
beschreibt die automatisierten Prüfungen.

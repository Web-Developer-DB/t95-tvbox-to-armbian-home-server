# Öffentliche Testmatrix: stabil getesteter T95-Stand

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

## Optionale Weiterentwicklung

- zusätzliche USB-/SMB-Dauerlast, weitere Kaltstarts und Langzeitstabilität;
- WLAN, HDMI, Audio und Fernbedienung;
- dauerhafter Ersatz für `clk_ignore_unused nohz=off`;
- Kernel- oder Bootloader-Aktualisierungen.

Der dokumentierte Grundstand darf für die geprüfte Platine als **stabil
getesteter Home-Server-Release** bezeichnet werden. Die offenen Punkte sind
Erweiterungen und keine bekannten Fehler im abgenommenen Funktionsumfang.

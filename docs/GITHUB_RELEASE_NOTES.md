# T95 → Armbian Home-Server v1.0.1

Stabil getestetes, hardwaregebundenes SD-Release für die Platine
**`H616-T95MAX-AXP313A-V3.0`**, Allwinner H616, 2 GiB DDR3L,
Armbian 26.8.4 / Debian 13 Trixie / Kernel `6.18.48-current-sunxi64`.
Andere als „T95“ verkaufte Boxen sind nicht automatisch kompatibel.

> [!IMPORTANT]
> **Vor dem Schreiben zwingend lokal personalisieren.** Das öffentliche
> Image enthält kein Standardpasswort: Root ist gesperrt. Ein unverändert
> geflashtes Image ermöglicht keinen Passwortzugang. Verwende den unten
> verlinkten Installationsweg, um eine private Kopie mit eigenem Passwort
> zu erstellen und anschließend geprüft auf SD zu schreiben.

> [!CAUTION]
> **Kernel und DTB dauerhaft sperren.** Die DTB beschreibt die Hardware der Platine.
> Die Sperre nach der Ersteinrichtung und vor weiteren Installationen oder Updates
> setzen. Ein Ersatz dieser angepassten Dateien kann den Start der Box verhindern.
> [Pflichtschritt zum Schutz](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/INSTALLATION.md#5-kernel-und-dtb-vor-updates-schützen).

## Installation

**[→ Vollständige Anleitung auf Deutsch](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/INSTALLATION.md)** ·
**[English installation guide](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/INSTALLATION.en.md)**

1. Exakte Platinenrevision prüfen; Linux-PC und USB-Kartenleser vorbereiten.
2. Installer verwenden: Release laden, Prüfsumme kontrollieren und persönliche
   Image-Kopie mit eigenem Root-Passwort erzeugen.
3. SD anhand von Größe/Modell/Seriennummer auswählen. Schreiben löscht die
   gesamte Zielkarte; das Werkzeug liest die Karte zurück und prüft sie.
4. SD nur bei ausgeschalteter T95 einsetzen, Ethernet verbinden, starten und
   die DHCP-Adresse im Router suchen. Per SSH als `root` mit dem in Schritt 2
   gewählten Passwort anmelden; den Hostschlüssel der richtigen Box zuordnen.
5. Armbian-Ersteinrichtung abschließen, als normaler Benutzer erneut anmelden,
   Kernel-/DTB-Pakete vor Updates sperren. Ein privates SD-Backup ist ein optionaler Rückweg.
6. Optional Samba installieren und Dateizugriff prüfen. Der empfohlene feste
   Speicherpfad liegt ausdrücklich auf der System-SD; USB-Freigaben sind separat.

Die Anleitung verwendet das Basisimage und die Image-Werkzeuge von `v1.0.1`.
Dashboard und Bluetooth sind optionale Zusatzmodule aus `main`. Ihre
dokumentierten Schritte wurden vom Projektbetreiber am 17.10.2026 geprüft
und als funktionsfähig bestätigt.

## Änderung in v1.0.1: DRAM-Stabilität

Der Linux-DTB hält den AXP313A-Regler `dcdc3` mit Minimum und Maximum auf
**1,36 V**. Das entspricht der SPL-Initialisierung und verhindert die vorherige
Absenkung auf 1,20 V beim Kernelstart. Vollständige Kaltstarts bis zum Login
wurden auf zwei Boxen der exakten Platinenrevision geprüft.

## Was geprüft ist und welche Grenzen gelten

- microSD-Boot, Ethernet/DHCP, SSH, sauberes Herunterfahren und Dateizugriff
  wurden auf der Zielplatine geprüft. Samba/USB/VLC wurden auf der
  Referenzinstallation separat geprüft.
- Die Zugangsdaten-Härtung ist offline geprüft: kein verwendbares
  Root-Passwort, keine SSH-Hostschlüssel, leere Maschinenidentität. Eigene
  Hostschlüssel entstehen vor dem ersten Start des SSH-Dienstes.
- **Die Android-eMMC wird durch den SD-Installationsweg nicht bereinigt oder
  beschrieben.** Eine spätere Nutzung als Datenlaufwerk erfordert eine eigene
  Einrichtung. Armbian-Boot von eMMC ist nicht der unterstützte Weg.
- WLAN, HDMI als Serverfunktion, Fernbedienung, zusätzliche Dauerlast- und
  Langzeitmessungen gehören nicht zur Basisabnahme. `clk_ignore_unused nohz=off`
  bleibt eine Diagnosekonfiguration.
- Gezielte Kernel-/Bootloader-Updates benötigen Backup und erneute Hardwareprüfung.
- Ein kompletter Durchlauf der neu geordneten Anleitung auf einer separaten SD
  ist noch offen; vorhandene Hardwaretests sind davon getrennt.

[Hilfe nach Symptomen](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/TROUBLESHOOTING.md) ·
[Testmatrix](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/blob/main/docs/VALIDATION.md)

## Download-Dateien

Der empfohlene Installer lädt die benötigten Dateien automatisch. Für die
manuelle Alternative genügen Image und zugehörige Image-Prüfsumme; der
komplette Satz enthält zusätzlich Entwickler- und Nachweisdateien:

- `T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz`
- `SHA256SUMS`
- `RELEASE-MANIFEST.txt`
- `HARDENING-METADATA.txt`
- `T95-H616-AXP313A-u-boot-sunxi-with-spl.bin`
- `T95-H616-AXP313A-tanix-6.18.dtb`

Persönliche Images, Passwortdaten, SSH-Schlüssel und SD-Backups bleiben privat.

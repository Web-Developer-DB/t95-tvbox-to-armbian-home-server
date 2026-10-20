# Changelog

## 2026-10-20

- USB-Status auf angeschlossene USB-Laufwerke konzentriert; interne SD/eMMC- und ZRAM-Geräte erscheinen nicht mehr als „Nicht verwaltet“.
- Vorgänge früherer Verbindungen und bereits abgeschalteter Geräte ausgeblendet; aktuelle Auswurffehler und Hinweise zu USB-Prüf-/Mountfehlern bleiben sichtbar. Gespeicherte Vorgänge werden nicht gelöscht.
- Leere USB-Übersicht ausdrücklich gekennzeichnet. Sechs zusätzliche Regressionstests; insgesamt 79 Modul-Tests bestanden.

## 2026-10-19

- Hardwarebestätigung bei `52b6be1`: exFAT-Auswurf/Power-off, Wiederanstecken und Samba-Lesen/-Schreiben. Historische Auswurfvorgänge zeigen jetzt ihre diskseq und werden von der aktuellen Verbindung unterschieden; 73 Modul-Tests bestanden.
- Hardwarebefund beim exFAT-Auswurf korrigiert: Freigabedefinitionen bleiben nach dem Entfernen des Mountordners lesbar; Bereinigung und Wiederaufnahme benötigen keinen existierenden Freigabepfad.
- Neue Freigaben werden einzeln durch Samba bestätigt. Fehlerhafte Definitionen verhindern keine Geräte-/Vorgangsdiagnose mehr; unvollständiger Status liefert weiterhin einen Fehlerstatus.
- Regressionstests bilden die Samba-Dateien und den verschwundenen Mountordner nach; erster Korrekturstand mit 70 Tests geprüft; spätere Hardwarebestätigung siehe oben.
- Gemeinsamer Python-Kern für Geräteidentität, atomare Zuordnungen und gesperrte Namensvergabe.
- Gerätebezogene udev-Sperre ersetzt das Stoppen des Automounters beim Auswurf.
- Auswurf aller Partitionen mit Btrfs-/FUSE-Zuordnung, Nachbarschutz und Wiederaufnahme nach Fehlern.
- Private Konfigurationssicherung und geprüfte Rücknahme; `--update` erhält Samba-Einstellungen/Passwörter.
- Lesendes `usb-eject --status`; automatisierte Regressionstests und getrennte offene Hardwarecheckliste.

## 2026-09-16

- README für den integrierten Home-Server-Pfad mit Installations-, Prüf-,
  Client-, VLC- und Rückbauanleitung vollständig überarbeitet.
- eMMC-Nutzung als internes ext4-Datenlaufwerk und der nicht erfolgreiche
  eMMC-Bootversuch in den Projektunterlagen klargestellt.
- Hauptprojekt-README um den bestätigten Samba-/USB-/VLC-Abnahmestatus ergänzt.
- GitHub-Veröffentlichungshinweise auf den tatsächlichen Modulpfad angepasst.
- Bevorzugten Client-Zugriff auf Samba-Serverwurzel `smb://SERVER-IP/` festgelegt.
- Statische `[USB]`-Sammelfreigabe entfernt.
- Dynamische Samba-Usershares pro USB-/SSD-Dateisystem eingeführt.
- Medien mit Label verwenden das bereinigte Label als Share-Name.
- Medien ohne Label verwenden `Extern-USB-1`, `Extern-USB-2`, ...
- Namenskollisionen werden mit `-2`, `-3`, ... aufgelöst.
- `t95-usb-share` über `udiskie` Event-Hook integriert.
- State-Mappings unter `~/.local/state/t95-usb-shares/` eingeführt.
- Doppel-Event-Fehler behoben: derselbe Mountpunkt erzeugt keinen zweiten Share mehr.
- Endlosschleife durch ungeeigneten `net usershare info`-Existenztest behoben.
- Überschreiben der Shell-Systemvariable `PATH` in beiden Skripten behoben.
- Sicheres Auswerfen um temporäres Stoppen/Starten von `udiskie` erweitert.
- Samba-`DeviceBusy` durch `smbcontrol smbd close-share` behoben.
- Reihenfolge korrigiert: Usershare/State werden erst nach erfolgreichem Unmount gelöscht.
- Vollständiger Test erfolgreich: Share entfernt, Mount weg, `/dev/sdX` nach Power-Off aus `lsblk` verschwunden; Wiedereinstecken erstellt Share automatisch neu.

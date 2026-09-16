# Changelog

## 2026-09-16

- README für den integrierten Home-Server-Pfad mit Installations-, Prüf-,
  Client-, VLC- und Rückbauanleitung vollständig überarbeitet.
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

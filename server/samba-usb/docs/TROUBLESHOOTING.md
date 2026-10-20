# 🔎 Samba-/USB-Fehlerhilfe

**Deutsch** | [English](TROUBLESHOOTING.en.md)

Zuerst prüfen, auf welcher Ebene der Fehler liegt. Diese Anleitung setzt die
[aktuelle Projektinstallation](../README.md) voraus.

| Beobachtung | Nächster Schritt |
| --- | --- |
| Laufwerk fehlt bereits in `lsblk` | Kabel, USB-Port, Versorgung und Kernelmeldungen prüfen. |
| Gerät sichtbar, aber nicht eingehängt | udiskie-/Kernelprotokoll, Dateisystemzustand und Auswurfsperre prüfen. |
| Eingehängt, aber Freigabe fehlt | Freigabe-Hook und Samba-Einstellungen prüfen. |
| Freigabe lesbar, Schreiben scheitert | Samba-Konto und tatsächliche Dateirechte prüfen; bei ext4 gelten vorhandene UID/GID/ACLs. |
| Auswurf fehlgeschlagen | Nicht abziehen; Status und betroffene Mounts prüfen, dann erneut auswerfen. |
| `Path is not a directory` nach Auswurf | Älteren Stand aktualisieren; bereits ausgehängter Mountordner konnte die Freigabebereinigung blockieren. Siehe unten. |

## 📋 Status sammeln

**Auf der T95, normaler SSH-Benutzer; die Befehle ändern keine Einstellungen:**

```bash
sudo usb-eject --status
lsblk -o NAME,TYPE,SIZE,FSTYPE,TRAN,MOUNTPOINTS
net usershare list
systemctl --user status udiskie.service --no-pager -l
sudo journalctl -t T95-USB-SHARE -b --no-pager -n 60
sudo journalctl -b -u udisks2.service --no-pager -n 60
sudo journalctl -k -b --no-pager -n 80
```

Fehlt das Benutzerjournal, systemweit nach der tatsächlichen UID suchen:

**Auf der T95, normaler SSH-Benutzer:**

```bash
sudo journalctl -b "_UID=$(id -u)" --no-pager -n 80
```

Protokolle können Seriennummern, UUIDs und Benutzernamen enthalten. Vor dem
öffentlichen Teilen prüfen. Eine leere Usershare-Liste ist ohne eingebundenen
USB-Datenträger korrekt; die feste `T95-DATA`-Freigabe wird dort nicht gelistet.

`usb-eject --status` konzentriert sich auf angeschlossene USB-Laufwerke und
Vorgänge ihrer aktuellen Verbindung. Interne SD/eMMC- und ZRAM-Geräte sowie
alte Auswurfvorgänge werden ausgeblendet. USB-Prüf- und Mountfehler bleiben
sichtbar. Für die vollständige Liste aller Blockgeräte den obigen `lsblk`-Befehl
verwenden. Fehlt ein USB-Gerät auch dort, zuerst Kabel, Stromversorgung und
Kernelmeldungen prüfen.

## 💾 Dateisystem und Zugriffsrechte

- ext4: Mounten und Schreibberechtigung sind getrennte Fragen. Rechte am Datenträger gezielt prüfen; keine pauschalen rekursiven Eigentümerwechsel.
- NTFS: `volume is dirty`, Hibernation oder Fast-Startup können das Einbinden verhindern. Daten sichern und separat eine passende Reparatur planen; das Skript erzwingt keinen Mount.
- Schreibgeschützte Datenträger bleiben schreibgeschützt. Die Statusanzeige prüft Zugriffsrechte als tatsächlicher Samba-Benutzer.
- Fehlt das Gerät in `lsblk`, kann der Freigabe-Hook es noch nicht verarbeiten. Das ist von einer fehlenden SMB-Freigabe zu unterscheiden.

## ⏏️ Auswurf bleibt unvollständig

Offene Dateien, VLC und Terminalfenster im USB-Ordner schließen. Den tatsächlichen
Freigabenamen wählen:

**Auf der T95, normaler SSH-Benutzer:**

```bash
read -r -p 'Freigabename des betroffenen USB-Laufwerks: ' T95_SHARE
```

Den Namen eingeben, Enter drücken. Dann im selben T95-Fenster:

```bash
sudo usb-eject "$T95_SHARE"
```

`failed` kann einen teilweise ausgeführten Vorgang bedeuten. Die Sperre bleibt
auf das betroffene Laufwerk begrenzt; andere Geräte werden weiter eingebunden.
Nicht manuell den gesamten Automounter stoppen oder die Sperrdatei löschen.
Nach erfolgreichem Auswurf abziehen und neu verbinden, wenn das Laufwerk wieder
benutzt werden soll. Auch ein Rechnerneustart hebt Laufzeitsperren auf.

### 🛠️ `Path is not a directory` nach dem Aushängen

Beim T95-Test von Revision `aef4e9f` konnte Samba nach Beginn des exFAT-Auswurfs
den Freigabepfad nicht mehr als Verzeichnis öffnen. `net usershare info` prüft
diesen Ordner und verhinderte dadurch die noch ausstehende Freigabebereinigung.
Auch die damalige Statusabfrage brach an dieser Stelle ab. Ein geöffnetes
Samba-Fenster allein erklärt diesen Fehler nicht.

Die Korrektur liest gespeicherte Usershare-Definitionen mit Prüfungen von
Verzeichnis, Eigentümer, Dateityp, Größe und Format; fehlende Mountordner
verhindern die Bereinigung nicht mehr. Geräteidentität und Mountgrenzen werden
weiter unabhängig geprüft. Neue Freigaben bestätigt Samba weiterhin einzeln.

Die Repository-Kopie aktualisieren und den
[Update-Modus](../README.md#vorhandene-einrichtung-aktualisieren) ausführen.
Das Laufwerk dabei angeschlossen lassen. Danach `sudo usb-eject --status`
aufrufen und den Auswurf mit dem bisherigen Freigabenamen wiederholen.
Das rootgeschützte Vorgangsprotokoll ermöglicht die Wiederaufnahme auch dann,
wenn der Update-Abgleich die veraltete Freigabe bereits entfernt hat.
Keine leeren Ersatz-Mountordner anlegen und keine Sperrdateien löschen.
Eine Abziehfreigabe gilt erst nach erfolgreichem Abschluss des erneuten Auswurfs.

## 🔄 Installation oder Update scheitert

`--update` erhält die Samba-Konfiguration. Meldet es fehlende Einstellungen,
die genannten Werte prüfen; keine komplette Neueinrichtung als ersten
Fehlerbehebungsversuch ausführen. Bei noch unbekannter Gruppe `sambashare` die
Box kontrolliert neu starten und den Aufruf wiederholen.

Private Sicherung und `state.json` liegen unter `/var/lib/t95-samba/installation-…/`.
`rolled-back` bestätigt die geprüfte Rücknahme; `rollback-failed` erfordert die
Prüfung der angegebenen Sicherung und Fehlermeldung. Sicherungen bleiben privat.

<!-- Compatibility anchors for older documentation links. -->
<a id="-auswurf-erfolgreich-prüfen"></a>
<a id="-command-not-found-für-rmloggerheadsync-innerhalb-eines-skripts"></a>
<a id="-devicebusy-beim-auswerfen"></a>
<a id="-doppelte-extern-usb-n-freigabe"></a>
<a id="-gerät-wird-direkt-nach-unmount-wieder-gemountet"></a>
<a id="-troubleshooting"></a>
<a id="-usb-wird-gemountet-aber-keine-samba-freigabe-erscheint"></a>
<a id="auswurf-erfolgreich-prüfen"></a>
<a id="command-not-found-für-rmloggerheadsync-innerhalb-eines-skripts"></a>
<a id="devicebusy-beim-auswerfen"></a>
<a id="doppelte-extern-usb-n-freigabe"></a>
<a id="gerät-wird-direkt-nach-unmount-wieder-gemountet"></a>
<a id="troubleshooting"></a>
<a id="usb-wird-gemountet-aber-keine-samba-freigabe-erscheint"></a>

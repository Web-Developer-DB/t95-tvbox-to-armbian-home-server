<a id="dateiserver-und-usb-laufwerke-auf-der-t95"></a>

# 📂 Dateiserver und USB-Laufwerke auf der T95

**Deutsch** | [English](README.en.md)

**USB einstecken und Dateien im Heimnetz teilen:** Reguläre Samba-Pakete erhalten
hier eine eigene Projektkonfiguration für die T95 und ihre USB-Anschlüsse.
Unterstützte USB-Sticks, SSDs und Festplatten werden automatisch eingebunden
und einzeln freigegeben. PC, Handy und VLC können darauf zugreifen.

**Beim Auswerfen eines Laufwerks bleiben die anderen nutzbar.** Der Automounter
läuft weiter und nimmt auch währenddessen neue USB-Geräte an.
Die feste Freigabe `T95-DATA` liegt beim empfohlenen Erststart auf der System-SD
unter `/srv/t95-sd-data/Share`; USB-Freigaben sind davon unabhängig.

| Dein Ziel | Hier geht es weiter |
| --- | --- |
| 🚀 Neuer Dateiserver | [Voraussetzungen](#voraussetzungen) → [Einrichten](#dateiserver-einrichten) |
| 🔄 Vorhandene Einrichtung aktualisieren | [Update ohne Ersatz der Samba-Konfiguration](#vorhandene-einrichtung-aktualisieren) |
| 📂 Dateien öffnen | [PC, Handy und VLC](#zugriff-von-clients-und-vlc) |
| ⏏️ Laufwerk abziehen | [Gezielt sicher auswerfen](#usb-sicher-auswerfen) |
| 🔎 Fehler verstehen | [Status und Fehlerhilfe](docs/TROUBLESHOOTING.md) |

> [!IMPORTANT]
> **Neue USB-Verwaltung vom 19.10.2026:** Die Auditkorrekturen sind automatisiert
> geprüft. Auf der T95 bestätigt sind das Update einer vorhandenen Einrichtung
> sowie Samba-Lesen/-Schreiben, Auswurf/Power-off und Wiedereinstecken eines
> exFAT-Sticks. Weitere Dateisystem- und Mehrgerätetests bleiben offen.
> [Prüfstand und Abnahme](../../docs/SAMBA_USB_AUDIT.md).

<a id="voraussetzungen"></a>

## 📋 Voraussetzungen

- T95 mit geprüftem Armbian, normalem SSH-Benutzer und `sudo`.
- [Kernel-/DTB-Sperre](../../docs/INSTALLATION.md#5-kernel-und-dtb-vor-updates-schützen) gesetzt; Internet für die Installation.
- ext4, exFAT, FAT32 oder NTFS auf gesundem USB-Datenträger. Bei ext4 gelten die vorhandenen Linux-Dateirechte weiter.
- Btrfs: nur ein physisches Laufwerk, auch mit Subvolumes. LUKS, LVM, RAID und Btrfs über mehrere Laufwerke sind nicht abgedeckt.
- Ausreichende Stromversorgung; Festplatten bei Bedarf extern versorgen.

Ein [SD-Backup](../../docs/BACKUP.md) ist optional. Der interne eMMC-Speicher wird
hier weder formatiert noch vorbereitet.

<a id="dateiserver-einrichten"></a>
<a id="schnellstart-reproduzierbare-wiederherstellung"></a>

## 🚀 Dateiserver einrichten

> [!WARNING]
> **Neueinrichtung ersetzt die Samba-Konfiguration nach einer privaten Sicherung.**
> Für eine vorhandene Einrichtung den [Update-Modus](#vorhandene-einrichtung-aktualisieren) verwenden.

**Auf der T95, normaler SSH-Benutzer; `sudo` wo angegeben:**

```bash
sudo apt update
sudo apt install -y git
git clone --branch main --depth 1 https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git
cd t95-tvbox-to-armbian-home-server/server/samba-usb
sha256sum -c MANIFEST.sha256
```

Erwartet: alle Prüfsummen `OK`. Bei einem vorhandenen Repository-Ordner zuerst
lokale Änderungen prüfen und eine aktuelle, geprüfte Kopie verwenden.

**Auf der T95, im selben Fenster, normaler SSH-Benutzer:**

```bash
export T95_USER="$(id -un)"
id "$T95_USER"
sudo T95_USER="$T95_USER" DATA_PATH=/srv/t95-sd-data/Share ./scripts/restore-samba-usb-setup.sh
```

Die `sudo`-Frage erwartet dein Linux-Passwort. Fehlt ein Samba-Konto, wird danach
ein eigenes Samba-Passwort abgefragt. Passworteingaben bleiben unsichtbar.
**Erfolg: `Fertig.`** Danach [Dateizugriff prüfen](#nach-der-installation-prüfen).

Meldet das Setup, dass der Benutzermanager die Gruppe `sambashare` noch nicht
kennt, wird kein Erfolg gemeldet und die Projektkonfiguration zurückgenommen.
Die Box kontrolliert neu starten und denselben Installationsaufruf wiederholen.
Bei aktivem Linger genügt ein neuer SSH-Login allein nicht.

<a id="vorhandene-einrichtung-aktualisieren"></a>

## 🔄 Vorhandene Einrichtung aktualisieren

**Voraussetzung:** aktuelle geprüfte Repository-Kopie; im Modulordner
`server/samba-usb`. Eigene Änderungen vor dem Aktualisieren der Kopie prüfen.

**Auf der T95, normaler SSH-Benutzer:**

```bash
sha256sum -c MANIFEST.sha256
sudo T95_USER="$(id -un)" ./scripts/restore-samba-usb-setup.sh --update
```

Erwartet: `Fertig. Bestehende Samba-Konfiguration erhalten.` Samba-Passwörter,
Datenpfad und eigene Samba-Freigaben bleiben erhalten. Fehlende notwendige
Samba-Einstellungen werden mit Korrekturhinweisen gemeldet. Der Update-Modus
ersetzt sie nicht automatisch. udiskie wird zur Übernahme seiner Einstellungen
neu gestartet; vorhandene Mounts werden mit den Freigaben abgeglichen.

<a id="nach-der-installation-prüfen"></a>

## ✅ Nach der Installation prüfen

**Auf der T95, normaler SSH-Benutzer:**

```bash
sudo usb-eject --status
net usershare list
```

Erwartet: aktiver Automounter und eine eigene Freigabe je unterstütztem,
eingebundenem USB-Dateisystem. Ohne USB darf die Usershare-Liste leer sein.
`T95-DATA` ist eine feste Samba-Freigabe und steht nicht in dieser Liste.

Die Laufwerksübersicht zeigt angeschlossene USB-Laufwerke; interne SD-Karte,
eMMC und ZRAM werden ausgeblendet. Vorgänge früherer Geräteverbindungen
erscheinen ebenfalls nicht mehr. Warnungen zu einem aktuell angeschlossenen
USB-Laufwerk bleiben sichtbar, auch wenn es nicht eingehängt werden konnte
oder der Auswurf blockiert ist. Die Statusanzeige allein gibt keine Freigabe
zum Abziehen; dafür den [Auswurfbefehl](#usb-sicher-auswerfen) verwenden.

<a id="zugriff-von-clients-und-vlc"></a>

## 📂 Zugriff von Clients und VLC

| Client | Adresse beziehungsweise Bedienung |
| --- | --- |
| Linux-Dateimanager | `smb://SERVER-IP/` |
| Windows-Explorer | `\\SERVER-IP\` |
| Handy / VLC | SMB-Netzwerkzugriff → Serveradresse → Freigabe wählen |

`SERVER-IP` durch die IP der Box ersetzen. Mit T95-Benutzername und
**Samba-Passwort** anmelden. In `T95-DATA` oder der gewählten USB-Freigabe eine
kleine eigene Testdatei schreiben und wieder öffnen. Eine schreibgeschützte
Freigabe oder fehlende ext4-Rechte wird durch das Setup nicht automatisch geändert.

<a id="usb-sicher-auswerfen"></a>

## ⏏️ USB sicher auswerfen

**Auf der T95, normaler SSH-Benutzer:**

```bash
net usershare list
read -r -p 'Freigabename des auszuwerfenden Laufwerks: ' T95_SHARE
```

Den tatsächlichen Namen aus der Liste eingeben und Enter drücken. Dann:

**Auf der T95, im selben Fenster, normaler SSH-Benutzer:**

```bash
sudo usb-eject "$T95_SHARE"
```

**Das gesamte zugehörige Laufwerk wird ausgeworfen, einschließlich seiner
weiteren Partitionen und Freigaben.** Andere physische Laufwerke bleiben nutzbar.

| Meldung | Bedeutung und nächster Schritt |
| --- | --- |
| `USB-Datenträger kann entfernt werden.` | Abschalten durch Geräteentfernung bestätigt; abziehen. |
| `Sicher ausgehängt; Hardware bleibt eingeschaltet. Du kannst das Laufwerk abziehen.` | Mounts und Freigaben entfernt; gezielte Wieder-Einhängesperre aktiv. Abziehen ist freigegeben. |
| `FEHLER: Auswurf unvollständig…` | Nicht abziehen. Status prüfen, offene Dateien/Terminalordner schließen und erneut versuchen. |

Bei einem Fehler können bereits einzelne Partitionen ausgehängt sein. Die
Sperre betrifft weiterhin nur dieses Laufwerk. Derselbe Aufruf kann einen
unterbrochenen Vorgang wieder aufnehmen. Nach erfolgreichem Aushängen bleibt
das Laufwerk bis zum Abziehen gegen automatisches Einbinden gesperrt.
Wiedereinstecken erzeugt wieder eine Freigabe; auch ein Rechnerneustart hebt
Laufzeitsperren auf.

<a id="einrichtung-zurücknehmen"></a>
<a id="konfiguration-wiederherstellen"></a>

## ↩️ Sicherung und Wiederherstellung

Vor Änderungen entsteht eine private Sicherung unter
`/var/lib/t95-samba/installation-…/` mit Einzelkopien und `state.json`.
Fehlschläge bei der Aktivierung stellen die gesicherten Projektdateien und
vorherigen Dienstzustände wieder her. Ein Fehler der Rücknahme bleibt sichtbar
als `rollback-failed`. Pakete, Gruppen und gemeinsames Linger können verbleiben.

Eine bewusste spätere Rückkehr zu einer älteren Einrichtung ist ein manueller
Administrationsschritt: zuerst die betreffende Sicherung und aktuelle Änderungen
prüfen. Das Modul bietet kein pauschales Deinstallations- oder Restore-Kommando.
Sicherungen können private Konfiguration enthalten und bleiben auf der Box.

<a id="was-richtet-das-samba-modul-ein"></a>
<a id="ergebnis-auf-einen-blick"></a>

## ⚙️ Technik und Grenzen

| Bestandteil | Aufgabe |
| --- | --- |
| Samba | Feste Datenfreigabe und dynamische, authentifizierte USB-Usershares |
| UDisks + udiskie | Einbinden unterstützter Geräte; ausdrücklich gewählte Projektkonfiguration |
| Gemeinsamer Python-Kern | Geräteidentität, Namenssperren, atomare JSON-Zuordnungen und Auswurf |
| udev-Auswurfsperre | Nur die aktuelle Verbindung des gewählten Laufwerks zurückhalten |

`T95_USER`, `DATA_PATH` und `NETBIOS_NAME` dienen der Neueinrichtung.
`DATA_PATH` verwendet ohne Angabe `/srv/T95-DATA/Share`; ohne dortigen eMMC-Mount
liegt auch dieser Pfad auf der SD. Der empfohlene Aufruf setzt deshalb einen
eindeutigen SD-Pfad. `--update` erhält den vorhandenen Samba-Datenpfad.
Es gibt keine automatische Dateisystemreparatur, Formatierung, Force-Mounts oder
rekursiven Änderungen vorhandener Dateirechte.

[Technische Referenz](docs/SAMBA-USB-SETUP.md) · [Fehlerhilfe](docs/TROUBLESHOOTING.md) ·
[Abnahmecheckliste](docs/RESTORE-CHECKLIST.md) · [Audit und Testgrenzen](../../docs/SAMBA_USB_AUDIT.md)

<!-- Compatibility anchors for older documentation links. -->
<a id="-einrichtung-zurücknehmen"></a>
<a id="-ergebnis-auf-einen-blick"></a>
<a id="-konfiguration-wiederherstellen"></a>
<a id="-sicherheit-und-veröffentlichung"></a>
<a id="-was-richtet-das-samba-modul-ein"></a>
<a id="-weiterführende-dokumentation"></a>
<a id="1-modul-beziehen-und-manifest-prüfen"></a>
<a id="2-linux-benutzer-und-netzwerk-prüfen"></a>
<a id="3-installation-ausführen"></a>
<a id="die-mitgelieferten-skripte"></a>
<a id="einrichtung-anpassen"></a>
<a id="einstellungen-später-ändern"></a>
<a id="getestete-referenzplattform"></a>
<a id="sicherheit-und-veröffentlichung"></a>
<a id="t95-samba--usb-automount"></a>
<a id="usb-datenträger-anschließen"></a>
<a id="weiterführende-dokumentation"></a>
<a id="welchen-speicherort-soll-ich-wählen"></a>

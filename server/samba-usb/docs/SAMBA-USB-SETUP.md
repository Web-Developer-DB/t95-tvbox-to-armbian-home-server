# ⚙️ Technische Referenz: Samba und USB

**Deutsch** | [English](SAMBA-USB-SETUP.en.md)

Für neue Nutzer ist die [Modulanleitung](../README.md) der verbindliche Ablauf.
Diese Referenz beschreibt die Implementierung vom 19.10.2026. Manuelle Schritte
aus früheren Fassungen sind durch den Installer beziehungsweise `--update` ersetzt.

| Ebene | Aufgabe |
| --- | --- |
| Samba | Feste `T95-DATA`-Freigabe plus einzelne USB-Usershares |
| UDisks / udiskie | Dateisysteme mounten und Ereignisse melden |
| Gemeinsamer Python-Kern | Gerätezuordnung, Freigaben, Status, gezielter Auswurf |
| udev | Wieder-Einhängen ausschließlich des ausgeworfenen Laufwerks verhindern |

## 📦 Installation und Aktualisierung

Der Installer prüft das gesamte Paketmanifest vor APT. Er sichert zu ersetzende
Dateien und den Dienstzustand privat unter `/var/lib/t95-samba/installation-…/`.
Die Paketinstallation benötigt zusätzlich Python 3 mit `python3-dbus`, udev und
util-linux. Der installierte Kern liegt unter `/usr/local/lib/t95-usb/`.

`T95_USER` bezeichnet einen vorhandenen normalen Linux-Benutzer; dessen UID und
primäre GID werden ermittelt. `DATA_PATH` und `NETBIOS_NAME` ändern die
Neueinrichtung. Der Standarddatenpfad ist `/srv/T95-DATA/Share`; der empfohlene
SD-Weg setzt ausdrücklich `/srv/t95-sd-data/Share`.

`--update` erhält Samba-Konfiguration, Passwörter, Datenpfad und eigene feste
Freigaben. Es prüft die notwendigen Usershare-Einstellungen und meldet fehlende
Werte. Eine vorhandene `config.yml` bleibt erhalten; der Dienst startet gezielt
mit `--config=%h/.config/udiskie/config.json`.

Nach `daemon-reload`, Aktivierung und kontrolliertem udiskie-Neustart werden
vorhandene Mounts abgeglichen. Ein veralteter Gruppensatz des Benutzermanagers
verhindert einen falschen Installationserfolg. Die Fehlermeldung verlangt dann
einen kontrollierten Neustart und einen erneuten Aufruf.

## 🧩 Freigaben und Status

Eine kurze gemeinsame Sperre schützt Namensvergabe, Anlage und Statusänderung.
Das Label wird zu einem zulässigen Namen bereinigt; ohne Label werden Namen
wie `Extern-USB-1` verwendet. Gleiche Namen erhalten Zähler. Feste Freigaben und
Namen noch angeschlossener ausgeworfener Geräte sind reserviert.

Zuordnungen liegen als atomar geschriebene JSON-Dateien unter
`~/.local/state/t95-usb-shares/`. Sie enthalten Schema-Version, Freigabe,
Mountpunkt, Partition und aktuelle Geräteidentität. Alte `.map`-Dateien werden
nur bei bestätigter aktueller Zuordnung übernommen. Keine Datei wird als
Shellcode geladen. Fehler einer Geräte- oder Samba-Abfrage gelten nicht als
leeres Ergebnis.

Der Hook gleicht beim Start und bei Geräteereignissen den tatsächlichen
Mountzustand ab. Doppelte Ereignisse erzeugen keine zweite Freigabe. Neue
Freigaben werden bei fehlgeschlagener Statusspeicherung wieder entfernt oder
als reparaturbedürftig protokolliert.

## ⏏️ Gezielter Auswurf

`usb-eject` ermittelt aus einer Freigabe das gesamte physische USB-Laufwerk.
Die Bootkennung, der kanonische sysfs-Pfad und `diskseq` verhindern eine
Verwechslung mit wiederverwendeten Gerätenamen. System-/fremde Mounts, Swap und
nicht unterstützte Speicheraufbauten verhindern den Auswurf.

Vor dem Aushängen entsteht eine rootverwaltete Sperre unter `/run/t95-usb/`.
Die udev-Regel setzt `UDISKS_IGNORE=1` und `UDISKS_AUTO=0` für dieses Gerät und
seine Partitionen. UDisks muss die Sperre bestätigen; laufende Geräteaufträge
müssen beendet sein. **udiskie bleibt während des Auswurfs aktiv.**

Alle zugehörigen Samba-Verbindungen werden geschlossen. Die Dateisysteme werden
synchronisiert und Mountpunkte von innen nach außen ausgehängt. Btrfs und
FUSE-NTFS können anonyme Mount-Gerätenummern besitzen; die Blockquelle wird
deshalb zusätzlich ausgewertet. Erst nach bestätigtem Aushängen werden die
zugehörigen Freigaben und Zuordnungen entfernt.

Power-off erfolgt nur bei bestätigter Unterstützung und ohne gefährdete
Nachbarlaufwerke eines Mehrfachgeräts. Fehlt diese Möglichkeit, genügt eine
bestätigte Aushängung mit wirksamer Sperre für die Freigabe zum Abziehen.
Andere Abschaltfehler führen zu einem Fehlerstatus.

Die Sperre bleibt bis zum Abziehen beziehungsweise Rechnerneustart bestehen.
Ein udiskie-Neustart hebt sie nicht auf. Neue Geräteverbindungen übernehmen
keine alte Sperre. Auswurfprotokolle in `/run/t95-usb/operations/` sind privat;
Freigabenreservierungen sind lesbar, aber nur durch root veränderbar.

## 🔎 Diagnose und Rücknahme

**Auf der T95, normaler SSH-Benutzer:**

```bash
sudo usb-eject --status
sudo journalctl -t T95-USB-SHARE -b --no-pager -n 60
systemctl --user status udiskie.service --no-pager -l
```

Status zeigt Geräte, Dateisysteme, Mounts, Benutzerrechte, Freigaben, Sperren und
fehlgeschlagene Auswürfe. Exitstatus: `0` bestätigter Erfolg, `1` Betriebsfehler,
`2` ungültiger Aufruf. Bei Auswurffehlern können einzelne Partitionen bereits
ausgehängt sein; den Status prüfen und den gleichen Aufruf wiederholen.

Bei Installationsfehlern werden gesicherte Projektdateien und vorherige
Dienstzustände automatisch wiederhergestellt und geprüft. Misslingt dies,
bleibt `rollback-failed` mit Sicherungspfad sichtbar. Pakete, Gruppen und Linger
können erhalten bleiben. Eine spätere manuelle Wiederherstellung erfordert die
Prüfung des jeweiligen privaten Journals und zwischenzeitlicher Änderungen.

## 🧪 Nachweise und Grenzen

[Audit mit Korrekturstatus](../../../docs/SAMBA_USB_AUDIT.md) ·
[Hardware-Abnahme](RESTORE-CHECKLIST.md) · [Fehlerhilfe](TROUBLESHOOTING.md)

Unterstützt: ext4, exFAT, FAT32, NTFS und Btrfs auf einem einzelnen Laufwerk.
Linux-Dateirechte, Treiber und der Zustand des Mediums gelten weiterhin.
Automatische Reparatur, Formatierung, Force-Unmount und rekursive Rechteänderung
sind nicht Bestandteil des Moduls. Die Hardwarebestätigung der neuen Version
ist noch offen.

<!-- Compatibility anchors for older documentation links. -->
<a id="-1-zielbild"></a>
<a id="-10-dynamisches-share-skript"></a>
<a id="-11-sicheres-auswerfen"></a>
<a id="-12-vollständig-validierter-auswurf-test"></a>
<a id="-13-unterstützte-namenslogik"></a>
<a id="-14-gefundene-und-behobene-fehler"></a>
<a id="-15-tests-nach-wiederherstellung"></a>
<a id="-16-client-zugriff"></a>
<a id="-17-was-nicht-ins-öffentliche-github-repository-gehört"></a>
<a id="-2-relevanter-serverzustand"></a>
<a id="-3-benötigte-pakete"></a>
<a id="-4-samba-benutzer-und-usershare-gruppe"></a>
<a id="-5-samba-konfiguration"></a>
<a id="-6-interne-t95-data-berechtigungen"></a>
<a id="-7-udiskspolkit-usb-ohne-passwort-mounten-und-auswerfen"></a>
<a id="-8-udiskie-als-dauerhafter-benutzer-service"></a>
<a id="-9-udiskie-event-hook"></a>
<a id="-vollständige-dokumentation-samba--dynamische-usb-freigaben-auf-t95armbian"></a>
<a id="1-zielbild"></a>
<a id="10-dynamisches-share-skript"></a>
<a id="11-sicheres-auswerfen"></a>
<a id="12-vollständig-validierter-auswurf-test"></a>
<a id="13-unterstützte-namenslogik"></a>
<a id="14-gefundene-und-behobene-fehler"></a>
<a id="15-tests-nach-wiederherstellung"></a>
<a id="16-client-zugriff"></a>
<a id="17-was-nicht-ins-öffentliche-github-repository-gehört"></a>
<a id="2-relevanter-serverzustand"></a>
<a id="3-benötigte-pakete"></a>
<a id="4-samba-benutzer-und-usershare-gruppe"></a>
<a id="5-samba-konfiguration"></a>
<a id="6-interne-t95-data-berechtigungen"></a>
<a id="7-udiskspolkit-usb-ohne-passwort-mounten-und-auswerfen"></a>
<a id="8-udiskie-als-dauerhafter-benutzer-service"></a>
<a id="9-udiskie-event-hook"></a>
<a id="fehler-1-endlosschleife-bei-usershare-prüfung"></a>
<a id="fehler-2-shell-systemvariable-path-überschrieben"></a>
<a id="fehler-3-doppelte-freigaben-bei-mehrfachem-event"></a>
<a id="fehler-4-sofortiges-remount-nach-unmount"></a>
<a id="fehler-5-devicebusy-durch-samba"></a>
<a id="fehler-6-usershare-zu-früh-gelöscht"></a>
<a id="medium-mit-label"></a>
<a id="medium-ohne-label"></a>
<a id="user-service"></a>
<a id="vollständige-dokumentation-samba--dynamische-usb-freigaben-auf-t95armbian"></a>
<a id="warum-keine-usb-sammelfreigabe"></a>
<a id="warum-smbcontrol-smbd-close-share"></a>
<a id="warum-udiskie-vorübergehend-stoppen"></a>
<a id="wichtige-eigenschaft-idempotenz"></a>

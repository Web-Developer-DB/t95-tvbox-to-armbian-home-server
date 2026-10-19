<a id="samba-usb-audit-vom-19102026"></a>

# 🔎 Samba-/USB-Audit vom 19.10.2026

**Deutsch** | [English](SAMBA_USB_AUDIT.en.md)

Untersucht: Repository-Stand `4f97a5d`, insbesondere Samba-Installation,
udiskie-Konfiguration, Event-Hook, sichere Entfernung und Audio-Rücknahme.
Quellprüfung und isolierte Simulationen ersetzen keinen Datenträgertest.

> [!IMPORTANT]
> **Ergebnis:** Der normale Ablauf ist nachvollziehbar, Fehlerpfade und
> gleichzeitige Ereignisse sind aber nicht durchgehend abgesichert. Eine
> Zusage „funktioniert mit jedem Dateisystem“ wäre nicht gerechtfertigt.
> Die folgenden Samba-Befunde sind offen; dieser Audit ändert die USB-Skripte nicht.

[Samba einrichten](../server/samba-usb/README.md) · [Fehlerhilfe](TROUBLESHOOTING.md#usb-laufwerk-fehlt-oder-ist-belegt)

<a id="fehler-nach-ebene-unterscheiden"></a>

## 🧭 Fehler nach Ebene unterscheiden

| Beobachtung | Zuerst untersuchen |
| --- | --- |
| Datenträger fehlt in `lsblk` | USB-/Blockgeräteerkennung, Kabel, Versorgung, Kernel und vorheriges Power-off |
| Datenträger sichtbar, Mount fehlt | udiskie/UDisks, Kernel-Treiber, Dateisystemzustand und Mountfehler |
| Mount vorhanden, Freigabe fehlt | Event-Hook, Benutzergruppe, Konfiguration und Usershare-Erstellung |
| Freigabe vorhanden, Schreiben scheitert | Samba-Anmeldung sowie tatsächliche Unix-/Dateisystemrechte |

Im begleitenden Diagnosefall verweigerte `ntfs3` den Mount eines als „dirty“
markierten NTFS-Volumes. Ein zweites exFAT-Volume war eingehängt. Das ist kein
Nachweis über den separat gemeldeten ext4-Datenträger. Unsauberer Zustand kann
unterschiedliche Ursachen haben; aus diesen Meldungen lässt sich die Ursache
seiner Entstehung nicht ableiten. Die [Kernel-Dokumentation](https://docs.kernel.org/filesystems/ntfs3.html)
rät vom erzwungenen NTFS-Mount ab. Reparaturen gehören in einen gesonderten
Schritt mit Datensicherung und eindeutig identifiziertem Medium.

<a id="offene-samba-usb-befunde"></a>

## 🛠️ Offene Samba-/USB-Befunde

| Priorität | Befund | Auswirkung und Korrekturvorschlag |
| --- | --- | --- |
| Hoch | `usb-eject` behandelt jeden Power-off-Fehler als „nicht unterstützt“ | Nach Neustart von udiskie kann das noch angeschlossene Medium erneut gemountet werden, obwohl die Meldung das Abziehen freigibt. Fehler unterscheiden, Mounts abschließend prüfen und Remount bis zum Abziehen verhindern. |
| Hoch | Fehler der Geräteauflistung gehen in einer Prozesssubstitution verloren | Schlägt `lsblk` bei der Ermittlung der Partitionen fehl, kann die Schleife leer bleiben. Trotzdem werden Freigabe/State gelöscht und später eine Erfolgsmeldung ausgegeben. Auflistung und Exitstatus zuerst prüfen. |
| Hoch | Neustart des Automounters wird mit `|| true` verschluckt | Das Skript kann erfolgreich enden, obwohl udiskie gestoppt bleibt. Nachfolgende Datenträger werden dann nicht automatisch gemountet. Neustartstatus prüfen und klar melden. |
| Mittel | Kein gemeinsames Lock für Freigabenamen und State-Dateien | Zwei zeitgleiche Mount-Ereignisse können denselben freien Namen auswählen; `net usershare add` ersetzt dann eine Zuordnung. Namensvergabe, Anlage und State-Schreiben serialisieren. |
| Mittel | udiskie wird ohne festen Konfigurationspfad gestartet | Eine vorhandene `config.yml` hat Vorrang vor der installierten `config.json`. Dadurch können Automount und Hook anders konfiguriert sein. Projektdatei explizit auswählen und vorhandene Konfiguration vorher sichern. |
| Mittel | `enable --now` lädt eine bereits laufende udiskie-Instanz nicht neu | Nach erneutem Setup kann der alte Prozess mit alter Konfiguration weiterlaufen. Kontrolliert neu starten und vorhandene Mounts abgleichen. |
| Mittel | Fehlgeschlagene Samba-Abfrage verhindert den vorgesehenen State-Fallback | Mit `set -e` und `pipefail` bricht `MOUNTPOINT=...` bei einem Abfragefehler vorher ab. Fehler explizit behandeln. Eine erfolgreiche Abfrage ohne Treffer ist davon zu unterscheiden. |
| Mittel | Btrfs-Subvolume-Quelle wird als Gerätename übernommen | `findmnt` liefert beispielsweise `/dev/sda1[/@]`; `lsblk` kann das nicht als Blockgerät verwenden. Gerät über `--nofsroot` beziehungsweise eine eindeutige Geräteidentität bestimmen. |

Betroffene Stellen:

- [usb-eject](../server/samba-usb/scripts/usb-eject): Samba-Abfrage 46–50,
  Quellgerät 87–102, Neustart 125–130, Partitionen 144–161, Power-off 181–194.
- [t95-usb-share](../server/samba-usb/scripts/t95-usb-share): Namensvergabe
  122–157; Cleanup und State-Schreiben besitzen keine gemeinsame Sperre.
- [udiskie-Dienst](../server/samba-usb/config/systemd-user/udiskie.service):
  Startaufruf ohne `--config`.
- [Samba-Installer](../server/samba-usb/scripts/restore-samba-usb-setup.sh):
  Konfiguration wird kopiert, danach nur `enable --now` aufgerufen.

Der [udiskie-Quellstand 2.5.7](https://github.com/coldfix/udiskie/tree/v2.5.7)
bestätigt die YAML-Priorität, nebenläufige Event-Hooks und das Mounten verfügbarer
Medien beim Start. Die Simulation des Remounts bildet dieses Verhalten nach.
Die tatsächliche Häufigkeit auf der T95 wurde nicht gemessen.

<a id="grenzen-nach-dateisystem"></a>

## 💾 Grenzen nach Dateisystem

| Typ | Einordnung |
| --- | --- |
| ext4 | Kein expliziter Ausschluss im Hook. Gespeicherte UID/GID, Modus und ACLs gelten weiterhin; eine Samba-Freigabe erteilt keine zusätzlichen Unix-Rechte. Der gemeldete sporadische Mountfehler ist ohne zugehörige Logs offen. |
| exFAT / FAT | Treiber und Dateisystemzustand entscheiden über den Mount. Besitzer-/Maskenoptionen unterscheiden sich von ext4; Dateigrößen- und Namensgrenzen bleiben bestehen. |
| NTFS | UDisks kann `ntfs3` trotz installiertem `ntfs-3g` auswählen. „dirty“ oder nicht sauber beendeter Zustand darf nicht pauschal durch Force-Mount übergangen werden. |
| Btrfs mit Subvolume | Mount kann funktionieren; der aktuelle Auswurfpfad verarbeitet die Quellenangabe nicht zuverlässig. |
| LUKS, LVM, RAID, andere Gerätepfade | `/dev/mapper/*` und `/dev/dm-*` werden vom Hook nicht akzeptiert. Entsperren, Mapper-Auflösung und komplexe Laufwerkstopologien sind kein zugesicherter Funktionsumfang. |

UDisks beschreibt die [dateisystemspezifischen Mountoptionen](https://storaged.org/udisks/docs/mount_options.html).
Samba dokumentiert, dass die [Unix-Rechte die Freigaberechte begrenzen](https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html).
Weder automatische Eigentümerwechsel noch rekursives `chmod` sind eine allgemeine Lösung.

<a id="audio-rücknahme-separat-korrigiert"></a>

## 🎧 Audio-Rücknahme: separat korrigiert

Die alte Rücknahme ignorierte einzelne Dienstfehler und setzte Dienste still,
anstatt alle vorherigen Zustände wiederherzustellen. Ein systemweit aktivierter
Benutzerdienst kann außerdem trotz lokalem `disable` später erneut starten;
dieses Verhalten ist in der [systemd-Dokumentation](https://www.freedesktop.org/software/systemd/man/256/systemctl.html) beschrieben.

Die überarbeitete [Audio-Einrichtung](../server/bluetooth/README.md) sichert
Konfiguration vor APT und stellt die vorherigen Dienstzustände wieder her.
Ein vorher aktiver `mpris-proxy` darf bei diesem ausdrücklich gewählten
Rücknahmemodus wieder aktiv sein. Das ist von einer vollständigen Entfernung
auch vorher vorhandener Audiopakete zu unterscheiden. Ein neuer Hardwaretest
der geänderten Rücknahme bleibt offen.

<a id="prüfverfahren-und-aussagegrenzen"></a>

## 🧪 Prüfverfahren und Aussagegrenzen

- Drei Samba-Shellskripte bestehen `bash -n`; udiskie-JSON ist syntaktisch gültig.
- Alle 20 Samba- und 14 Dashboard-Prüfsummen stimmten beim Audit des Ausgangsstands.
- Die vorhandenen 16 Setup-Tests bestanden; sie testeten Dashboard/Bluetooth,
  keinen echten Samba-Dateizugriff und keine Dateisystemmatrix.
- 13 isolierte Auditfälle bestätigten normale und blockierte Auswürfe,
  wiederholte Events sowie die beschriebenen simulierten Fehlerpfade.
  „Erfolgreich reproduziert“ bedeutet hier, dass das Fehlverhalten nachgewiesen
  wurde; es bedeutet nicht, dass diese USB-Fehler behoben sind.
- Echte `findmnt`-Ausgabe aus einer temporären Mountinfo-Datei bestätigte den
  Btrfs-Suffix. Keine Partition wurde dafür eingehängt.
- Keine Formatierung, Reparatur, Paketinstallation oder Dienständerung auf dem
  Entwicklungs-PC oder der T95 wurde für diese Simulationen ausgeführt.

Für Hardware-Abnahme erforderlich: lesender und schreibender Clientzugriff je
Dateisystem, mehrere Partitionen, gleichzeitige Geräteereignisse, Auswurf bei
offenen Dateien, nicht unterstütztes Power-off, Neustart und erneutes Anstecken.

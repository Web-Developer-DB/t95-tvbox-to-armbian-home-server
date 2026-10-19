<a id="samba-usb-audit-vom-19102026"></a>

# 🔎 Samba-/USB-Audit vom 19.10.2026

**Deutsch** | [English](SAMBA_USB_AUDIT.en.md)

Untersucht: Repository-Stand `4f97a5d`, insbesondere Samba-Installation,
udiskie-Konfiguration, Event-Hook, sichere Entfernung und Audio-Rücknahme.
Quellprüfung und isolierte Simulationen ersetzen keinen Datenträgertest.

> [!IMPORTANT]
> **Korrekturstand 19.10.2026:** Alle acht Befunde sind im Code bearbeitet und
> durch automatisierte Tests abgesichert. Der Auswurf arbeitet jetzt je Laufwerk;
> udiskie bleibt aktiv. **Die Hardware-Abnahme hat begonnen; der vollständige
> Durchlauf steht noch aus.** Update und exFAT-Status sind als Teilabnahme bestätigt.
> Der anschließende exFAT-Auswurf deckte einen weiteren Fehler bei fehlendem
> Mountordner auf. Bei `52b6be1` sind korrigierter Auswurf/Power-off, erneutes
> Einbinden und tatsächlicher Samba-Lese-/Schreibzugriff für den exFAT-Stick bestätigt.
> Der ursprüngliche sporadische ext4-Fehler ist damit noch nicht auf echter
> Hardware als behoben nachgewiesen.

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

## 🛠️ Samba-/USB-Befunde und Korrekturstand

| Ausgangsbefund | Korrektur im Code | Automatisiert | Hardware |
| --- | --- | --- | --- |
| Power-off-Fehler wird als fehlende Unterstützung behandelt | Fehlertypen unterscheiden; gerätebezogene Sperre und abschließende Zustandsprüfung | Bestanden | Offen |
| Fehler der Geräteauflistung geht verloren | Strukturierte Auflistung; Fehler und leere Ergebnisse verhindern ungesicherte Schritte | Bestanden | Offen |
| Automounter-Neustartfehler wird unterdrückt | Stoppen/Starten aus dem Auswurf entfernt; andere Geräte laufen weiter | Bestanden | Offen |
| Gleichzeitige Freigabenamen kollidieren | Gemeinsame kurze Sperre, Namensreservierung und atomare JSON-Zuordnungen | Bestanden | Offen |
| YAML übersteuert Projekt-JSON | Dienst wählt die Konfigurationsdatei ausdrücklich; vorhandene Dateien werden gesichert | Bestanden | Offen |
| Erneutes Setup lädt laufenden Dienst nicht neu | Kontrollierter Neustart und Abgleich bereits gemounteter Geräte | Bestanden | Teilweise: Update, aktiver Dienst und exFAT-Freigabe bestätigt |
| Samba-Abfrage verhindert State-Fallback | Fehler ausdrücklich melden; nur validierte aktuelle Zuordnungen verwenden | Bestanden | Offen |
| Btrfs-Subvolume-Quelle ist kein Blockgerätename | Blockquelle ohne FSROOT-Suffix auswerten; auch anonyme Btrfs-/FUSE-Mount-Gerätenummern berücksichtigen | Bestanden | Offen |

Zusätzlich abgesichert: alle Partitionen/Freigaben eines physischen Laufwerks,
Unterbrechungen und Wiederaufnahme, wiederverwendete Gerätenamen, Schutz fremder
Mounts und Nachbarlaufwerke von Mehrfachgeräten. Freigabenamen bleiben während
eines Auswurfs reserviert. Doppelte Ereignisse schreiben unveränderte Zuordnungen
nicht erneut auf die SD.

Maßgeblich sind der [gemeinsame Kern](../server/samba-usb/lib/t95_usb.py),
der [Installer](../server/samba-usb/lib/t95_install.py), die
[udev-Regel](../server/samba-usb/config/udev/99-t95-usb-eject.rules) und die
[Regressionstests](../server/samba-usb/tests/test_usb.py).
Die bisherigen Shell-Aufrufe bleiben als Einstieg erhalten.

Der [udiskie-Quellstand 2.5.7](https://github.com/coldfix/udiskie/tree/v2.5.7)
bestätigt die zugrunde liegende Auswahl von Konfiguration und Gerätehinweisen.
Die neue gerätebezogene Sperre muss auf der T95 noch praktisch abgenommen werden.

<a id="grenzen-nach-dateisystem"></a>

## 💾 Grenzen nach Dateisystem

| Typ | Einordnung |
| --- | --- |
| ext4 | Kein expliziter Ausschluss im Hook. Gespeicherte UID/GID, Modus und ACLs gelten weiterhin; eine Samba-Freigabe erteilt keine zusätzlichen Unix-Rechte. Der gemeldete sporadische Mountfehler ist ohne zugehörige Logs offen. |
| exFAT / FAT | Treiber und Dateisystemzustand entscheiden über den Mount. Besitzer-/Maskenoptionen unterscheiden sich von ext4; Dateigrößen- und Namensgrenzen bleiben bestehen. |
| NTFS | UDisks kann `ntfs3` trotz installiertem `ntfs-3g` auswählen. „dirty“ oder nicht sauber beendeter Zustand darf nicht pauschal durch Force-Mount übergangen werden. |
| Btrfs mit Subvolume | Blockquelle und anonyme Mount-Gerätenummer werden berücksichtigt. Unterstützt ist ein einzelnes physisches Laufwerk; Hardware-Abnahme offen. |
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

**Ausgangsaudit bei `4f97a5d`, vor den Korrekturen:** Die folgenden Nachweise betreffen die ursprüngliche Untersuchung. Die aktuellen Regressionsergebnisse stehen getrennt darunter.

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

<a id="abnahme-der-neuen-usb-verwaltung"></a>

## ✅ Abnahme der neuen USB-Verwaltung

- **73 automatisierte Modul-Tests bestanden**: Freigaben/Auswurf, Parser und Update-/Rollback-Fixtures, einschließlich 15 zusätzlicher Fälle nach dem Hardwarebefund und drei Tests zur Statuszuordnung früherer Verbindungen. Zusätzlich bestehen 37 Setup-Tests einschließlich der neuen USB-Dashboard-Hilfe.
- **udev-Regel syntaktisch geprüft**; die Sperrprüfung wurde beim bestätigten exFAT-Auswurf durchlaufen. Weitere Persistenz-/Mehrgerätefälle bleiben offen.
- **Simulationen verändern keine echten Datenträger oder Dienste.** Sie verwenden temporäre Verzeichnisse und System-Doubles.
- **Teilabnahme auf T95 bei `aef4e9f`:** Update einer vorhandenen Einrichtung erfolgreich; private Sicherung angelegt, Samba-Konfiguration einschließlich eigener fester Freigaben unverändert, Automounter aktiv und vorhandene exFAT-Freigabe mit positiven Benutzerrechte-Prüfungen erkannt. Nachweis: vom Projektbetreiber übermittelte Terminalausgabe vom 19.10.2026; noch kein Datei-/SMB-Zugriff oder Auswurf. [Details und Grenzen](VALIDATION.md#-neue-samba-usb-verwaltung--19102026).
- **Anschließender Auswurf bei `aef4e9f` fehlgeschlagen:** `net usershare info` verweigert die Abfrage, wenn es den Freigabepfad nicht mehr als Verzeichnis öffnen kann. Dadurch blieben Bereinigung und Status hängen; der Fehler trat auch ohne offenes Samba-Fenster auf. Die bisherige reine Dictionary-Simulation der Freigaben bildete diese Samba-Prüfung nicht nach. Neue dateibasierte CLI-Fixtures reproduzieren den Fehler mit verschwundenem Mountordner.
- **Korrektur dieses zusätzlichen Befunds:** Eigentümer-/Format-geprüfte Usershare-Definitionen unabhängig vom Mountziel lesen; neue Freigaben gezielt durch Samba bestätigen; Geräte-/Vorgangsstatus trotz Definitionsfehler ausgeben und unvollständige Abfragen weiterhin als Fehler melden. Keine Ersatzverzeichnisse oder pauschal ignorierten Abfragefehler. Wiederaufnahme nach Update-Abgleich automatisiert geprüft und im unten genannten exFAT-Hardwarefall bestätigt. Die zugrunde liegende Pfadprüfung steht im [Samba-Parser](https://github.com/samba-team/samba/blob/samba-4.22.4/source3/param/loadparm.c), die Verwendung durch Info/List im [Usershare-Kommando](https://github.com/samba-team/samba/blob/samba-4.22.4/source3/utils/net_usershare.c).
- **Hardware-Wiederholung bei `52b6be1` bestanden:** Der angefangene exFAT-Auswurf wurde nach Update fortgesetzt, die Freigabe bereinigt und Power-off bestätigt (`powered-off`, LED aus). udiskie blieb aktiv. Wiedereinstecken ergab eine neue diskseq ohne Sperre und wieder eine Freigabe. Samba-Lesen/-Schreiben wurde vom Projektbetreiber bestätigt; ein gesonderter Inhaltsvergleich fehlt. Die Statusanzeige kennzeichnet historische Vorgänge jetzt anhand ihrer diskseq.
- **Hardware offen:** Inhaltsvergleich beim exFAT-Stick; Client lesen/schreiben und Auswurf für ext4, FAT32 und NTFS; Btrfs-Subvolumes; 20 ext4-Ansteck-/Auswurfzyklen; Mehrgerätebetrieb an beiden Ports und mit Hub; nicht unterstütztes Power-off und weitere Unterbrechungsfälle.

Die [Abnahmecheckliste](../server/samba-usb/docs/RESTORE-CHECKLIST.md) hält diese
Punkte getrennt fest. Erst nach tatsächlicher Durchführung wird ein Hardwarefall
als bestanden eingetragen. [Update-Anleitung](../server/samba-usb/README.md#vorhandene-einrichtung-aktualisieren).

<a id="-offene-samba-usb-befunde"></a>

# ✅ Hardware-Abnahme: neue Samba-/USB-Verwaltung

**Deutsch** | [English](RESTORE-CHECKLIST.en.md)

**Teilabnahme begonnen:** Diese Liste gilt für die Implementierung vom 19.10.2026.
Frühere Hardwarebestätigungen erfüllen sie nicht. Separate Datenträger mit
gesicherten Daten verwenden. Formatieren oder Reparieren gehört nicht zur Abnahme.

**Bestätigt bei `aef4e9f` am 19.10.2026:** Update der vorhandenen T95-Einrichtung,
unveränderte Samba-Konfiguration einschließlich eigener fester Freigaben,
aktiver Automounter und Erkennung einer bereits gemounteten exFAT-Freigabe mit
positiver Lese-/Schreibrechte-Prüfung. Die Rückmeldung enthält noch keinen
tatsächlichen Datei-/SMB-Zugriff und keinen Auswurf. [Nachweis und Grenzen](../../../docs/VALIDATION.md#-neue-samba-usb-verwaltung--19102026).

**Anschließender Auswurf fehlgeschlagen:** Bei `aef4e9f` blockierte ein nicht mehr
als Verzeichnis lesbarer Freigabepfad Bereinigung und Statusabfrage. Wiederholung
ohne offenes Samba-Fenster ebenfalls fehlgeschlagen. Die Korrektur ist mit
dateibasierten Samba-Fixtures geprüft.

**Wiederholung bei `52b6be1`: erfolgreich.** Der zuvor fehlgeschlagene exFAT-Auswurf
endete mit `powered-off`, entfernter Freigabe und erloschener LED; udiskie blieb
aktiv. Nach Wiedereinstecken wurden neue diskseq, ausgeschaltete Sperre, Mount
und Freigabe bestätigt. Auch tatsächliches Lesen/Schreiben über Samba wurde
bestätigt. Ein gesonderter Inhaltsvergleich ist noch nicht protokolliert.

| Dateisystem | Client lesen/schreiben mit Inhaltsprüfung | Auswurf und Wiedereinstecken | Ergebnis |
| --- | --- | --- | --- |
| ext4 | ☐ | ☐ 20 Zyklen | Nicht geprüft |
| exFAT | Lesen/Schreiben bestätigt; Inhaltsvergleich offen | ✅ | Teilabnahme bei `52b6be1` |
| FAT32 | ☐ | ☐ | Nicht geprüft |
| NTFS | ☐ | ☐ | Nicht geprüft |
| Btrfs auf einem Laufwerk mit Subvolumes | ☐ | ☐ | Nicht geprüft |

## 🧪 Verbindliche Szenarien

- [ ] Neueinrichtung; Passwortabfrage und `T95-DATA` lesen/schreiben ohne USB.
- [x] Update einer vorhandenen Einrichtung; Sicherung angelegt und Samba-Konfiguration einschließlich eigener fester Freigaben unverändert.
- [x] Bereits gemountete exFAT-Freigabe nach Update erkannt; Automounter aktiv und Benutzerrechte-Prüfung positiv.
- [x] Tatsächliches Lesen und Schreiben über Samba beim getesteten exFAT-Stick bestätigt.
- [x] Fehlgeschlagenen exFAT-Auswurf nach Update fortgesetzt; Freigabe entfernt und Power-off mit erloschener LED bestätigt.
- [x] exFAT nach Wiedereinstecken automatisch gemountet/freigegeben; neue diskseq ohne geerbte Sperre.
- [ ] Bisheriges Samba-Passwort und Inhaltsvergleich gesondert bestätigen.
- [ ] Vorhandene YAML-Konfiguration; ausdrücklich gewählte Projekt-JSON bestätigen.
- [ ] A auswerfen, während B les-/schreibbar bleibt und neu angeschlossenes C eingebunden/freigegeben wird.
- [ ] An beiden eingebauten Anschlüssen und mit versorgtem USB-Hub wiederholen.
- [ ] Mehrere Partitionen: alle zugehörigen Freigaben geschlossen und Mounts entfernt.
- [ ] Power-off nicht unterstützt: bestätigte Sperre/Aushängung erlaubt Abziehen; andere Laufwerke funktionieren weiter.
- [ ] Offene Datei: Fehler ohne falsche Abziehfreigabe; erneuter Versuch funktioniert.
- [ ] Unterbrechung und udiskie-Neustart: Ziel bleibt gesperrt, andere Geräte werden weiter eingebunden.
- [ ] Wiedereinstecken und Rechnerneustart: keine veraltete Sperre oder kollidierenden Freigabenamen.
- [ ] ext4 mit eingeschränkten Rechten und schreibgeschütztes Medium: verständliche Diagnose; Eigentümer/Daten unverändert.
- [ ] Kernel-/UDisks-Protokolle auf I/O-, Verbindungs- und Dateisystemfehler prüfen.

Datum, Revision, Hardware, Dateisystem/Treiber, Ergebnis und Fehlerdetails in den
[Testnachweisen](../../../docs/VALIDATION.md) festhalten. Persönliche Protokolle
bleiben privat. [Nutzeranleitung](../README.md) · [Technische Referenz](SAMBA-USB-SETUP.md)

<!-- Compatibility anchors for older documentation links. -->
<a id="-manuelle-wiederherstellung-prüfen"></a>
<a id="-restore-checkliste"></a>
<a id="-vorbereiten"></a>
<a id="manuelle-wiederherstellung-prüfen"></a>
<a id="restore-checkliste"></a>
<a id="vorbereiten"></a>

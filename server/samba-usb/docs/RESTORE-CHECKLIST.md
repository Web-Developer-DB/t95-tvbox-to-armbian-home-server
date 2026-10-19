# ✅ Hardware-Abnahme: neue Samba-/USB-Verwaltung

**Deutsch** | [English](RESTORE-CHECKLIST.en.md)

**Noch offen:** Diese Liste gilt für die Implementierung vom 19.10.2026.
Frühere Hardwarebestätigungen erfüllen sie nicht. Separate Datenträger mit
gesicherten Daten verwenden. Formatieren oder Reparieren gehört nicht zur Abnahme.

| Dateisystem | Client lesen/schreiben mit Inhaltsprüfung | Auswurf und Wiedereinstecken | Ergebnis |
| --- | --- | --- | --- |
| ext4 | ☐ | ☐ 20 Zyklen | Nicht geprüft |
| exFAT | ☐ | ☐ | Nicht geprüft |
| FAT32 | ☐ | ☐ | Nicht geprüft |
| NTFS | ☐ | ☐ | Nicht geprüft |
| Btrfs auf einem Laufwerk mit Subvolumes | ☐ | ☐ | Nicht geprüft |

## 🧪 Verbindliche Szenarien

- [ ] Neueinrichtung; Passwortabfrage und `T95-DATA` lesen/schreiben ohne USB.
- [ ] Update einer vorhandenen Einrichtung; Samba-Konfiguration und Passwörter vorher/nachher vergleichen.
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

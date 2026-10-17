# T95 TV-Box → Armbian Home-Server

**Deutsch** | [English](README.en.md)

Eine T95 mit **Allwinner H616 und der Platine `H616-T95MAX-AXP313A-V3.0`**
als kleinen Datei- und Medienserver weiterverwenden: Armbian startet von
microSD, Ethernet verbindet die Box mit dem Heimnetz, SSH dient zur Bedienung.
Samba stellt auf Wunsch Dateien für PC, Android und VLC bereit.

![Basisrelease: hardwaregeprüft](https://img.shields.io/badge/Basisrelease-hardwaregepr%C3%BCft-brightgreen)
![System: Armbian 26.8.4](https://img.shields.io/badge/Armbian-26.8.4-18a303)
![Boot: microSD](https://img.shields.io/badge/Boot-microSD-blue)

> [!WARNING]
> **Zuerst die Platine prüfen.** „T95“ bezeichnet unterschiedliche Hardware.
> Nur `H616-T95MAX-AXP313A-V3.0` ist für dieses Image geprüft. Bei anderer
> oder unbekannter Platine hier stoppen: [Hardware identifizieren](docs/HARDWARE_IDENTIFICATION.md)
> und [Entwicklerpfad](docs/PORTING.md).

## Home-Server installieren

**[→ Zur vollständigen Installationsanleitung](docs/INSTALLATION.md)**

Der empfohlene Weg setzt grundlegende Terminal-/SSH-Kenntnisse und einen
Linux-PC mit USB-Kartenleser voraus. Er enthält Voraussetzungen, Download,
Prüfung und lokale Passwortvergabe, SD-Schreiben, Erstlogin und Dateifreigaben.

**Hardware prüfen → PC vorbereiten → SD erstellen → SSH → Kernel schützen
→ Backup → Samba → Dateizugriff prüfen**

> [!IMPORTANT]
> Das Download-Image hat **kein Standardpasswort**. Vor dem Schreiben ist
> eine persönliche Kopie mit eigenem Passwort erforderlich. Die Anleitung
> erledigt das mit dem geprüften Installer. Alle Schreibvorgänge löschen
> die ausgewählte SD vollständig; die interne Android-eMMC wird dabei nicht beschrieben.

**Schon installiert?** [Hilfe nach Symptomen](docs/TROUBLESHOOTING.md) ·
[Samba und USB](server/samba-usb/README.md) · [SD-Backup](docs/BACKUP.md)

## Hardware-Fotos

Vergleiche den **Platinenaufdruck**, nicht nur das Gehäuse. Auf der
Anschlussseite steht er direkt oberhalb des Kühlkörpers. Die KI-unterstützte
Orientierungsansicht markiert die gesuchte Stelle; für den Hardwareabgleich
sind die unveränderten Originalfotos darunter maßgeblich.
Box vor dem Öffnen vollständig von der Stromversorgung trennen.

![KI-unterstützte Orientierungsansicht des Platinenaufdrucks H616-T95MAX-AXP313A-V3.0](docs/images/t95-board-identification.png)

<p>
  <a href="docs/images/t95-board-connectors.jpg"><img src="docs/images/t95-board-connectors.jpg" alt="Original: Anschlussseite der geprüften Platine" width="320"></a>
  <a href="docs/images/t95-board-memory.jpg"><img src="docs/images/t95-board-memory.jpg" alt="Original: Speicherbausteine auf der Rückseite" width="240"></a>
</p>
<p>
  <a href="docs/images/t95-box-top.jpg"><img src="docs/images/t95-box-top.jpg" alt="T95-Gehäuse von oben" width="200"></a>
  <a href="docs/images/t95-case-bottom-redacted.jpg"><img src="docs/images/t95-case-bottom-redacted.jpg" alt="Gehäuseunterseite mit abgedecktem individuellen Aufkleber" width="200"></a>
</p>

Die Originalfotos lassen sich durch Anklicken vergrößern. Sie ersetzen keine
Hardwareprüfung. EXIF-/GPS-Daten sind entfernt; individuelle Aufkleber sind abgedeckt.

## Was funktioniert?

| Funktion | Dokumentierter Stand |
| --- | --- |
| Armbian von microSD, Ethernet, DHCP, SSH, Herunterfahren | Auf der exakten Platine geprüft |
| Samba-Dateifreigaben, USB-Automount, Auswurf, VLC über SMB | Auf der Referenzinstallation geprüft; separat einzurichten |
| eMMC als Datenlaufwerk | Auf der Referenzinstallation geprüft; eigene Einrichtung nötig |
| Armbian von eMMC starten | Nicht erfolgreich; microSD bleibt der unterstützte Bootweg |
| SSH-Dashboard: Einrichtung und Anzeige | Vom Projektbetreiber geprüft und als funktionsfähig bestätigt (17.10.2026) |
| Bluetooth-Musikplayer: Einrichtung und Bedienung | Vom Projektbetreiber geprüft und als funktionsfähig bestätigt (17.10.2026) |
| WLAN, HDMI als Serverfunktion, Fernbedienung und weitere Langzeittests | Nicht Bestandteil der Basisabnahme |

Die Basis ist Armbian **26.8.4 / Debian 13 Trixie / Kernel
`6.18.48-current-sunxi64`**. Nach dem Erstlogin schützt die Anleitung Kernel
und DTB vor unkontrolliertem Ersatz. Ethernet ist auf 100 Mbit/s begrenzt;
im Referenztest wurden ungefähr 11–12 MB/s Nutzdaten erreicht.

[Testnachweise und offene Einzelprüfungen](docs/VALIDATION.md) ·
[Hardwaredetails, Messwerte und SSH-Beispiel](docs/TECHNICAL_REFERENCE.md)

## Optionale Erweiterungen

Erst nach dem funktionierenden Grundsystem und einem privaten SD-Backup:

| Wunsch | Anleitung |
| --- | --- |
| Dateien im Heimnetz bereitstellen und USB-Laufwerke nutzen | [Samba-Modul](server/samba-usb/README.md) |
| Systeminformationen bei der SSH-Anmeldung anzeigen | [Dashboard](docs/SSH_DASHBOARD.md) |
| Musik an Bluetooth-Kopfhörer senden | [Bluetooth und Musikplayer](server/bluetooth/README.md) |
| Beide Zusatzmodule über ein Auswahlmenü einrichten | [Gemeinsamer Setup-Einstieg](server/setup/README.md) |
| Interne eMMC später als Datenlaufwerk verwenden | [Voraussetzungen und Referenz](docs/TECHNICAL_REFERENCE.md#emmc-als-internes-datenlaufwerk) |

## Quellstände

| Bestandteil | Verwendeter Stand |
| --- | --- |
| Basisimage | [Release `v1.0.1`](https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/releases/tag/v1.0.1) |
| Startskript für die SD-Vorbereitung | `main`; lädt die Image-Werkzeuge ausdrücklich vom Tag `v1.0.1` |
| Dokumentation und optionale Servermodule | `main` |
| Lokaler Checkout für Servermodule auf der T95 | `main`; siehe [Setup-Anleitung](server/setup/README.md#lokaler-checkout) |

Das Basisimage wird als Release-Asset geladen. Ein Git-Checkout enthält
Skripte und Dokumentation. Der Release-Werkzeugeordner auf dem PC ist kein
Checkout der aktuellen Servermodule. Installationsbefehle stehen jeweils in ihrer
zuständigen Anleitung; Dateien verschiedener Quellstände nicht mischen.

## Dokumentation und Entwicklerpfad

| Aufgabe | Einstieg |
| --- | --- |
| Neue Box einrichten | [Installation](docs/INSTALLATION.md) |
| Probleme anhand einer Fehlermeldung lösen | [Hilfe nach Symptomen](docs/TROUBLESHOOTING.md) |
| System sichern oder wiederherstellen | [SD-Backup](docs/BACKUP.md) |
| Hardwarestand und Änderungen verstehen | [Technische Referenz](docs/TECHNICAL_REFERENCE.md), [Armbian-Änderungen](docs/CHANGES_FROM_ARMBIAN.md) |
| Release, Layout und bewusstes Kernelupdate prüfen | [Release-Handbuch](docs/RELEASE.md) |
| Andere H616-Platine untersuchen | [Portierung](docs/PORTING.md), [UART](docs/UART_BRINGUP.md), [Bootdiagnose](docs/BOOT_TROUBLESHOOTING.md) |
| Image bauen oder veröffentlichen | [Buildkette](build/README.md), [Veröffentlichung](docs/PUBLISHING.md), [Release-Text](docs/GITHUB_RELEASE_NOTES.md) |

UART ist für Portierung und frühe Bootfehler der Diagnoseweg. Vor diesen
Arbeiten einen **3,3-V-TTL-Adapter** vorbereiten; niemals 5-V-TTL oder RS-232
anschließen. Hardwaredetails und sichere Verdrahtung stehen im Entwicklerpfad.

## Projekt und Grenzen

Ausgangspunkt dieses privaten Projekts war eine als BadBox-belastet oder
-verdächtig eingestufte Android-Installation. Der SD-Umbau verwendet dieses
Android-System nicht als Betriebssystem oder Vertrauensquelle. Er bereinigt
oder entfernt die Android-eMMC nicht automatisch.

Persönliche Images, Backups, Zugangsdaten und rohe Diagnoseaufzeichnungen
bleiben privat. Ein SD-Backup erfasst keine separaten USB-/eMMC-Daten.
Der vollständige Durchlauf der Grundinstallation auf einer separaten SD wird
in der [Abnahme-Checkliste](docs/VALIDATION.md#abnahme-der-installationsanleitung)
geführt. Die bestätigten Dashboard-/Bluetooth-Schritte sind dort separat dokumentiert.

## Lizenz

Für das Repository ist noch keine eigene Lizenz festgelegt. Vor einer
Weiterveröffentlichung sind Projektlizenz und übernommene Upstream-Lizenzen
zu prüfen; die vorhandenen Armbian-Lizenzhinweise bleiben erhalten.

<details>
<summary>Links zu früheren Abschnitten</summary>

<a id="schnellinstallation-dashboard-und-bluetooth"></a><a id="ssh-anmeldedashboard"></a><a id="bluetooth-musikplayer"></a>

[Zusatzmodule](server/setup/README.md)

<a id="vor-der-portierung-uart-ist-erforderlich"></a><a id="uart-diagnose-mit-rp2040-zero"></a>

[Porting / UART](docs/PORTING.md)

<a id="inhaltsübersicht"></a><a id="ein-skript-start"></a><a id="technische-detailreferenz-image-personalisierung-und-sd-schreiben"></a><a id="projektstruktur"></a><a id="reproduzierbarer-build-und-release"></a>

[Entwicklerreferenz](build/README.md)

<a id="projektziel"></a><a id="4-t95-starten-und-per-ssh-anmelden"></a><a id="armbian-standard-und-t95-anpassungen"></a><a id="geprüfte-hardware-und-software"></a><a id="nachgewiesener-stand"></a><a id="emmc-als-internes-datenlaufwerk"></a><a id="leistung-und-verschleiß"></a><a id="bootstrategie"></a><a id="beispiel-einer-erfolgreichen-ssh-sitzung"></a><a id="ssh-statusansicht"></a><a id="sicherheitsgrenzen"></a>

[Technische Referenz](docs/TECHNICAL_REFERENCE.md)

<a id="endanwender-schnellstart"></a><a id="pflichtschritt-nach-dem-ersten-ssh-login-kernel-und-dtb-einfrieren"></a><a id="voraussetzungen"></a><a id="1-arbeitsordner-einrichten-und-release-laden"></a><a id="2-lokale-image-kopie-mit-eigenem-passwort-erzeugen"></a><a id="3-sd-karte-ermitteln-und-image-schreiben"></a><a id="5-kernel-und-dtb-vor-updates-schützen"></a><a id="ausführungsumgebung-linux-oder-wsl2"></a><a id="warum-natives-linux-bevorzugt-wird"></a><a id="wenn-windows-trotzdem-verwendet-wird"></a><a id="1-release-dateien-prüfen"></a><a id="2-werkzeuge-lokal-klonen-und-image-personalisieren"></a><a id="3-sd-karte-eindeutig-bestimmen"></a><a id="4-persönliches-image-schreiben"></a><a id="5-kaltstart-und-ersteinrichtung"></a><a id="kernel--und-dtb-schutz"></a>

[Installation](docs/INSTALLATION.md)

<a id="optional-danach-samba-dateiserver-und-usb-automount-einrichten"></a><a id="6-optional-dateien-über-usbsamba-freigeben"></a><a id="samba--und-usb-dateiserver"></a>

[Samba / USB](server/samba-usb/README.md)

<a id="7-backup-erstellen"></a><a id="sd-backup-und-wiederherstellung"></a>

[Backup](docs/BACKUP.md)

<a id="optionale-weiterentwicklung"></a>

[Testmatrix](docs/VALIDATION.md)

</details>

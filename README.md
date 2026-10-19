# T95 TV-Box → Armbian Home-Server

**Deutsch** | [English](README.en.md)

Eine T95 mit **Allwinner H616 und der Platine `H616-T95MAX-AXP313A-V3.0`**
als kleinen Home-Server nutzen: Armbian startet von microSD und verbindet die
Box per Ethernet mit deinem Heimnetz.

**[🚀 Neu einrichten](docs/INSTALLATION.md)** · **[🧭 Im Alltag benutzen](docs/DAILY_USE.md)** · **[🛟 Problem lösen](docs/TROUBLESHOOTING.md)**

Armbian ist ein vollständiges Linux-System auf Basis von Debian 13.
Die Projektskripte sind **optionale Ergänzungen für die private Nutzung des
Projektbetreibers**. Weitere Anwendungen findest du im
**[Armbian-Software-Katalog](https://docs.armbian.com/software/)** und in der
[Docker-Anleitung](https://docs.armbian.com/software/docker/) — für die Zeit
**nach der Grundinstallation mit Kernel-Sperre**.

![Basisrelease: hardwaregeprüft](https://img.shields.io/badge/Basisrelease-hardwaregepr%C3%BCft-brightgreen)
![Boot: microSD](https://img.shields.io/badge/Boot-microSD-blue)

> [!WARNING]
> **Zuerst die Platine prüfen:** [Aufdruck mit dem Originalfoto vergleichen](#hardware-fotos).
> „T95“ bezeichnet unterschiedliche Hardware. Nur `H616-T95MAX-AXP313A-V3.0`
> ist für dieses Image geprüft. Bei anderer oder unbekannter Platine stoppen:
> [Hardware identifizieren](docs/HARDWARE_IDENTIFICATION.md) und [Entwicklerpfad](docs/PORTING.md).

> [!CAUTION]
> **⛔ PFLICHT: KERNEL UND DTB SPERREN**
>
> Nach der Ersteinrichtung, **vor weiterer Softwareinstallation oder Systemupdates**,
> Kernel und DTB (die Hardwarebeschreibung) sperren. **Die Sperre im normalen
> Betrieb nicht aufheben.** Ein Ersatz kann die T95-Anpassungen überschreiben —
> **die Box startet danach möglicherweise nicht mehr.**
>
> **[→ Pflichtschritt zur Kernel-/DTB-Sperre](docs/INSTALLATION.md#5-kernel-und-dtb-vor-updates-schützen)**

<a id="home-server-installieren"></a>

## 🚀 Home-Server installieren

**[→ Mit Schritt 1 der Installationsanleitung beginnen](docs/INSTALLATION.md)**

**Das legst du bereit:**

| Du brauchst | Wofür? |
| --- | --- |
| 📺 Geprüfte T95 mit passendem Netzteil | Armbian auf der unterstützten Platine betreiben |
| 💾 Entbehrliche microSD und USB-Kartenleser | System schreiben und von SD starten |
| 🖥️ Linux-PC mit Internet | SD vorbereiten und per SSH zugreifen |
| 🌐 Ethernet-Kabel und Router | Die Box mit deinem Heimnetz verbinden |
| 📁 Mindestens 6 GB freier PC-Speicher | Image vorbereiten; zusätzlicher Platz nur für ein optionales SD-Backup |

Die Anleitung erklärt Terminal und SSH, also den Fernzugriff auf die Box.
Windows/WSL2 hat einen eigenen Abschnitt mit zusätzlichen Gerätevoraussetzungen.

**Hardware → PC → SD → SSH → Kernel sperren → optionales Backup → optionaler Dateiserver**

> [!IMPORTANT]
> **Kein Standardpasswort:** Vor dem Schreiben eine persönliche Image-Kopie
> mit eigenem Passwort erzeugen. Der Installer führt dich durch diesen Schritt.
> **Schreiben löscht die ausgewählte SD vollständig.** Die eMMC, der fest
> eingebaute Android-Speicher der Box, wird dabei nicht beschrieben.

<a id="hardware-fotos"></a>

## 📷 Hardware-Fotos

Box vor dem Öffnen vollständig von der Stromversorgung trennen.
**Gesuchter Aufdruck: `H616-T95MAX-AXP313A-V3.0`**, auf der Anschlussseite
oberhalb des Kühlkörpers. Vergleiche ihn mit deiner Platine; der Gehäusename genügt nicht.

<p>
  <a href="docs/images/t95-board-connectors.jpg"><img src="docs/images/t95-board-connectors.jpg" alt="Unverändertes Originalfoto der Anschlussseite; Platinenaufdruck oberhalb des Kühlkörpers" width="320" align="top"></a>
  <a href="docs/images/t95-board-identification.png"><img src="docs/images/t95-board-identification.png" alt="KI-unterstützter Detailausschnitt: Platinenaufdruck H616-T95MAX-AXP313A-V3.0 mit Rahmen und Pfeil markiert" width="480" align="top"></a>
</p>

**Bilder anklicken und vergrößern.** Die KI-unterstützte Detailansicht markiert
den Platinenaufdruck. Für den Hardwareabgleich ist das unveränderte Originalfoto maßgeblich.

<details>
<summary>📷 Weitere Hardwarefotos anzeigen</summary>

<p>
  <a href="docs/images/t95-board-memory.jpg"><img src="docs/images/t95-board-memory.jpg" alt="Original: Speicherbausteine auf der Rückseite" width="200"></a>
  <a href="docs/images/t95-box-top.jpg"><img src="docs/images/t95-box-top.jpg" alt="T95-Gehäuse von oben" width="200"></a>
  <a href="docs/images/t95-case-bottom-redacted.jpg"><img src="docs/images/t95-case-bottom-redacted.jpg" alt="Gehäuseunterseite mit abgedecktem individuellen Aufkleber" width="200"></a>
</p>

Die Originalfotos lassen sich vergrößern. EXIF-/GPS-Daten sind entfernt;
individuelle Aufkleber sind abgedeckt.

</details>

<a id="was-funktioniert"></a>

## ✅ Was funktioniert?

| Funktion | Stand |
| --- | --- |
| microSD-Boot, Ethernet, SSH und Herunterfahren | ✅ Getestet |
| Samba, USB-Laufwerke und VLC über SMB | ✅ Getestet; optional einzurichten |
| SSH-Dashboard und Bluetooth-Musikplayer | ✅ Getestet; optional einzurichten |
| eMMC als Datenlaufwerk | ✅ Getestet; eigene Vorbereitung nötig |
| Armbian von eMMC starten | 🚫 Nicht unterstützt; microSD verwenden |
| WLAN, HDMI als Serverfunktion, Infrarot-Fernbedienung | ❔ Nicht geprüft |

Referenz: **Armbian 26.8.4 / Debian 13 / Kernel `6.18.48-current-sunxi64`**.
Die Dashboard-/Bluetooth-Schritte hat der Projektbetreiber am **17.10.2026**
als funktionsfähig bestätigt. Weitere Abnahmen und Langzeittests stehen in den
[Testnachweisen](docs/VALIDATION.md).

**Neue USB-Verwaltung:** automatisiert geprüft; Hardware-Abnahme noch offen. [Korrekturstand](docs/SAMBA_USB_AUDIT.md).

Ethernet: 100 Mbit/s, gemessen etwa 11–12 MB/s.

<a id="alltag"></a>

## 🧭 Alltag

**[→ Zur Alltagsanleitung](docs/DAILY_USE.md)**: erneut anmelden, Dateien öffnen,
USB sicher auswerfen, Bluetooth bedienen, Musik hören, neu starten oder herunterfahren.
Für Fehler verwende die [Hilfe nach Symptomen](docs/TROUBLESHOOTING.md).

<a id="optionale-erweiterungen"></a>

## 🧩 Optionale Erweiterungen

Wähle nach der Grundinstallation mit Kernel-Sperre die Funktionen, die du
nutzen möchtest. Ein [vollständiges SD-Backup](docs/INSTALLATION.md#6-grundsystem-sichern)
ist optional.

> [!TIP]
> ### 🔌 USB-Dateiserver: einstecken und Dateien teilen
>
> **Mach die USB-Anschlüsse deiner TV-Box zum Dateiserver für dein Heimnetz.**
>
> - **Weniger Handarbeit:** Nach einmaliger Einrichtung werden USB-Sticks, SSDs und
>   externe Festplatten mit unterstütztem Dateisystem automatisch eingebunden und
>   über SMB freigegeben. Du musst nicht jedes Laufwerk selbst mounten oder eine Freigabe anlegen.
> - **Jeder Speicher einzeln erreichbar:** Die USB-Freigaben zeigen die passende
>   Kapazität und den freien Platz des jeweiligen Dateisystems.
> - **Auf die T95 abgestimmt:** Reguläre Samba-Pakete, ergänzt um die eigene
>   Projektkonfiguration und die USB-Helfer für automatisches Einbinden und sicheres Auswerfen.
>
> **[→ USB-Dateiserver einrichten](server/samba-usb/README.md)** ·
> [Laufwerk sicher auswerfen](server/samba-usb/README.md#usb-sicher-auswerfen)

> [!NOTE]
> ### 📊 Dashboard: Speicher und SD-Schreiblast sofort im Blick
>
> **Sieh bei jeder SSH-Anmeldung, was auf deiner Box und ihren Laufwerken los ist.**
>
> - **SD-Schreiblast verfolgen:** `SD-Writes` zeigt die seit dem letzten Systemstart
>   auf die SD-Karte geschriebene Datenmenge.
> - **USB-Speicher zuordnen:** Die Übersicht der eingebundenen Laufwerke zeigt
>   Gerätenamen und Einhängepfade, einschließlich angeschlossener USB-Speicher.
> - **Platzprobleme erkennen:** Gesamtgröße, freier Platz und Belegung stehen direkt
>   dabei; ab 90 % Belegung wird der Prozentwert rot hervorgehoben.
>
> **[→ SSH-Dashboard einrichten](docs/SSH_DASHBOARD.md)**

**Weitere optionale Wege:**

| Dein Ziel | Anleitung |
| --- | --- |
| Musik an Kopfhörer oder Lautsprecher senden | [Bluetooth-Musikplayer](server/bluetooth/README.md) |
| Dashboard und Player über ein Menü einrichten | [Gemeinsame Einrichtung](server/setup/README.md) |
| Interne eMMC als Datenlaufwerk nutzen | [Voraussetzungen für Fortgeschrittene](docs/TECHNICAL_REFERENCE.md#emmc-als-internes-datenlaufwerk) |

<a id="weitere-anwendungen-installieren"></a>

## 📦 Weitere Anwendungen installieren

Wähle Anwendungen mit **ARM64-Unterstützung**, die zur Prozessorleistung,
zu **2 GiB RAM** und dem freien Speicher passen. Reserven für Armbian und
bereits laufende Dienste einplanen; die Projektmodule sind optional.

> [!CAUTION]
> **Kernel-/DTB-Sperre beibehalten.** In `armbian-config` keine Kernelwechsel
> oder Kernel-/Firmware-/Bootloader-Updates aktivieren. Normale
> Anwendungspakete dürfen bei gesetzter Sperre aktualisiert werden.

**Auf der T95, normaler SSH-Benutzer mit `sudo`:**

```bash
sudo armbian-config
```

In der [Armbian-Konfiguration](https://docs.armbian.com/config/) unter
**Software** eine Kategorie und Anwendung auswählen. Docker steht unter
**Software → Containers → Docker**. Anforderungen und Anleitungen stehen
im [Software-Katalog](https://docs.armbian.com/software/).

<details>
<summary>🛠️ Quellstände und Entwicklerdetails</summary>

<a id="quellstände"></a>

## 🛠️ Quellstände

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

<a id="dokumentation-und-entwicklerpfad"></a>

## 📚 Dokumentation und Entwicklerpfad

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

</details>

<a id="projekt-und-grenzen"></a>

## ℹ️ Projekt und Grenzen

Ausgangspunkt dieses privaten Projekts war eine als BadBox-belastet oder
-verdächtig eingestufte Android-Installation. Der SD-Umbau verwendet dieses
Android-System nicht als Betriebssystem oder Vertrauensquelle. Er bereinigt
oder entfernt die Android-eMMC nicht automatisch.

Persönliche Images, Backups, Zugangsdaten und rohe Diagnoseaufzeichnungen
bleiben privat. Ein SD-Backup erfasst keine separaten USB-/eMMC-Daten.
Der vollständige Durchlauf der Grundinstallation auf einer separaten SD wird
in der [Abnahme-Checkliste](docs/VALIDATION.md#abnahme-der-installationsanleitung)
geführt. Die bestätigten Dashboard-/Bluetooth-Schritte sind dort separat dokumentiert.

<a id="lizenz"></a>

## 📄 Lizenz

Für das Repository ist noch keine eigene Lizenz festgelegt. Vor einer
Weiterveröffentlichung sind Projektlizenz und übernommene Upstream-Lizenzen
zu prüfen; die vorhandenen Armbian-Lizenzhinweise bleiben erhalten.

<details>
<summary>🔗 Links zu früheren Abschnitten</summary>

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

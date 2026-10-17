<a id="technische-referenz-des-geprüften-t95-aufbaus"></a>

# 📚 Technische Referenz des geprüften T95-Aufbaus

**Deutsch** | [English](TECHNICAL_REFERENCE.en.md)

Diese Referenz bewahrt Hardwaredetails, Messwerte und Hintergründe aus der
bisherigen README. Für die Einrichtung folge der [Installationsanleitung](INSTALLATION.md).
Die Messwerte beschreiben den dokumentierten Aufbau; sie sind keine
Mindestanforderungen oder Zusagen für andere Geräte.

| Gesuchte Information | Weiterlesen |
| --- | --- |
| 📦 Image und Layout | [Release-Handbuch](RELEASE.md) |
| ✅ Prüfergebnisse und offene Abnahme | [Testmatrix](VALIDATION.md) |
| 🧭 Abweichende Hardware | [Portierungspfad](PORTING.md) |

[Zur Startseite](../README.md)

<a id="armbian-standard-und-t95-anpassungen"></a>

## 🧩 Armbian-Standard und T95-Anpassungen

Als Ausgangspunkt dient ein offizielles Armbian-Image für die verwandte
Tanix-TX6s-/AXP313-Plattform: Armbian 26.8.4, Debian 13 Trixie und Kernel
`6.18.48-current-sunxi64`. Kernel, Initramfs und das Debian-Root-Dateisystem
werden im nachgewiesenen T95-6.18-Aufbau weitgehend unverändert übernommen.
Die Bootfähigkeit entsteht durch eine zusätzliche, hardware­spezifische
Bootkette:

> [!CAUTION]
> **UART-ADAPTER VOR DER PORTIERUNG ANSCHLIESSEN:** Vor jeder Portierung
> einer ähnlichen Platine einen **3,3-V-TTL-UART-
> Adapter** anschließen und den Bootlog aufzeichnen. Nur damit lassen sich
> Fehler in TOC0/U-Boot, DRAM/PMIC, DTB oder Kernel unterscheiden, bevor
> Änderungen an der Armbian-Basis vorgenommen werden. Ein RP2040-Zero kann
> mit der passenden Firmware als Adapter dienen: [RP2040-Zero-UART-
> Adapterprojekt](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter).
> Verwende 115200 Baud, 8N1 und gemeinsame Masse; 5-V-TTL und echtes RS-232
> dürfen nicht direkt an der Platine angeschlossen werden.

| Bestandteil | Armbian-Ausgangsstand | T95-Projektänderung | Bei anderer Box zuerst prüfen |
| --- | --- | --- | --- |
| Kernel und Rootfs | vorhanden, funktionierender Standard | kein Kernel-Neubau im finalen 6.18-Aufbau | Kernelversion und Treiberbestand beibehalten |
| U-Boot / TOC0 | generischer Board-Bootpfad | eigener T95-Loader, SD-Laden von `mmc 0:1`, TOC0 bei Byte 8192 | SoC, DRAM, PMIC und Boot-ROM-Vertrag |
| TF-A / BL31 | passend zum Ausgangsboard | mit dem T95-U-Boot gepaarte TF-A-Version | SoC-/Boardvariante und BL31-Kompatibilität |
| DTB | Tanix-TX6s-/AXP313-DTB | T95-kompatibler Name und AC300-/RMII-Beschreibung | tatsächliche Platine, PHY-Adresse, MDIO und Taktpfad |
| `armbianEnv.txt` | generische DTB-/Bootauswahl | T95-DTB, serielle Konsole, ext4-Root und Diagnoseparameter | nur die wirklich belegten Gerätewerte ändern |
| AC300-Ethernet | nicht für jede T95-Revision garantiert | DTB-/U-Boot-Vorinitialisierung für `end0` | PHY, Reset, Clock, MAC und Link separat messen |
| `clk_ignore_unused nohz=off` | nicht erforderlich | vorläufige Diagnose-/Stabilitätshilfe | nach erfolgreichem Boot wieder unabhängig testen |
| Sicherheits-Härtung | nicht Teil des Rohimages | Root sperren, Hostkeys entfernen, neue Hostkeys vor `sshd` erzeugen | Zugangsdaten immer lokal personalisieren |
| Samba und USB-Shares | nicht Teil des Minimalimages | separates Modul unter `server/samba-usb/` | erst nach stabilem Linux- und Netzwerkstart |

Für diese Platine ist daher **nur das Austauschen des DTB nicht ausreichend**:
Ein ungeeigneter U-Boot-/TOC0-Loader kann bereits vor dem Kernel hängen bleiben.
Umgekehrt muss für einen reinen Kernel- oder Userspace-Fehler nicht sofort die
gesamte Armbian-Basis geändert werden. Die bewährte Reihenfolge ist:

1. **Kein U-Boot-Banner:** zuerst Loader, TOC0-Offset, SD-Layout und UART prüfen.
2. **U-Boot startet, DRAM/PMIC scheitert:** nur DRAM-, AXP313- oder Boardparameter
   des Loaders untersuchen.
3. **Kernel startet, aber bleibt früh hängen:** DTB, Kernelversion und
   `armbianEnv.txt` vergleichen; Rootfs zunächst unverändert lassen.
4. **Linux läuft, Ethernet fehlt:** AC300-/PHY-Knoten, RMII, Reset und Clock
   prüfen; Samba oder eMMC sind dafür nicht relevant.
5. **Linux und Netzwerk laufen:** erst dann optionale Schichten wie Samba,
   USB-Automount und eMMC-Datenablage einrichten.

Diese Trennung erleichtert Portierungen: Für eine ähnliche Platine werden
zunächst Kernel und Rootfs aus dem passenden Armbian-Image übernommen und nur
die nachweislich boardabhängigen Teile angepasst. Änderungen am Kernel oder am
Rootfs sind erst dann gerechtfertigt, wenn UART-Log und DTB-Prüfung zeigen,
dass die Bootkette bereits funktioniert.

Die vollständige Zuordnung von Armbian-Ausgangspunkt, Patch, Build-Skript,
Resultat, Portierungsprüfung und Nachweis steht im
[Änderungsinventar](CHANGES_FROM_ARMBIAN.md). Dort sind auch die bewusst
unveränderten Bestandteile und die Pflegeanforderungen für neue Armbian-Releases
festgehalten.

<a id="geprüfte-hardware-und-software"></a>

## 🔎 Geprüfte Hardware und Software

| Bereich | Nachgewiesene Konfiguration |
| --- | --- |
| Platine | `H616-T95MAX-AXP313A-V3.0` |
| SoC | Allwinner H616, 4 × Cortex-A53 |
| PMIC | AXP313A |
| Arbeitsspeicher | 2 GiB DRAM |
| Ethernet | Allwinner AC300 EPHY, RMII, 100 Mbit/s Full Duplex |
| Systemmedium | 128-GB-microSD (`/dev/mmcblk0`) |
| Interner Speicher | ca. 32-GB-eMMC (`/dev/mmcblk2`), Lesen/Schreiben geprüft; als ext4-Datenlaufwerk nutzbar |
| Distribution | Armbian 26.8.4, Debian 13 Trixie |
| Kernel | `6.18.48-current-sunxi64` |
| DTB | `sun50i-h616-t95-axp313-tanix-6.18.dtb` |
| Bootmedium | microSD, TOC0-Loader ab Byte 8192 |

<a id="nachgewiesener-stand"></a>

## ✅ Nachgewiesener Stand

| Test | Ergebnis | Hinweis |
| --- | :---: | --- |
| SD-Boot mit eigenem TOC0-/U-Boot | ✅ | eMMC bleibt dabei unverändert |
| DRAM-Initialisierung | ✅ | 2 GiB erkannt |
| Ethernet / DHCP / SSH | ✅ | `end0`, 100 Mbit/s, IPv4/IPv6 und DNS getestet |
| Endanwender-Start | ✅ | Start aus ausgeschaltetem Zustand von microSD geprüft |
| Sauberes Herunterfahren | ✅ | kontrolliertes Herunterfahren im Betrieb geprüft |
| Dateizugriff | ✅ | Dateien über den eingerichteten Serverpfad erreichbar |
| eMMC als ext4-Datenlaufwerk | ✅ | interner Speicher funktioniert als Datenmedium; Einbindung ist installationsabhängig |
| Armbian-Boot von eMMC | ❌ | Installations-/Bootversuch fehlgeschlagen; microSD bleibt der unterstützte Bootweg |
| CPU-Dauerlast | ✅ | 4 Worker, 10 Minuten, ca. 62 °C maximal |
| microSD-I/O | ✅ | etwa 22–23 MB/s Lesen und 21,5 MB/s Schreiben |
| eMMC-I/O | ✅ | ca. 63,8–77,4 MB/s Lesen; Schreiben für diesen Stand nicht belastbar gemessen |
| eMMC-Gesundheit | ✅ | Life Time A/B und Pre-EOL jeweils `0x01` |
| SSH-Dashboard | ✅ | dokumentierte Schritte vom Projektbetreiber am 17.10.2026 geprüft und bestätigt |
| Bluetooth-Musikplayer | ✅ | dokumentierte Schritte vom Projektbetreiber am 17.10.2026 geprüft und bestätigt; separat einzurichten |
| WLAN / GPU / weitere Audio-Ausgänge | ⚠️ | nicht Bestandteil des abgenommenen Funktionsumfangs |
| Samba `T95-DATA` | ✅ | authentifizierte SMB2/SMB3-Freigabe getestet |
| USB-Automount und dynamische Usershares | ✅ | Label-/Fallback-Namen, Auswurf und Wiedereinstecken getestet |
| VLC-Wiedergabe über SMB | ✅ | lokale Netzwerk-Wiedergabe erfolgreich geprüft |

Die Samba-/USB-Ausbaustufe sowie die Endanwender-Abnahme mit Start,
Herunterfahren und Dateizugriff sind damit bestanden. Langzeitmessungen,
weitere Peripherie und eine endgültige Kernel-/Timer-Konfiguration bleiben
optionale Weiterentwicklungen und ändern den stabil getesteten Grundstand
nicht.

<a id="emmc-als-internes-datenlaufwerk"></a>

## 💽 eMMC als internes Datenlaufwerk

Die T95 besitzt neben dem microSD-Steckplatz einen internen eMMC-Speicher. Unter
Armbian wird er als `/dev/mmcblk2` mit einer nutzbaren Kapazität von etwa
29,1 GiB erkannt (entspricht nominell 32 GB). Die vom eMMC-Standard
bereitgestellten Bootbereiche sind ebenfalls vorhanden:

```text
/dev/mmcblk2boot0   4 MiB
/dev/mmcblk2boot1   4 MiB
```

Für den Serverbetrieb wurde der Nutzbereich als eigene ext4-Datenpartition
eingerichtet:

```text
/dev/mmcblk2p1   ext4   Label: T95-DATA   Mountpoint: /srv/T95-DATA
```

Die konkrete UUID wird absichtlich nicht dokumentiert. Sie gehört zur jeweils
verwendeten eMMC-Partition und muss bei einer eigenen Einrichtung mit
`blkid` bzw. `findmnt` ermittelt werden.

### Leistung und Verschleiß

Die protokollierten sequenziellen Lesetests ergaben:

| Medium / Test | Ergebnis |
| --- | ---: |
| eMMC, direkter Lesetest | ca. 77,4 MB/s |
| eMMC, `hdparm` | ca. 63,8 MB/s |
| microSD, Lesen | ca. 23,4 MB/s |
| microSD, Schreiben | ca. 21,5 MB/s |

Damit liest die eMMC ungefähr drei Mal schneller als die verwendete microSD.
Ein belastbarer eMMC-Schreibwert liegt für diesen Versuchsstand nicht vor und
wird deshalb nicht angegeben.

Die eMMC-Health-Register wurden mit `mmc-utils` geprüft:

```text
DEVICE_LIFE_TIME_EST_TYP_A = 0x01
DEVICE_LIFE_TIME_EST_TYP_B = 0x01
PRE_EOL_INFO               = 0x01
```

`0x01` steht bei den beiden Lifetime-Feldern für etwa 0–10 % der
spezifizierten Lebensdauer und beim Pre-EOL-Feld für einen normalen Zustand.
Die getestete eMMC zeigte somit keinen nennenswerten Verschleiß. Diese
Hersteller-Schätzwerte ersetzen keine Backups und sind keine Garantie für die
zukünftige Lebensdauer.

### Bootstrategie

Ein vollständiger Armbian-Start von der eMMC wurde versucht, war mit dem
generischen eMMC-Bootloader auf dieser konkreten H616-/AXP313A-Platine jedoch
nicht zuverlässig möglich. Das Problem lag im Bootpfad, nicht an der
Dateisystem- oder eMMC-Gesundheit. Der reproduzierbare Stand verwendet daher:

```text
microSD  → TOC0-/U-Boot und Armbian-System
eMMC     → dauerhaftes ext4-Datenlaufwerk (T95-DATA)
```

Diese Aufteilung verändert die Android-eMMC nicht automatisch und macht sie
nicht bootfähig. Sie bietet trotzdem eine schnelle interne Ablage für Backups,
Samba-Dateien und andere Serverdaten.

Im öffentlichen SD-Release wird die interne eMMC nicht beschrieben. Wer sie
wie im geprüften Aufbau als Datenlaufwerk verwenden möchte, muss Partitionierung,
Formatierung und Einbindung bewusst selbst durchführen und vorher ein eigenes
Backup anlegen.

Das integrierte Ethernet ist auf 100 Mbit/s begrenzt; gemessen wurden etwa
94,5 Mbit/s beziehungsweise ungefähr 11–12 MB/s Nutzdaten pro Sekunde. Bei
Samba-Zugriffen ist daher das Netzwerk und nicht die eMMC der limitierende
Faktor.

<a id="beispiel-einer-erfolgreichen-ssh-sitzung"></a>

## 🖥️ Beispiel einer erfolgreichen SSH-Sitzung

### SSH-Statusansicht

Die folgende anonymisierte Sitzung zeigt den erfolgreichen Armbian-Start und
die verfügbaren Systeminformationen nach der SSH-Anmeldung. Netzwerkadressen,
der letzte Login-Absender und der lokale Hostname wurden durch
Dokumentationswerte ersetzt.

![Anonymisierte SSH-Statusansicht der T95 unter Armbian](images/t95-ssh-status-redacted.png)

> [!NOTE]
> **Datenschutz-Hinweis:** Das Bild basiert auf einer echten SSH-Sitzung des
> getesteten Systems, ist für die Veröffentlichung aber sichtbar bereinigt.
> LAN-/WAN-Adressen, IPv6-Adressen, der letzte Login-Absender und der lokale
> Hostname wurden durch neutrale Dokumentationswerte ersetzt. Es handelt sich
> daher nicht um eine unveränderte Live-Aufnahme.

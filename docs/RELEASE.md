# Release-Handbuch: T95 H616 / AXP313A

**Deutsch** | [English](RELEASE.en.md)

Stand: 2026-09-22. Dieser **stabil getestete, hardwaregebundene** SD-Release gilt ausschließlich für
`H616-T95MAX-AXP313A-V3.0`. Er ist kein universelles T95-Image und verändert
die Android-eMMC nicht. Fotos zur Boardzuordnung stehen in der
[README](../README.md#hardware-fotos); individuelle Daten auf
dem Unterseitenfoto sind redigiert.

**Für die Einrichtung:** [Schritt-für-Schritt-Installation](INSTALLATION.md).
Dieses Handbuch beschreibt Release-Artefakte und Wartung.

## Release-Identität

| Eigenschaft | Wert |
|---|---|
| Releasekanal | `v1.0.1` (finaler, hardwaregebundener Release) |
| Projektstatus | stabil getestet auf `H616-T95MAX-AXP313A-V3.0` |
| System | Armbian 26.8.4 Trixie |
| Kernel | `6.18.48-current-sunxi64` |
| Bootmedium | microSD, eine Ext4-Partition ab Byte 4 MiB |
| Bootloader | signierter T95-TOC0-Loader bei Byte 8192 |
| DRAM / Ethernet | 2 GiB DDR3L, DCDC3 1,36 V / AC300 EPHY (`end0`, 100 Mbit/s) |
| eMMC im Releaseweg | kein Lese- oder Schreibzugriff |

Die eMMC funktioniert als interner Blockspeicher und kann außerhalb des
öffentlichen SD-Releasewegs als ext4-Datenlaufwerk eingebunden werden. Ein
Armbian-Installations- und Bootversuch von eMMC war nicht erfolgreich; der
nachgewiesene und unterstützte Bootweg dieses Releases ist deshalb weiterhin
die microSD-Karte.

Das gehärtete generische Rohimage hat die SHA-256
`849ec697bca90c07537b4b71bad350c9a05854ac8287fc960483d3bf0d0b7cf4`
und ist 1.535.115.264 Byte groß. Es enthält kein verwendbares Root-Passwort,
keine SSH-Hostschlüssel, keine `authorized_keys`, keine Benutzerverzeichnisse
und keine `machine-id`.

Das Rootkonto ist im öffentlichen Download gesperrt. Beim ersten SSH-Start
erzeugt eine systemd-Abhängigkeit eigene Hostschlüssel **vor** `ssh.service`.
Armbians spätere Hostkey-Neuerzeugung ist für dieses Image deaktiviert, damit
die bereits eindeutigen Schlüssel erhalten bleiben.

`v1.0.1` hält im Linux-DTB den AXP313A-Regler `dcdc3` auf 1,36 V. Der Wert
entspricht der SPL-DRAM-Initialisierung und wurde mit vollständigen Kaltstarts
auf zwei Boxen der exakten Platinenrevision geprüft.

## Nachgewiesener Stand und Grenzen

Der zugrunde liegende SD-Start wurde auf echter Hardware mit UART geprüft:
TOC0-SPL, 2 GiB DRAM, AXP313/AC300-Vorinitialisierung, Ext4-Boot, Kernel,
systemd, `end0`, Link, DHCP und SSH. Der RP2040-Zero als externer 3,3-V-TTL-
Adapter (115200 Baud/8N1) ist im separaten
[UART-Adapterprojekt](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
dokumentiert.

Die neue Zugangsdaten-Härtung wurde vollständig offline geprüft: Rootkonto
gesperrt, Hostkey-Dateien entfernt, Root-Hash und alle drei privaten
Quellhostkey-Payloads im vollständigen Rohimage nicht auffindbar, Ext4
prüfbar. Die Endanwender-Abnahme des personalisierten Systems wurde auf der
Zielplatine bestanden: Start von microSD, sauberes Herunterfahren, SSH und
Dateizugriff funktionierten ohne beobachtete Fehler. Der Status „stabil
getestet“ bezieht sich ausschließlich auf diesen dokumentierten Aufbau; er
ist keine Garantie für andere T95-Revisionen oder ungetestete
Langzeit-/Peripheriefunktionen.

Nicht Bestandteil der Stabilitätszusage sind WLAN, Audio, Fernbedienung, HDMI
als Serverfunktion, zusätzliche Langzeitmessungen und Kernel-/Bootloader-
Aktualisierungen.

## Öffentliche Release-Assets erzeugen

Nur ein gehärtetes, anschließend gegen das private Quellartefakt geprüftes
Image darf paketiert werden. Alle Schritte arbeiten ausschließlich auf
Host-Dateien – kein Blockgerät, FEL oder eMMC wird geöffnet.

```bash
export REPO=/pfad/zum/t95-h616-axp313a-projekt
export SOURCE_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-ext4-image-20260914-101300"
export HARDENED_ARTIFACT="$REPO/build/artifacts/t95-tanix-6.18-hardened-20260915-120000"

bash "$REPO/build/audit-t95-generic-release-image.sh" \
  "$HARDENED_ARTIFACT" "$SOURCE_ARTIFACT"
T95_RELEASE_ARTIFACT="$HARDENED_ARTIFACT" \
  bash "$REPO/build/create-t95-release-asset.sh" v1.0.1
```

Der Release-Ordner enthält sechs Dateien:

```text
T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
RELEASE-MANIFEST.txt
HARDENING-METADATA.txt
T95-H616-AXP313A-u-boot-sunxi-with-spl.bin
T95-H616-AXP313A-tanix-6.18.dtb
SHA256SUMS
```

Vor Upload immer prüfen:

```bash
cd "$REPO/release-assets/v1.0.1"
sha256sum -c SHA256SUMS
xz -t T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v1.0.1.img.xz
```

## Lokale Personalisierung und SD-Schreibvorgang

Das öffentliche Image ist vor der lokalen Personalisierung nicht per Passwort
loginfähig. Root ist gesperrt. Der Installer fragt zweimal verdeckt nach einem
eigenen, nichtleeren Passwort und schreibt dessen SHA-512-Hash nur in die
private Kopie; Passwort und Hash erscheinen nicht im Begleitmanifest.

Der maßgebliche Endanwenderweg steht in der [Installation](INSTALLATION.md).
Die [manuelle Alternative](INSTALLATION.md#manuelle-alternative-zur-sd-vorbereitung)
ersetzt ausschließlich deren SD-Vorbereitung. Beide Wege verwenden das Image
und die Image-Werkzeuge vom Tag `v1.0.1`; die neuen Server-Zusatzmodule kommen
separat aus `codex/archive-ssh-dashboard`.

Persönliche Images und `.t95-provisioned-manifest`-Dateien bleiben privat.
Der Schreiber akzeptiert wechselbare USB-Karten, prüft Manifest und Rücklese-
Hash und öffnet weder die T95-eMMC noch FEL. Nach `ERFOLG` die SD nur bei
vollständig ausgeschalteter Box einsetzen. Erstes SSH-Login: `root` mit dem
lokal gewählten Passwort, danach Armbian-Ersteinrichtung und normaler Benutzer.

## Den geprüften Kernel-/DTB-Stand schützen

Nach der Ersteinrichtung die Armbian-Metapakete halten, damit ein automatisches
Upgrade nicht den H616-/DTB-/Ethernet-Stand ersetzt:

```bash
sudo apt-mark hold linux-image-current-sunxi64 linux-dtb-current-sunxi64
apt-mark showhold
uname -r
dpkg-query -W -f='${binary:Package}\t${Version}\t${Status}\n' \
  linux-image-current-sunxi64 linux-dtb-current-sunxi64
```

Vor einem bewusst geplanten Kernel-/DTB-Upgrade ein Vollbackup erstellen,
UART bereithalten und anschließend erneut Kaltstart, DTB, AC300 und Netzwerk
prüfen:

```bash
sudo apt-mark unhold linux-image-current-sunxi64 linux-dtb-current-sunxi64
sudo apt update
sudo apt full-upgrade
```

Die Sperre ersetzt keine Sicherheitsbewertung und ist keine pauschale
Abschaltung aller Debian-Sicherheitsupdates.

## Rebuild-Grenze

Die Armbian-Quelle, U-Boot `v2024.04`/`25049ad560826f7dc1c4740883b0016014a59789`
und TF-A `v2.10`/`b6c0948400594e3cc4dbb5a4ef04b815d2675808` sind in lokalen
Artefakten festgehalten. Der finale TOC0-Loader wurde mit einem privaten
Experimentierschlüssel signiert. Dieser Schlüssel wird absichtlich nicht
veröffentlicht; der hashbelegte Loader im Release-Asset ist maßgeblich.

Die hostseitige Reihenfolge lautet: Armbian vorbereiten, DTB ableiten, Image
zusammensetzen, Image härten, gegen das private Quellartefakt auditieren, erst
dann das Release-Asset erzeugen. Details stehen in
[../build/README.md](../build/README.md). Bei Fehlern eMMC nicht als
Reparaturweg verwenden; stattdessen SD erneut aus dem geprüften Asset aufbauen
und UART-Daten privat sichern.

# Release-Handbuch: T95 H616 / AXP313A

Stand: 2026-09-15. Dieser experimentelle SD-Release gilt ausschließlich für
`H616-T95MAX-AXP313A-V3.0`. Er ist kein universelles T95-Image und verändert
die Android-eMMC nicht. Fotos zur Boardzuordnung stehen in der
[README](../README.md#fotos-der-geprüften-hardware); individuelle Daten auf
dem Unterseitenfoto sind redigiert.

## Release-Identität

| Eigenschaft | Wert |
|---|---|
| Releasekanal | `v0.1.1-hardened-experimental` |
| System | Armbian 26.8.4 Trixie |
| Kernel | `6.18.48-current-sunxi64` |
| Bootmedium | microSD, eine Ext4-Partition ab Byte 4 MiB |
| Bootloader | signierter T95-TOC0-Loader bei Byte 8192 |
| DRAM / Ethernet | 2 GiB / AC300 EPHY (`end0`, 100 Mbit/s) |
| eMMC im Releaseweg | kein Lese- oder Schreibzugriff |

Das gehärtete generische Rohimage hat die SHA-256
`e2c1fad50f6bc138332de8ef944b9e83462a882414cc736e9537450de759df4c`
und ist 1.535.115.264 Byte groß. Es enthält kein verwendbares Root-Passwort,
keine SSH-Hostschlüssel, keine `authorized_keys`, keine Benutzerverzeichnisse
und keine `machine-id`.

Das Rootkonto ist im öffentlichen Download gesperrt. Beim ersten SSH-Start
erzeugt eine systemd-Abhängigkeit eigene Hostschlüssel **vor** `ssh.service`.
Armbians spätere Hostkey-Neuerzeugung ist für dieses Image deaktiviert, damit
die bereits eindeutigen Schlüssel erhalten bleiben.

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
prüfbar. Ein Kaltstart des **gehärteten** Release-Assets ist noch als eigener
Abnahmetest offen. Deshalb bleibt der Kanal experimentell.

Nicht freigegeben sind WLAN, Audio, Fernbedienung, HDMI als Serverfunktion,
USB-/SMB-Dauerlast, mehrere Kaltstarts, Langzeitbetrieb und Kernel-/Bootloader-
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
  bash "$REPO/build/create-t95-release-asset.sh" v0.1.1-hardened-experimental
```

Der Release-Ordner enthält sieben Dateien:

```text
T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img.xz
RELEASE-MANIFEST.txt
HARDENING-METADATA.txt
HARDENED-ARTIFACT-SHA256SUMS
T95-H616-AXP313A-u-boot-sunxi-with-spl.bin
T95-H616-AXP313A-tanix-6.18.dtb
SHA256SUMS
```

Vor Upload immer prüfen:

```bash
cd "$REPO/release-assets/v0.1.1-hardened-experimental"
sha256sum -c SHA256SUMS
xz -t T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img.xz
```

## Lokale Personalisierung und SD-Schreibvorgang

Das GitHub-Image ist absichtlich nicht direkt loginfähig. Es wird vor dem
Schreiben lokal und außerhalb des Repositorys personalisiert. Das Werkzeug
fragt zweimal verdeckt nach einem eigenen Passwort (mindestens 12 Zeichen)
und schreibt nur dessen SHA-512-Hash in die private Kopie. Passwort und Hash
erscheinen nicht in der Kommandozeile oder im begleitenden Manifest.

```bash
export DOWNLOAD=/pfad/zum/GitHub-Release-Download
mkdir -p "$HOME/t95-private"
(cd "$DOWNLOAD" && sha256sum -c SHA256SUMS)
xz -dk --keep \
  "$DOWNLOAD/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img.xz"
bash "$REPO/tools/provision-t95-release-image.sh" \
  "$DOWNLOAD/T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img" \
  "$HOME/t95-private/t95-personal.img" \
  PROVISION-T95-ROOT-PASSWORD

lsblk -b -o NAME,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS
bash "$REPO/tools/write-t95-provisioned-image-to-sd.sh" \
  /dev/sdX \
  "$HOME/t95-private/t95-personal.img" \
  "$HOME/t95-private/t95-personal.img.t95-provisioned-manifest" \
  WRITE-T95-PROVISIONED-TO-SDX
```

`/dev/sdX` ist ein Platzhalter und muss nach jedem Einstecken neu mit `lsblk`
bestimmt werden. Der Schreiber akzeptiert ausschließlich eine wechselbare
USB-SD-Karte, prüft ihren Rücklese-Hash und öffnet weder T95-eMMC noch FEL.
Die persönliche Image-Datei samt Manifest ist privat und darf weder in Git
noch als GitHub-Asset landen.

Nach `ERFOLG`: SD nur bei ausgeschalteter T95 einsetzen, Ethernet verbinden
und einschalten. Die DHCP-Adresse im Router suchen, den neuen SSH-Fingerprint
prüfen und sich mit dem lokalen Personalisierungs-Passwort als `root`
anmelden. Armbian führt anschließend durch seine Ersteinrichtung.

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

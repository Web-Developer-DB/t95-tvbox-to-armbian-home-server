# Entwurf für GitHub Release `v0.1.1-hardened-experimental`

## T95 H616 / AXP313A: gehärtetes SD-Armbian

Experimenteller SD-Release für die exakt geprüfte Platine
`H616-T95MAX-AXP313A-V3.0`. Der Startweg nutzt die microSD; die Android-eMMC
wird nicht gelesen oder beschrieben.

Der zugrunde liegende Start mit U-Boot, 2 GiB RAM, AC300-Ethernet, DHCP und
SSH wurde auf der Zielplatine nachgewiesen. UART-Diagnosen erfolgten mit einem
externen [RP2040-Zero-UART-Adapter](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
(3,3-V-TTL, 115200 Baud/8N1).

### Sicherheitsänderung

Der öffentliche Download enthält **kein Standardpasswort** und **keine
SSH-Hostschlüssel**:

- Root ist im generischen Image gesperrt.
- Der Anwender erzeugt vor dem SD-Schreiben lokal eine private Kopie mit einem
  eigenen Passwort.
- Die T95 erzeugt bei ihrem ersten SSH-Start eigene Hostschlüssel, bevor
  `ssh.service` Verbindungen annimmt.
- Der frühere Root-Hash und die drei privaten Quellhostkeys wurden im gesamten
  gehärteten Rohimage geprüft und nicht gefunden.

### Installation

1. Alle sieben Assets herunterladen und `sha256sum -c SHA256SUMS` ausführen.
2. Das Image entpacken, mit
   `tools/provision-t95-release-image.sh` außerhalb des Repositorys lokal
   personalisieren und die dabei angelegte private Manifest-Datei behalten.
3. Ausschließlich
   `tools/write-t95-provisioned-image-to-sd.sh` mit einem frisch per `lsblk`
   geprüften wechselbaren `/dev/sdX` verwenden.
4. Karte nur bei ausgeschalteter Box einsetzen, Ethernet vor dem Einschalten
   verbinden, DHCP-Adresse ermitteln und den neuen SSH-Fingerprint prüfen.
5. Per SSH als `root` mit dem lokal gewählten Passwort anmelden und Armbians
   Ersteinrichtung abschließen.

Vollständige Anleitung: [RELEASE.md](RELEASE.md).

### Wichtige Grenzen

- Nur diese Board-Revision ist unterstützt. Andere „T95“-Boxen können andere
  SoCs, RAM, PMICs oder Netzwerkhardware besitzen.
- `clk_ignore_unused nohz=off` bleibt eine Diagnosekonfiguration.
- WLAN, Audio, Fernbedienung, USB-/SMB-Dauerlast und Langzeitbetrieb sind
  nicht Teil der Freigabe. Die grundlegende Samba-/USB-/VLC-Funktion wurde
  separat auf der T95 geprüft.
- Kernel- und Bootloader-Updates nur nach Backup und erneuter UART-/Netzwerk-
  Validierung durchführen.
- Der gehärtete Asset-Aufbau wurde offline geprüft; ein eigener Kaltstarttest
  dieses Assets bleibt vor einer stabilen Freigabe erforderlich.

### Assets

- `T95-H616-AXP313A-Armbian-26.8.4-6.18.48-v0.1.1-hardened-experimental.img.xz`
- `RELEASE-MANIFEST.txt`
- `HARDENING-METADATA.txt`
- `HARDENED-ARTIFACT-SHA256SUMS`
- `T95-H616-AXP313A-u-boot-sunxi-with-spl.bin`
- `T95-H616-AXP313A-tanix-6.18.dtb`
- `SHA256SUMS`

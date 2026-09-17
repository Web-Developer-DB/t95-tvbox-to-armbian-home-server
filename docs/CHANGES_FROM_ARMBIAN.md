# Änderungsinventar: Armbian-Basis → T95

Dieses Dokument beschreibt die **öffentlichen, reproduzierbaren Änderungen**
gegenüber dem verwendeten Armbian-Ausgangsstand. Es ist die technische
Detailreferenz zur kompakten Übersicht in der [README](../README.md).

## Ausgangsstand

| Merkmal | Festgelegter Ausgangspunkt |
| --- | --- |
| Distribution | Armbian 26.8.4, Debian 13 (Trixie) |
| Referenzboard | Tanix TX6s / AXP313 |
| Eingabeimage | `Armbian_26.8.4_Tanix-tx6s-axp313_trixie_current_6.18.48_minimal.img.xz` |
| Eingabeimage-SHA-256 | `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` |
| Kernel | `6.18.48-current-sunxi64` |
| U-Boot | v2024.04, Commit `25049ad560826f7dc1c4740883b0016014a59789` |
| TF-A | v2.10, Commit `b6c0948400594e3cc4dbb5a4ef04b815d2675808` |
| Zielhardware | Platine `H616-T95MAX-AXP313A-V3.0` |
| Bootmedium | microSD; der getestete eMMC-Boot ist nicht der unterstützte Pfad |

Die Eingabe wird durch `build/prepare-t95-tanix-6.18-source.sh` anhand fester
SHA-256-Prüfsummen verifiziert. Die konkreten Image-Dateien und Build-Artefakte
bleiben lokal bzw. werden nur als GitHub-Release-Asset veröffentlicht.

## Änderungsmatrix

Die IDs sind stabil. Bei einer neuen Armbian-Version wird eine bestehende ID
aktualisiert oder eine neue ID ergänzt; die Begründung und der Nachweis müssen
dabei erhalten bleiben.

| ID | Armbian-Basis | Projektdatei/Patch | Änderung | Zweck | Portierung prüfen | Nachweis |
| --- | --- | --- | --- | --- | --- | --- |
| `BASE` | Geprüftes Tanix-Image | `build/prepare-t95-tanix-6.18-source.sh` | Offline-Entpacken und Hash-Prüfung von Image und Rootfs | Reproduzierbare, unveränderte Eingabe | Image-Version, Layout und Rootfs-Hash | `sha256sum`, `e2fsck -fn` |
| `BOOT` | Generischer Allwinner-Bootpfad | `build/patches/0001-t95-axp313-h616-fel-bringup.patch`, `build/build-t95-ac300-ext4boot.sh` | T95-TOC0-/U-Boot-Loader; SD-Boot ab Byte 8192 und `mmc 0:1` | Boot-ROM und U-Boot der T95 bedienen | SoC, Boot-ROM-Vertrag, SD-Offset, DRAM | U-Boot-Banner, FEL-/SD-Kaltstart, Loader-Header `TOC0.GLH` |
| `TFA` | Passende TF-A-Version | `build/build-t95-ac300-ext4boot.sh` | BL31 wird mit dem T95-U-Boot gepaart | Stabiler Übergang aus SPL/U-Boot | SoC-Plattform und BL31-Kompatibilität | Commit- und Artefakt-Hash |
| `DTB` | Tanix-TX6s-/AXP313-DTB | `build/build-t95-tanix-6.18-dtb.sh` | Board-Identität wird als T95 ergänzt; H616-/AC300-Kompatibilität bleibt erhalten | Eindeutige DTB-Auswahl ohne unnötigen Kernelumbau | reale Platine, PHY-Adresse, MDIO, Clocks, Reset | `fdtget`, dekompilierte DTS, DTB-Hash |
| `ENV` | Generische Armbian-Bootauswahl | `build/assemble-t95-tanix-6.18-ext4-image.sh` und erzeugtes `armbianEnv.txt` | T95-DTB, serielle Konsole, ext4-Root und belegte Diagnoseparameter | Kernel mit dem passenden Hardwaremodell starten | Kernelpfad, Root-UUID und Konsole | Inhalt und Hash von `armbianEnv.txt`, UART-Log |
| `AXP313` | Boardabhängige SPL-/DRAM-Initialisierung | `build/patches/0001-t95-axp313-h616-fel-bringup.patch` | AXP313A-PMIC und 2-GiB-DRAM-Timing der geprüften Platine; 600 MHz | Speicher vor U-Boot zuverlässig initialisieren | RAM-Typ, Kapazität, PMIC-Spannung und Frequenz | SPL meldet `DRAM: 2048 MiB`; Kaltstart |
| `AC300` | Ethernet nicht für jede T95-Revision garantiert | `build/patches/0002-t95-ac300-preinit-command.patch` und T95-DTB | AC300-EPHY/RMII-Vorinitialisierung und PHY-Beschreibung | `end0`, Link und DHCP ermöglichen | PHY, Reset, Clock, MAC, MDIO und Linkgeschwindigkeit | Kernel-Log, Link/DHCP, `iperf3` |
| `KMOD` | Kernel-Userspace bleibt Armbian-Standard | historische Kompatibilität in `build/patches/0003-linux-6.12-ac300-phy-compat.patch`; 6.18 nutzt den vorhandenen Treiberpfad | Kein neuer finaler Kernel; experimentelle Initramfs-/Treiberstände sind Diagnosematerial | Änderungen am Kernel auf das Notwendige begrenzen | Kernel-ABI, Modulpfad und Initramfs-Reihenfolge | `modinfo`, Initramfs-Inventar, UART-Log |
| `HARDEN` | Rohimage ist nicht als öffentlicher Zugangspunkt gedacht | `build/harden-t95-release-image.sh`, `build/audit-t95-generic-release-image.sh` | Rootkonto sperren, Hostkeys entfernen, Erzeugung vor `sshd`, leere machine-id und bereinigte freie Blöcke | Keine lokalen Zugangsdaten im öffentlichen Asset | Härtung nach jedem Image-Update erneut prüfen | Härtungsmanifest, Read-only-Audit, Geheimnisscan |
| `RELEASE` | Kein Image im Git-Verlauf | `build/create-t95-release-asset.sh`, `tools/write-t95-release-image-to-sd.sh` | Geprüftes Image wird als versioniertes Release-Asset mit Manifest und Hash bereitgestellt | Sichere Verteilung und SD-Schreibvorgang | Zielgerät stets mit `lsblk` ermitteln; nur wechselbare SD | SHA-256, Größen-/TOC0-/ext4-Prüfung |
| `SAMBA` | Nicht Bestandteil des Minimalimages | `server/samba-usb/` | Nachgelagerte Samba-/USB-Automount-Schicht | Dateifreigaben erst nach stabilem Linux/Netzwerk | Pakete, Mountregeln, Benutzer und USB-Dateisystem | Installations- und Restore-Checklisten |

## Was unverändert bleibt

- Debian-/Armbian-Userspace und der geprüfte 6.18-Kernel werden als Basis
  übernommen; ein Kernel-Neubau ist für das finale 6.18-Image nicht erforderlich.
- Die interne eMMC wird vom öffentlichen Releaseweg weder gelesen noch
  überschrieben. Sie kann nach dem Boot als separates ext4-Datenlaufwerk genutzt
  werden, ist aber kein vorausgesetztes Bootmedium.
- USB, Rootfs-Grundstruktur und Standardpakete werden nicht wegen Samba oder
  Ethernet neu erfunden. Samba ist eine optionale Nachinstallation.
- Das private Labor bleibt außerhalb des öffentlichen Repositorys: keine
  Captures, Backups, Rohimages, individuellen Hardwarekennungen oder privaten
  Schlüssel.

## Portierung auf eine andere H616-Box

1. **Baseline prüfen:** Armbian-Version, Kernel, Partitionierung und Rootfs-Hash
   festhalten (`BASE`).
2. **Bootkette isolieren:** zuerst TOC0-Header, SD-Offset, DRAM und PMIC testen
   (`BOOT`, `TFA`, `AXP313`).
3. **DTB anpassen:** nur belegte Boarddaten ändern; PHY-Adresse, Reset, Clocks,
   UART und Rootpfad mit UART-Log und Schaltbild abgleichen (`DTB`, `ENV`).
4. **Ethernet separat prüfen:** AC300/RMII und Link testen, bevor Initramfs- oder
   Samba-Schichten verändert werden (`AC300`, `KMOD`).
5. **Release härten:** jedes neue Image offline auditieren; lokale Passwörter
   ausschließlich nach dem Download bzw. vor dem eigenen SD-Schreibvorgang
   einsetzen (`HARDEN`, `RELEASE`).

Bei einem Fehler wird nur die betroffene Stufe geändert. Ein neuer Kernel oder
ein eMMC-Schreibvorgang ist kein Ersatz für fehlende Hardware-Nachweise.

## Marker in den Skripten

Öffentliche Build- und Schreibskripte verwenden kurze, einheitliche Kommentare:

- `ARMBIAN-BASE` kennzeichnet einen unveränderten Armbian-Schritt.
- `T95-CHANGE` kennzeichnet eine projektspezifische Änderung.
- `PORTING-NOTE` nennt Werte, die bei einer anderen Platine erneut geprüft
  werden müssen.

Die Marker sind Navigationshilfen und ersetzen nicht die Prüfsummen- und
UART-Nachweise in diesem Dokument.

## Pflege bei neuen Releases

1. Neue Armbian-Eingabe mit Version, Commit/Hash und Layout in `BASE` eintragen.
2. Betroffene Patch-, DTB-, Build- und Release-IDs aktualisieren.
3. Nur die geänderten Portierungsstellen markieren; Standardteile als
   `ARMBIAN-BASE` belassen.
4. Build, Audit, Geheimnisscan und Dokumentationslinks ausführen.
5. Erst danach Release-Manifest, `README.md` und dieses Inventar gemeinsam
   committen.

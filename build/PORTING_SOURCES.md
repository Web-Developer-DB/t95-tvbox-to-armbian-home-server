# Öffentliche Quellen für H616-Portierung

Diese Datei trennt reproduzierbare Quellen von lokalen Laborartefakten. Die
Werkzeuge laden ausschließlich in `build/sources/` und `build/work/`; beide
Verzeichnisse sind absichtlich nicht versioniert.

| Bestandteil | Quelle | Feste Revision / Prüfsumme | Zweck |
| --- | --- | --- | --- |
| U-Boot | `https://github.com/u-boot/u-boot.git` | `25049ad560826f7dc1c4740883b0016014a59789` | H616-SPL, eGON- und TOC0-Testloader |
| TF-A | `https://github.com/ARM-software/arm-trusted-firmware.git` | `b6c0948400594e3cc4dbb5a4ef04b815d2675808` | `bl31.bin` für `sun50i_h616` |
| Armbian-Tanix-Eingabe | vom offiziellen Armbian-Release manuell laden | Datei `Armbian_26.8.4_Tanix-tx6s-axp313_trixie_current_6.18.48_minimal.img.xz`; SHA-256 `f08a37afef45bca2b2a727b2d5e48d1d7521ff533f7ebc0ec03f52ada677870c` | Referenz-Rootfs und Tanix-DTB |

Die Armbian-Datei wird bewusst nicht automatisiert von einer unversionierten
Download-URL bezogen. Vor dem Ablegen unter `images/` müssen Dateiname und
Hash stimmen. Für eine neue Armbian-Version gelten Dateiname, Layout, Kernel
und Hash als neue Eingabe und müssen separat validiert werden.

Der T95-TOC0-Loader aus dem v1.0.0-Release ist ein getestetes Binärartefakt.
Sein historischer privater Signaturschlüssel ist nicht Teil dieses Repositories.
Ein eigener TOC0-Testloader ist daher nur mit einem selbst verwalteten lokalen
Schlüssel und ohne Zusage zur Secure-Boot-Kompatibilität möglich.

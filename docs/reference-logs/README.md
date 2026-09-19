# Bereinigte Referenzlogs

Diese Dateien enthalten nur die relevanten Erfolgsmeldungen aus dem T95-
Bring-up. Sie sind **keine** vollständigen Rohaufzeichnungen und wurden von
privaten Netzwerk-, Geräte- und Kontodaten bereinigt.

| Datei | Soll-Marker | Bedeutung |
| --- | --- | --- |
| [`h616-fel-egon-success.log`](h616-fel-egon-success.log) | `soc=00001823(H616)`, `eGON.BT0`, `DRAM: 2048 MiB` | Boot-ROM/FEL, SPL und DRAM erreichen eine stabile Diagnosephase |
| [`t95-sd-linux-success.log`](t95-sd-linux-success.log) | `TOC0.GLH`, `Trying to boot from MMC1`, `Starting kernel`, `Armbian ... ttyS0` | SD-Loader, U-Boot, Kernel und Userspace starten nacheinander |

Abweichungen auf einer anderen H616-Box sind erwartbar. Den letzten
übereinstimmenden Marker mit [PORTING.md](../PORTING.md) und
[BOOT_TROUBLESHOOTING.md](../BOOT_TROUBLESHOOTING.md) abgleichen.

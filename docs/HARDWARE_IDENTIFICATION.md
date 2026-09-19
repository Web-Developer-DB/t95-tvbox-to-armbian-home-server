# Hardware-Identifikation vor dem ersten Boottest

Fotografiere die geöffnete Platine bei gutem Licht und notiere den exakten
PCB-Aufdruck. Bauteilmarkierungen sind wichtiger als Gehäusenamen.

| Bereich | Ermitteln | T95-Referenz | Nicht blind übernehmen |
| --- | --- | --- | --- |
| SoC | Chipaufdruck und Stock-Log | Allwinner H616 | H618-/H616-Varianten |
| RAM | Aufdruck aller DRAM-Chips | 2 GiB DDR3 | Typ, Größe, Takt, TPR |
| PMIC | Aufdruck, Bus, Adresse | AXP313A, `0x36` | Rails und Spannung |
| UART | GND, TX, Pegel | UART0, 3,3-V-TTL | Pinlage und Baudrate |
| Bootmedien | SD/eMMC-Aufdruck | SD `mmc0`, eMMC `mmc2` | Controller-Reihenfolge |
| Ethernet | PHY, Magnetics, Reset/Clock | AC300/RMII | PHY-Adresse/Interface |

Vor Änderungen einen Stock-Bootlog und ein read-only-Backup der
Original-Firmware anlegen. Sie können DRAM-, PMIC- und DTB-Hinweise liefern.

> [!WARNING]
> Nie 5-V-TTL oder RS-232 an UART-Pads anschließen. Erst GND bestimmen, dann
> nur `Box-TX → Adapter-RX` und GND verbinden. RX der Box bleibt für reine
> Aufnahmen zunächst unverbunden.

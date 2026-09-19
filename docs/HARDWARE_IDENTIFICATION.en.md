# Hardware identification before the first boot test

[Deutsch](HARDWARE_IDENTIFICATION.md) | **English**

Photograph the open board in good light and record the exact PCB marking.
Component markings are more important than the product name on the case.

| Area | Determine | T95 reference | Do not copy blindly |
| --- | --- | --- | --- |
| SoC | chip marking and stock log | Allwinner H616 | H618/H616 variants |
| RAM | marking on every DRAM chip | 2 GiB DDR3 | type, size, clock, TPR values |
| PMIC | marking, bus, address | AXP313A, `0x36` | rails and voltage |
| UART | GND, TX, voltage level | UART0, 3.3 V TTL | pin position and baud rate |
| Boot media | SD/eMMC markings | SD `mmc0`, eMMC `mmc2` | controller order |
| Ethernet | PHY, magnetics, reset/clock | AC300/RMII | PHY address/interface |

Before making changes, capture a stock boot log and create a read-only backup
of the original firmware. They may provide DRAM, PMIC, and DTB clues.

> [!WARNING]
> Never connect 5 V TTL or RS-232 to UART pads. Identify GND first, then
> connect only `Box TX → adapter RX` and GND. Leave the box RX disconnected
> for capture-only operation at first.

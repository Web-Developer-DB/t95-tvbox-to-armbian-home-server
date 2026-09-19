# DRAM and PMIC: determine values, do not guess

[Deutsch](DRAM_PMIC.md) | **English**

The T95 reference uses DDR3, 2 GiB, 600 MHz, and AXP313A DCDC3 at 1.36 V.
These values are confirmed only for the tested board.

| T95 parameter | Verify for other boards |
| --- | --- |
| DDR3 and 600 MHz | actual type, width, capacity, and stock clock |
| ODT/DRI/TPR10–12 | stock log, original DTB/boot files, vendor kernel |
| AXP313A at `0x36` | PMIC chip, bus address, and regulators |
| DCDC3 1360 mV | DRAM rail from a reliable source |

If SPL stops before a DRAM message or reports an implausible size, investigate
only DRAM and PMIC parameters. Kernel, root filesystem, Ethernet, and Samba are
not relevant at this stage.

> [!CAUTION]
> Do not increase voltages by trial and error. Without reliable evidence,
> remain with volatile FEL tests and do not write SD or eMMC.

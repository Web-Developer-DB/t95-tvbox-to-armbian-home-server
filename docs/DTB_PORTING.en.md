# DTB porting: only after a stable FEL/DRAM test

[Deutsch](DTB_PORTING.md) | **English**

The Device Tree describes the specific board. It cannot replace a suitable
SPL/U-Boot loader. If U-Boot prints no banner or DRAM cannot be initialized,
check [FEL](FEL_BRINGUP.en.md) and [DRAM/PMIC](DRAM_PMIC.en.md) first.

## Safe procedure

1. Choose the closest available upstream or Armbian DTB as a starting point.
2. Add only confirmed hardware nodes: UART, SD, eMMC, PMIC, RAM parameters,
   Ethernet PHY, and USB ports that actually exist.
3. Build the DTB with the `dtc` matching the kernel version and inspect it
   with `fdtdump` or `fdtget` before use.
4. Test the new DTB with the unchanged root filesystem first. Do not replace
   kernel, root filesystem, and DTB at the same time.
5. Preserve the complete UART log and enable further components only after a
   stable kernel start.

## Ethernet is especially board-dependent

The tested T95 uses the Allwinner AC300 EPHY through RMII. Another H616 box
may differ in PHY address, reset GPIO, clock, supply, or even PHY model. The
expected kernel markers for the tested variant are `end0`, a detected PHY, and
a link status. These markers do **not** prove that the T95 DTS is correct for
another board.

| UART observation | Likely layer | Next safe step |
| --- | --- | --- |
| Kernel starts, no `end0` | DTB/MAC node | compare `aliases`, MAC node, and compatible Ethernet controller |
| `end0` exists, link stays down | PHY/RMII/reset/clock | verify PHY address and reset/clock signals; do not change Samba or DHCP |
| Link up, no address | userspace | inspect DHCP using `ip -br addr` and `journalctl -u NetworkManager` |
| USB, audio, or Wi-Fi fails | individual peripheral node | disable the node separately or verify it against board evidence |

## Stop criteria

- Do not try random GPIO, PHY, or voltage values.
- On kernel panic, filesystem errors, or repeated DRAM failures, return to the
  last working DTB.
- Leave the internal eMMC unchanged throughout porting.

Continue with [UART-based boot troubleshooting](BOOT_TROUBLESHOOTING.en.md).

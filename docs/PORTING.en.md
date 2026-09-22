# Porting an H616 TV box: safe bring-up path

[Deutsch](PORTING.md) | **English**

This guide is for developers working with a similar but not exactly tested
H616 TV box. The v1.0.1 image is approved only for
`H616-T95MAX-AXP313A-V3.0`.

> [!CAUTION]
> Before every test, back up a known-good SD card, preserve the original
> firmware and stock boot log, connect 3.3 V TTL UART, and leave the eMMC
> untouched. An unstable 5 V supply can look like a DRAM or boot failure.

| Stage | Goal | Success criterion | If it fails |
| --- | --- | --- | --- |
| 0 | Preserve the original state | Photos, PCB marking, and stock log exist | do not flash |
| 1 | Inventory the hardware | SoC, RAM, PMIC, UART, storage, and PHY are known | [Inventory](HARDWARE_IDENTIFICATION.en.md) |
| 2 | Verify UART | Stock output at 115200/8N1 | [UART](UART_BRINGUP.en.md) |
| 3 | Detect FEL | H616 is visible over USB | [FEL](FEL_BRINGUP.en.md) |
| 4 | Build eGON | `eGON.BT0`, no media operation | [DRAM/PMIC](DRAM_PMIC.en.md) |
| 5 | Evaluate the RAM test | plausible DRAM size | change DRAM/PMIC only |
| 6 | Optional TOC0 SD test | local key only | document Secure Boot behavior |
| 7 | Kernel and DTB | kernel reaches the root filesystem | [DTB](DTB_PORTING.en.md) |
| 8 | Network and services | PHY, DHCP, and SSH | add Samba only afterwards |

## Public build chain

```bash
bash build/setup-h616-porting-host.sh --check
bash build/fetch-h616-porting-sources.sh
bash build/build-h616-fel-egon.sh
```

The standard path creates host files only under `build/work/` and
`build/artifacts/`. It opens no SD card or eMMC and executes no FEL USB
command. The T95 profile is a reference profile, not proof for other hardware.

An optional TOC0 SD candidate is deliberately separate and requires a local
key:

```bash
bash build/build-h616-toc0-test.sh --key /absolute/path/test-root-key.pem
```

Secure Boot may reject the result. The script does not generate, publish, or
copy a key into the repository.

Further references: [UART](UART_BRINGUP.en.md), [FEL](FEL_BRINGUP.en.md),
[DRAM/PMIC](DRAM_PMIC.en.md), [DTB](DTB_PORTING.en.md),
[troubleshooting](BOOT_TROUBLESHOOTING.en.md), and
[sanitized logs](reference-logs/README.en.md).

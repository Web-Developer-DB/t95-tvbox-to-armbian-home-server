# Sanitized reference logs

[Deutsch](README.md) | **English**

These files contain only the relevant success messages from the T95 bring-up.
They are **not** complete raw captures and have been sanitized to remove
private network, device, and account data.

| File | Expected markers | Meaning |
| --- | --- | --- |
| [`h616-fel-egon-success.log`](h616-fel-egon-success.log) | `soc=00001823(H616)`, `eGON.BT0`, `DRAM: 2048 MiB` | Boot ROM/FEL, SPL, and DRAM reach a stable diagnostic phase |
| [`t95-sd-linux-success.log`](t95-sd-linux-success.log) | `TOC0.GLH`, `Trying to boot from MMC1`, `Starting kernel`, `Armbian ... ttyS0` | SD loader, U-Boot, kernel, and userspace start in sequence |

Differences on another H616 box are expected. Match the last corresponding
marker against [PORTING.en.md](../PORTING.en.md) and
[BOOT_TROUBLESHOOTING.en.md](../BOOT_TROUBLESHOOTING.en.md).

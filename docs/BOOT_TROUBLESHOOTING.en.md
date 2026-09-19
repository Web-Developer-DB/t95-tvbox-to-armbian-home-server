# Boot troubleshooting with UART

[Deutsch](BOOT_TROUBLESHOOTING.md) | **English**

This sequence prevents an early boot failure from being mistaken for a
kernel, network, or Samba problem. Visible HDMI output does not replace a UART
log.

## Failure chain

| Last visible marker | Classification | Check | Do not do |
| --- | --- | --- | --- |
| No text, including in FEL | wiring, voltage level, or power | 3.3 V TTL, GND, crossed RX/TX, 115200 8N1, power supply | connect 5 V TTL or RS-232 |
| FEL is not detected | OTG/Boot ROM path | powered-off device, OTG port, UBOOT button only with board evidence | erase eMMC |
| `eGON.BT0` starts, no `DRAM:` | SPL, PMIC, or DRAM | PMIC, DRAM type/clock, and board parameters | change DTB or root filesystem |
| `DRAM:` visible, no U-Boot banner | SPL/U-Boot transition | BL31/U-Boot pair, build header, UART | reinstall Linux |
| U-Boot banner, no `Starting kernel` | SD path, DTB, or boot script | boot partition, `armbianEnv.txt`, root UUID | select eMMC as boot target |
| Kernel starts, root filesystem missing | root device or filesystem | `root=`, PARTUUID/UUID, ext4 integrity | investigate DHCP or Samba |
| Login visible, no network | PHY/DTB/userspace | `end0`, link, DHCP journal | replace the bootloader |

## Capture a log

The RP2040 adapter and capture program belong to the separate
[`rp2040-zero-uart-adapter`](https://github.com/Web-Developer-DB/rp2040-zero-uart-adapter)
project. After setting it up:

```bash
python3 tools/capture_uart.py /dev/ttyACM0 \
  --baud 115200 --duration 180 --prefix captures/boot
```

Power on the target only after recording has started. Save the log as text;
before publishing it, remove IP and MAC addresses, UUIDs, serial numbers,
local paths, and credentials.

## Reference

Sanitized expected markers are available under
[`docs/reference-logs/`](reference-logs/README.en.md). They classify the boot
stage but do not replace measurements on the actual board.

## Stop and return path

Do not combine multiple changes when the failure is unknown. Insert the known-
good SD card, preserve the original firmware backup, leave eMMC unchanged, and
return to the porting stage indicated by the last unambiguous UART marker.

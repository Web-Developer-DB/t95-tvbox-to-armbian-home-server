# FEL bring-up without flashing

[Deutsch](FEL_BRINGUP.md) | **English**

FEL is a volatile Allwinner USB mode. Powering off removes the RAM state. This
stage is for identification and the later eGON test, not for overwriting eMMC.

How FEL is activated depends on the board. After connecting the OTG port:

```bash
lsusb | grep -i allwinner
sunxi-fel version
```

The T95 reported `1f3a:efe8` and `soc=00001823(H616)`. No device or a timeout
is a stop criterion: verify cable, OTG port, button, power supply, and SoC
first.

`bash build/build-h616-fel-egon.sh` creates an `eGON.BT0` candidate but does
not upload it. On secured H616 devices, generic `sunxi-fel uboot` may fail at
the Secure-FEL handoff. That does not prove a RAM or DTB problem. Continue only
after checking the appropriate uploader and Boot ROM behavior.

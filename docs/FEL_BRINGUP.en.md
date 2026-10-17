<a id="fel-bring-up-without-flashing"></a>

# 🔌 FEL bring-up without flashing

[Deutsch](FEL_BRINGUP.md) | **English**

FEL is a volatile Allwinner USB mode. Powering off removes the RAM state. This
stage is for identification and the later eGON test, not for overwriting eMMC.

FEL activation depends on the board. Connect the appropriate OTG port to the Linux PC, then check detection below.

| Observation | What next? |
| --- | --- |
| 🔎 USB device detected | T95 reference: `1f3a:efe8`; also check the SoC with `sunxi-fel version` |
| ✅ H616 identified | Reference: `soc=00001823(H616)`; then choose the matching diagnostic path |
| 🛑 No device or timeout | Stop; check cable, OTG port, button, supply, and SoC |

<a id="check-usb-detection"></a>

## 🔎 Check USB detection

**On the Linux PC with the FEL box connected; appropriate USB access permissions required:**

```bash
lsusb | grep -i allwinner
sunxi-fel version
```

Compare both responses with the markers in the table. Without matching detection, stop here and check the connection.

`bash build/build-h616-fel-egon.sh` creates an `eGON.BT0` candidate but does
not upload it. On secured H616 devices, generic `sunxi-fel uboot` may fail at
the Secure-FEL handoff. That does not prove a RAM or DTB problem. Continue only
after checking the appropriate uploader and Boot ROM behavior.

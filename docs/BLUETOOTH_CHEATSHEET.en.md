# Bluetooth cheat sheet: discover, pair, disconnect

[Deutsch](BLUETOOTH_CHEATSHEET.md) | **English**

**Run on: T95, normal SSH user.** Use `sudo` only where shown; installed
helpers handle required elevation. Short `t95-bluetooth` commands require
[Bluetooth installation](../server/bluetooth/README.en.md).
`AA:BB:CC:DD:EE:FF` represents your device's actual address.

**Worked example with scan results and a concrete headphone selection:**
[Discover → connect → choose audio → disconnect or forget](../server/bluetooth/README.en.md#pair-headphones-and-choose-their-output).
The example distinguishes commands in the interactive Bluetooth prompt from
commands in the normal SSH shell.

## 1. Find adapters and USB devices

```bash
lsusb
lsusb -t
bluetoothctl list
bluetoothctl show
rfkill list bluetooth
```

`lsusb` lists USB hardware/IDs, not wireless headphones; `lsusb -t` shows
USB topology, drivers, and negotiated speeds. A USB Bluetooth dongle appears
there. The internal BCM43342 uses **UART**, so inspect it with
`bluetoothctl list` instead. A USB Wi-Fi stick need not include Bluetooth.

Optional kernel-device inspection:

```bash
for device in /sys/class/bluetooth/hci*; do
  [ -e "$device" ] || continue
  printf '%s: ' "${device##*/}"
  readlink -f "$device/device"
done
```

For multiple controllers, open `sudo bluetoothctl`, use `list`, then
`select CONTROLLER-ADDRESS`. Controller and headphone addresses are different. The remote device
is chosen by its address in `pair`/`connect`; `select` chooses the local adapter.

## 2. Pair new headphones

Put headphones into **pairing mode**, not merely powered on. Disconnect
phones/PCs first. In the normal SSH shell:

```bash
t95-bluetooth pair
```

In the resulting **bluetoothctl prompt**, enter commands sequentially. Allow
about 15–30 seconds for scanning and use the discovered name/address:

```text
power on
agent on
default-agent
scan on
devices
pair AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
info AA:BB:CC:DD:EE:FF
scan off
quit
```

Confirm any pairing request. Expect `Paired: yes`, `Trusted: yes`, and
`Connected: yes`. Trust permits later known-device connections. Keep the
Bluetooth session open until finished so discovery and the agent remain active.

Back in the **normal SSH shell**, select the audio output:

```bash
t95-bluetooth audio AA:BB:CC:DD:EE:FF
```

Without helpers, `sudo bluetoothctl` opens the same prompt, but audio packages
and the player still need setup.

## 3. Manage known devices

**Normal T95 SSH shell:**

| Purpose | Command |
| --- | --- |
| List known devices | `bluetoothctl devices` |
| Inspect state | `bluetoothctl info AA:BB:CC:DD:EE:FF` |
| Reconnect | `sudo bluetoothctl connect AA:BB:CC:DD:EE:FF` |
| Disconnect only | `sudo bluetoothctl disconnect AA:BB:CC:DD:EE:FF` |
| Remove trust, keep pairing | `sudo bluetoothctl untrust AA:BB:CC:DD:EE:FF` |
| Forget pairing on the box | `sudo bluetoothctl remove AA:BB:CC:DD:EE:FF` |

Disconnecting preserves pairing and allows automatic reconnection. Removal
forgets the local pairing; for a new pairing you may also need to forget the
box on the headphones. Use `connect` for an existing pairing; `pair` can renew it.

## 4. Use headphones on the PC instead

On the T95:

```bash
t95-bluetooth off
```

Connect on the PC; the server and Samba keep running. To switch back,
disconnect on the PC, then run on the T95:

```bash
t95-bluetooth on
sudo bluetoothctl connect AA:BB:CC:DD:EE:FF
```

Use `t95-bluetooth restart` for a radio restart (music stays stopped), or
`t95-bluetooth status` to inspect state. `off` blocks **all** box controllers,
preserves pairing, and does not guarantee the same radio state after reboot;
run `on` if needed.

## 5. No devices discovered

Check pairing mode, distance, and phone/PC connections first. Inspect
`t95-bluetooth status` and `rfkill list bluetooth`; software cannot clear a
hardware block. Run `t95-bluetooth restart`, then scan with an open
`bluetoothctl` session. **T95 · normal user with `sudo` for logs:**

```bash
sudo journalctl -u bluetooth -b --no-pager -n 60
sudo dmesg | grep -Ei 'Bluetooth|hci0|btbcm|firmware' | tail -n 60
```

For `firmware Patch file not found` or `No default controller available`,
check [requirements](../server/bluetooth/README.en.md#technical-requirements-and-evidence).
Do not download arbitrary firmware or unload Wi-Fi/Bluetooth drivers on speculation.

[BlueZ command reference](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html)

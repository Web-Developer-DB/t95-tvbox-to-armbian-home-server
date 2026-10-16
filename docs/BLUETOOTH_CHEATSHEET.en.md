# Bluetooth made simple

[Deutsch](BLUETOOTH_CHEATSHEET.md) | **English**

This guide covers everyday headphone and Bluetooth-speaker tasks on your
T95. You do not need to memorize Linux commands. The box must already be set
up and the [Bluetooth player installed](../server/bluetooth/README.en.md).

## Start here: connect to the box

1. Search your computer's application menu for **Terminal** and open it.
   On Windows, search the Start menu for **PowerShell** instead.
2. Log in to the T95 as your normal user. Find your username and the box's IP
   address from [base installation](INSTALLATION.en.md#4-first-ssh-login-and-normal-user).
   **Adapt this example before entering it:** `alex` is an example username
   and `192.168.178.50` an example box address.

   ```bash
   ssh alex@192.168.178.50
   ```

3. Enter that user's Linux password and press **Enter**. No characters or
   stars appear while typing; this is normal. Check any SSH host-key prompt
   as described in base installation.

**You are in the right place when** the input line looks like `alex@t95:~$`.
Your names and appearance may differ. **All remaining commands on this page
run in this T95 connection**, even though the window is on your computer.

Using these examples:

- Copy a command, paste it into the window, and press **Enter**. For multiple
  lines, execute each line individually.
- Boxes marked **“Example response”** are for reading only. All names and
  device addresses here are fictional.
- When asked for a **device address**, paste your headphones' address from
  the device list, such as `AA:BB:CC:DD:EE:01`, then press Enter. You do not
  need to edit the provided command lines for those prompts.
- `sudo` allows a command to change the connection. If asked for a password,
  use your T95 Linux password.
- If you see `[bluetooth]#` or, for example, `[MX42H]#`, you are still inside
  the Bluetooth program. Enter `quit` to return to normal input. Only
  [first-time pairing](#connect-new-headphones-for-the-first-time) explicitly
  keeps you inside that program.

## Choose your task

| You want to | Go here |
| --- | --- |
| See devices remembered by the box | [Show paired devices](#show-paired-devices) |
| See what is connected now | [Show connected devices](#show-connected-devices) |
| Use familiar headphones again | [Reconnect and choose music output](#reconnect-and-choose-music-output) |
| End today's connection | [Disconnect only](#disconnect-only) |
| Use headphones with a PC or phone | [Pause box Bluetooth](#use-headphones-with-a-pc-or-phone) |
| Find new headphones | [Discover and pair](#connect-new-headphones-for-the-first-time) |
| Delete headphones from the box | [Forget a device permanently](#forget-a-device-permanently) |
| Solve a problem | [If something goes wrong](#if-something-goes-wrong) |

**Paired** means the box remembers the device. **Connected** means the radio
link is active now. Paired headphones can be switched off and still appear
in the remembered-device list.

Paused Bluetooth with `t95-bluetooth off`? Run `t95-bluetooth on` before
listing, discovering, or connecting devices again.

<a id="3-manage-known-devices"></a>

## Show paired devices

**Enter on the T95:**

```bash
bluetoothctl devices Paired
```

**Example response — read only:**

```text
Device AA:BB:CC:DD:EE:01 MX42H
Device AA:BB:CC:DD:EE:02 Living-Room-Speaker
```

Two devices are remembered. The **name is on the right**; the **device
address is in the middle**. In this example, `MX42H` has address
`AA:BB:CC:DD:EE:01`. Use your actual output's address. A device address is
not the T95's IP address.

**No device lines?** No paired devices are listed for the selected adapter.
Use [discovery and pairing](#connect-new-headphones-for-the-first-time) for
new headphones. For an error message instead, open [help](#if-something-goes-wrong).

## Show connected devices

**Enter on the T95:**

```bash
bluetoothctl devices Connected
```

**Example response — read only:**

```text
Device AA:BB:CC:DD:EE:01 MX42H
```

These headphones are connected now. An empty list means no device is
currently connected. Connecting alone does not start music.

For details, **enter this command first**:

```bash
read -r -p 'Device address from the list: ' BT_GERAET
```

When prompted, enter the device address and press Enter.
**Then retrieve the details:**

```bash
bluetoothctl info "$BT_GERAET"
```

**Reading the important response fields:**

| Field | Meaning |
| --- | --- |
| `Name: MX42H` | Name of the selected device |
| `Paired: yes` | Device is paired and remembered |
| `Connected: yes` | Device is connected now |
| `Connected: no` | Device is disconnected now |
| `Trusted: yes` | The box trusts this configured device |

## Reconnect and choose music output

1. Power on the headphones. Disconnect their phone/PC connection there to
   make them available to the box.
2. Find their address under [paired devices](#show-paired-devices).
3. **Turn Bluetooth on, on the T95:**

   ```bash
   t95-bluetooth on
   ```

4. **Enter this line.** When prompted, enter your headphones' address
   and press Enter:

   ```bash
   read -r -p 'Your headphones address: ' BT_GERAET
   ```

5. **Then connect and check the result:**

   ```bash
   sudo bluetoothctl connect "$BT_GERAET"
   bluetoothctl info "$BT_GERAET"
   ```

**Success:** the response includes `Connected: yes`. If connection fails,
continue with [help](#if-something-goes-wrong).

To send music to those headphones, enter **in the same window**:

```bash
t95-bluetooth audio "$BT_GERAET"
```

**Success:** the helper reports `Kopfhörer als MPD-Ausgang gewählt` (headphones
selected as MPD output). It remembers them, sets output volume to 20%, and
initially stops playback. MPD is the box's music player. If its queue already
contains tracks, start with `mpc play`. For your first library, see
[playing music](MUSIKPLAYER_CHEATSHEET.en.md#scan-and-play-music).
A connected device without audio support cannot serve as headphones.

The prompted address is remembered only for subsequent commands in this
window. When you open a new connection to the box later, start this section
again at step 1. Remembered headphones do not need pairing again.

## Disconnect only

Use this when the box should keep remembering the headphones. Find their
address under [connected devices](#show-connected-devices).
**On the T95, run this line first and answer the device prompt:**

```bash
read -r -p 'Device address to disconnect: ' BT_GERAET
```

**Then stop music, disconnect, and check:**

```bash
mpc stop
sudo bluetoothctl disconnect "$BT_GERAET"
bluetoothctl info "$BT_GERAET"
```

**Success immediately afterward:** `Connected: no`, while `Paired: yes`
remains. Music is stopped. You can [reconnect](#reconnect-and-choose-music-output)
later. Other devices and Samba remain available. If headphones automatically
reconnect, use the Bluetooth pause below.

<a id="4-use-headphones-on-the-pc-instead"></a>

## Use headphones with a PC or phone

**Enter on the T95:**

```bash
t95-bluetooth off
```

Now connect the headphones to the PC or phone. The box stops music and turns
**all its Bluetooth radio off**. Pairings remain; file serving and Samba keep
running.

Later, disconnect on the PC/phone first, then follow
[reconnect](#reconnect-and-choose-music-output). Its `t95-bluetooth on` command
turns radio back on. After reboot, radio state may differ; turn it on if needed.

<a id="2-pair-new-headphones"></a>

## Connect new headphones for the first time

### A. Prepare the headphones

Enable **pairing mode** according to the headphones' instructions. Merely
turning them on often is not enough. Disconnect other devices first.
**Enter in the normal T95 window:**

```bash
t95-bluetooth pair
```

### B. Start discovery

The Bluetooth program is now open, with a prompt such as `[bluetooth]#`.
**Enter only these commands, each individually:**

```text
power on
agent on
default-agent
scan on
```

Wait about 15–30 seconds. The program finds discoverable devices in range.
**Fictional example response — read only:**

```text
Discovery started
[NEW] Device AA:BB:CC:DD:EE:01 MX42H
[NEW] Device AA:BB:CC:DD:EE:02 Work-PC
[NEW] Device AA:BB:CC:DD:EE:03 Living-Room-Speaker
```

The example headphones are `MX42H`. For different headphones, use their name
and address from your output. Enter `devices` to list discovered and known
devices again. Results can include devices without audio support.

### C. Remember and connect the discovered headphones

**You are still inside the Bluetooth program.** Replace
`AA:BB:CC:DD:EE:01` below with your headphones' address. Send each line
individually. If asked to confirm with `yes/no`, check that it is your device,
then enter `yes` and press Enter. If both devices display a number, check
that the numbers match.

```text
pair AA:BB:CC:DD:EE:01
trust AA:BB:CC:DD:EE:01
connect AA:BB:CC:DD:EE:01
info AA:BB:CC:DD:EE:01
```

**Success:** `Paired: yes` and `Connected: yes` mean remembered and connected;
`Trusted: yes` indicates configured trust. If a command fails, read
[help](#if-something-goes-wrong) first.

### D. Stop discovery and return to normal input

**Still inside the Bluetooth program, enter individually:**

```text
scan off
quit
```

Normal T95 input returns. Enter this line **there**, answering the prompt
with the same device address:

```bash
read -r -p 'Address of the headphones just connected: ' BT_GERAET
```

**Then choose the headphones for music:**

```bash
t95-bluetooth audio "$BT_GERAET"
```

The helper confirms the choice and initially stops playback. Prepare music
using the [player guide](MUSIKPLAYER_CHEATSHEET.en.md). Next time,
[reconnect](#reconnect-and-choose-music-output) is sufficient.

## Forget a device permanently

Use this when the box should stop remembering those headphones.
Find their address under [paired devices](#show-paired-devices) first.
**On the T95, run this line first and answer the device prompt:**

```bash
read -r -p 'Device address to forget: ' BT_GERAET
```

**Then stop music, forget the device, and check the list:**

```bash
mpc stop
sudo bluetoothctl remove "$BT_GERAET"
bluetoothctl devices Paired
```

**Success:** the device no longer appears in the paired list. Other pairings
and music remain. A later scan can rediscover it; use requires pairing again.
You may also need to forget the old box connection on the headphones.

The music player remains installed. To remove it completely, use the
separate [uninstallation guide](../server/bluetooth/README.en.md#remove-the-player-and-disable-bluetooth).

<a id="5-no-devices-discovered"></a>

## If something goes wrong

| You see | What to do |
| --- | --- |
| Nothing appears while typing a password | Normal: finish typing and press Enter. |
| `command not found` for `t95-bluetooth` | Check that you are logged into the T95 and [Bluetooth is installed](../server/bluetooth/README.en.md). |
| `[bluetooth]#` instead of normal input | Enter `quit`; `sudo`, `read`, and `t95-bluetooth` commands belong in normal input. |
| `Device ... not available` | Copy the full address from your list and power on the headphones. For a new device, discover and pair first. |
| Headphones missing during discovery | Check pairing mode, distance, and existing phone/PC connections; search again. |
| `Waiting to connect to bluetoothd...` without progress | Press **Ctrl+C** to cancel. Run `t95-bluetooth on` in normal T95 input, then retry. |
| `No default controller available` | Run `t95-bluetooth on` in normal T95 input, then retry. For a persistent error, use technical diagnosis below. |
| `Connected: no` after attempting connection | Power on headphones, disconnect other devices, and repeat “Reconnect.” |
| Connected but silent | Choose those headphones with `t95-bluetooth audio` and their address; this initially stops playback. Start a populated queue with `mpc play`. More help: [music player](MUSIKPLAYER_CHEATSHEET.en.md#no-sound-or-button-response). |
| Device reconnects after disconnection | `t95-bluetooth off` pauses the box's Bluetooth radio. |

When finished, enter `exit` to log out of the T95. This does not turn off
the box or stop music that is already playing.

<a id="1-find-adapters-and-usb-devices"></a>

<details>
<summary>Technical diagnosis for experienced users</summary>

These checks are unnecessary for normal connection switching.
**Run on: T95, normal SSH user; use `sudo` only where shown.**

```bash
bluetoothctl list
bluetoothctl show
rfkill list bluetooth
lsusb
lsusb -t
```

`bluetoothctl list` shows local adapters. `select` inside interactive
`sudo bluetoothctl` chooses a local adapter; addresses in `pair`/`connect`
choose the remote device. Adapter and headphone addresses differ.
Internal BCM43342 uses UART and does not appear in `lsusb`. `lsusb` lists
USB hardware, not wireless headphones; a USB Wi-Fi stick need not include Bluetooth.

```bash
for device in /sys/class/bluetooth/hci*; do
    [ -e "$device" ] || continue
    printf '%s: ' "${device##*/}"
    readlink -f "$device/device"
done
```

For further diagnosis:

```bash
t95-bluetooth status
sudo journalctl -u bluetooth -b --no-pager -n 60
sudo dmesg | grep -Ei 'Bluetooth|hci0|btbcm|firmware' | tail -n 60
```

`t95-bluetooth restart` restarts Bluetooth and leaves music stopped. Software
cannot clear a hardware radio block. For `firmware Patch file not found`,
check [technical requirements](../server/bluetooth/README.en.md#technical-requirements-and-evidence).
Do not download arbitrary firmware or unload drivers on speculation.
`untrust ADDRESS` inside `bluetoothctl` removes trust but preserves pairing.

[BlueZ command reference for Debian Trixie](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html)

</details>

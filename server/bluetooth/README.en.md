# Bluetooth and music player on the T95

[Deutsch](README.md) | **English**

**Run on: running T95, normal SSH user with `sudo`.** Complete
[base installation, kernel holds, and SD backup](../../docs/INSTALLATION.en.md) first.

Launcher requirements: [Bash, curl, tar, Python 3, sudo](../setup/README.en.md#requirements).

> [!NOTE]
> **Review branch:** audio and headphone buttons were verified on the manual
> reference setup. The new installers passed simulated-service tests; full
> installation, removal, and cold boot on a fresh T95 SD remain open.

This setup uses the T95's **internal BCM43342 UART module** with AXP313A;
no USB Bluetooth dongle is needed. MPD sends music to Bluetooth headphones;
their playback buttons control MPD through mpDris2 and BlueZ `mpris-proxy`.

## Install

Download commands use `codex/archive-ssh-dashboard`. A later reviewed merge
requires coordinated updates of links and the default ref.

**T95 · normal SSH user with `sudo`:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/install-t95-bluetooth.sh)
```

The launcher requests your sudo password, downloads one consistent source
archive, installs packages, and configures user services. It does not start
music or pair an unknown device automatically. The default music directory
is `~/Music`; existing music is preserved.

From a [local review-branch checkout](../setup/README.en.md#local-checkout),
run at the repository root **on the T95 as normal SSH user with `sudo`**:

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER"
```

For a different music directory, choose it on the **first** installation:

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER" --music-dir "$HOME/.local/share/t95-music-test"
```

The installer does not create test tones. External music storage must already
be mounted and readable by that user. A root invocation requires `--user NAME`.
Usernames, UIDs, and Bluetooth addresses are not copied from the reference box.

## Pair headphones and choose their output

Put headphones into pairing mode; prevent their automatic connection to a
phone/PC temporarily. **T95 · normal SSH user:**

```bash
t95-bluetooth pair
```

This opens `bluetoothctl`. Enter the following **inside that Bluetooth prompt**;
replace `AA:BB:CC:DD:EE:FF` with the headphone address found during the scan.
Allow about 15–30 seconds for discovery before using the discovered address:

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

**Expected:** `info` shows `Paired: yes`, `Trusted: yes`, `Connected: yes`.
Back in the **normal T95 SSH shell**, select the actual audio output:

```bash
t95-bluetooth audio AA:BB:CC:DD:EE:FF
```

It sets MPD to those headphones, sets PipeWire volume to 20%, and stops
playback. Until the first selection, MPD uses a placeholder output. After a
profile change that changes the output name, run `audio` again. For devices
already paired, use `connect`; `pair` can renew an existing pairing.
Continue with the [music player guide](../../docs/MUSIKPLAYER_CHEATSHEET.en.md).

## Temporarily use the headphones on a PC

**T95 · normal SSH user; installed helpers handle required privileges:**

```bash
t95-bluetooth off
t95-bluetooth on
t95-bluetooth restart
t95-bluetooth status
```

Run the appropriate action, not the whole block in sequence. `off` stops the
player, blocks **all** box Bluetooth controllers, and stops BlueZ. Pairings
remain; Samba/server operation continues. `on` unblocks radio and starts
BlueZ/controller. `restart` cycles off/on and leaves music stopped.

To switch back, disconnect on the PC, run `on` on the T95, then if needed
`sudo bluetoothctl connect ADDRESS`. Reboot radio state also depends on
`systemd-rfkill` and system configuration; run `on` if necessary. Helpers work
offline after installation. `sudo bluetoothctl disconnect ADDRESS` only
disconnects one device; it may reconnect automatically.

## Remove the player and disable Bluetooth

**T95 · normal SSH user:**

```bash
t95-bluetooth remove --remove-packages
```

Alternatively, use the dedicated download launcher without a menu:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/uninstall-t95-bluetooth.sh)
```

Removal stops/disables the user's MPD, mpDris2, and `mpris-proxy`, blocks radio,
and stops/disables BlueZ. Existing configuration files are restored. A
firmware alias created by the installer is removed; a preexisting alias remains.

Only **newly installed, explicitly requested target packages** are proposed
for removal. If APT would remove other packages, that package step aborts.
Preexisting packages, shared dependencies, music, playlists, player state,
pairings, and original firmware remain. No `autoremove` or configuration
purge runs. Omitting `--remove-packages` also preserves installed target packages.

Previously running PipeWire/WirePlumber remain. **Linger remains** because
Samba/USB may use it. Helpers under `/usr/local/bin`, the cache under
`/usr/local/lib/t95-setup`, and private backups under
`/var/lib/t95-setup/bluetooth` remain for diagnosis/reinstallation. Repeated
removal is permitted. This removal intentionally disables Bluetooth/player
even if an earlier manual setup existed; it is not a full service-state rewind.

Later edits to managed files block removal. Save/check them before
deliberately using `t95-bluetooth remove --force --remove-packages`, which
overwrites those edits with the saved files.

## Technical requirements and evidence

- Target: Armbian 26.8.4/Debian Trixie, `6.18.48-current-sunxi64`, T95 H616,
  AXP313A, internal BCM43342. Board, firmware, and UART driver path are checked.
- Existing image firmware `BCM43342.hcd` is required, SHA-256
  `09970c63b7a0fc677915195923739ddac5e9ee8d589ef9f4b0ded7370684874f`.
  No proprietary firmware is redistributed or downloaded from other sources.
- Board alias: `BCM.mbox,t95-axp313.hcd -> BCM43342.hcd`. If newly created,
  only the verified Bluetooth UART device is rebound, not the Wi-Fi driver.
- Audio: PipeWire, WirePlumber 0.5, MPD PipeWire output, mpDris2, BlueZ
  `mpris-proxy`. MPD listens only on **127.0.0.1:6600**; the old system MPD
  instance is disabled to avoid conflicting with the user player.
- MPD-only client rules set `node.dont-fallback`/`node.dont-move` to prevent
  routing to another output when headphones are absent. Rule syntax was parsed
  using `pw-config`; actual hardware routing remains unverified.
- User audio works without a graphical login. WirePlumber receives a writable
  state directory; existing `~/.local/state` is not recursively reowned.
- Files and service states are journaled before changes. Failures restore
  files/service state where possible; installed/upgraded packages and linger
  may remain. `remove` can then clean the journaled setup.
- Boot parameters, CPU/RAM voltages, network, Samba, and SSH configuration are
  not configured here. The BCM43342 Wi-Fi side is not set up.

The manual reference box passed A2DP/SBC, clear test tones, and
play/pause/next/previous with MX42H headphones. The **new installers** passed
temporary-filesystem/simulated APT/systemd tests only. Real fresh-SD
installation/removal and cold boot remain open; the working box was not
uninstalled for these tests.

[Bluetooth cheat sheet](../../docs/BLUETOOTH_CHEATSHEET.en.md) ·
[Music player cheat sheet](../../docs/MUSIKPLAYER_CHEATSHEET.en.md) ·
[General help](../../docs/TROUBLESHOOTING.en.md)

Official references: [WirePlumber Bluetooth](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html),
[MPD PipeWire output](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire),
[PipeWire client rules](https://docs.pipewire.org/page_man_pipewire-client_conf_5.html),
[WirePlumber linking](https://pipewire.pages.freedesktop.org/wireplumber/policies/linking.html),
[BlueZ bluetoothctl](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html).

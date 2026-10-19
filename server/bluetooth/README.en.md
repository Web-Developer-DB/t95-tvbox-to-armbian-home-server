<a id="bluetooth-and-music-player-on-the-t95"></a>

# 🎧 Bluetooth and music player on the T95

[Deutsch](README.md) | **English**

Send music from the box to headphones or Bluetooth speakers.
**Already installed?** Open [Bluetooth made simple](../../docs/BLUETOOTH_CHEATSHEET.en.md)
for showing, connecting, disconnecting, and forgetting devices.

| Your goal | Go here |
| --- | --- |
| 🚀 Set up the player once | [Requirements](#requirements) → [Install](#install) |
| 🎧 Everyday headphone tasks | [Find, connect, and disconnect devices](../../docs/BLUETOOTH_CHEATSHEET.en.md) |
| 🎵 Play your first music | [Transfer and play a file](../../docs/MUSIKPLAYER_CHEATSHEET.en.md) |
| ↩️ Undo audio setup | [Removal and retained data](#remove-the-player-and-disable-bluetooth) |

<a id="requirements"></a>

## 📋 Requirements

For initial setup, the T95 must be running and you must be logged in as your
normal user. [Open your connection to the box](../../docs/BLUETOOTH_CHEATSHEET.en.md#start-here-connect-to-the-box).
Complete [base installation and kernel holds](../../docs/INSTALLATION.en.md) first.
A [full SD backup](../../docs/BACKUP.en.md) is optional.

For missing tools, see [preparation](../setup/README.en.md#requirements).

> [!NOTE]
> **Verified and tested:** the project maintainer tested the documented
> Bluetooth steps on **2026-10-17** and confirmed they work.
> [Test evidence and remaining individual checks](../../docs/VALIDATION.en.md#dashboard-and-bluetooth).

The matching T95 uses built-in Bluetooth; this setup does not require an
additional USB Bluetooth adapter.

> [!NOTE]
> **Rollback update, 2026-10-19:** the backup and service-baseline restoration
> described below have automated coverage; a separate T95 hardware run is still
> [pending](../../docs/VALIDATION.en.md#dashboard-and-bluetooth).

<a id="automatic-configuration-backup"></a>

## 🗂️ Automatic configuration backup

Before APT or audio configuration changes, setup creates a private archive and
journals the original content, modes, and ownership of the files it manages.
A failed backup aborts installation before the package operation.

| Saved item | Location or scope |
| --- | --- |
| Configuration archive | `/var/lib/t95-setup/bluetooth/audio-before-setup.tar.gz` |
| Automatic file rollback | File backups and SHA-256 records in the same private directory |
| Existing audio settings | Available MPD, mpDris2, PipeWire, WirePlumber, PulseAudio, Bluetooth settings and user audio units |
| Service baseline | Active/autostart state of system and user audio services |

The archive is readable only by root and must stay private. It is a reference
copy, not a system image or package-version backup. Automatic removal restores
managed files from the journal; do not blindly extract the complete archive over
an active system. An existing `~/.mpdconf` is saved, temporarily removed to avoid
conflicting MPD configuration, and restored on rollback. Repeating `install`
preserves the first backup; reinstalling after removal archives the old journal.

<a id="install"></a>

## 🚀 Install

The download commands and installer obtain their files from `main`.

**Once, on the T95:** copy the entire next line, paste it into the terminal
window connected to the box, and press Enter.

**On the T95, normal SSH user; `sudo` where shown:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/install-t95-bluetooth.sh)
```

If asked for a password, enter your T95 Linux password and press Enter.
No characters or stars appear while typing. The tool downloads the files and
installs the player. After `Fertig.`, setup is finished; continue with
[everyday use](../../docs/BLUETOOTH_CHEATSHEET.en.md). Headphones are then
selected and paired deliberately. Music is expected in your user's `Music`
folder; existing music is preserved.

<a id="verify-setup"></a>

## ✅ Verify setup

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-bluetooth status
```

**Expected:** `Setup: installed`, `Abweichende Dateien: 0`, and active Bluetooth/player
services. Headphones need not be connected yet. For errors, use
[module help](../../docs/TROUBLESHOOTING.en.md#dashboard-or-bluetooth-fails).
Next, pair/select headphones and [play your first file](../../docs/MUSIKPLAYER_CHEATSHEET.en.md).

<details>
<summary>Additional setup options for experienced users</summary>

From a [local checkout](../setup/README.en.md#local-checkout),
run at the repository root **on the T95 as normal SSH user with `sudo`**:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER"
```

For a different music directory, choose it on the **first** installation:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo python3 server/setup/t95_setup.py bluetooth install --user "$USER" --music-dir "$HOME/.local/share/t95-music-test"
```

The installer does not create test tones. External music storage must already
be mounted and readable by that user. A root invocation requires `--user NAME`.
Usernames, UIDs, and Bluetooth addresses are not copied from the reference box.

</details>

<a id="pair-headphones-and-choose-their-output"></a>

## 🎧 Pair headphones and choose their output

<a id="1-scan-the-bluetooth-surroundings"></a><a id="2-select-and-connect-the-desired-audio-device"></a><a id="3-use-the-connected-headphones-as-the-audio-output"></a><a id="4-reconnect-already-paired-headphones"></a><a id="5-temporarily-disconnect"></a><a id="6-permanently-remove-pairing-from-the-t95"></a>

The [step-by-step everyday guide](../../docs/BLUETOOTH_CHEATSHEET.en.md)
explains logging into the box, entering commands, and reading responses
without prior terminal knowledge.

| Your task | Start here |
| --- | --- |
| Find remembered devices | [Show paired devices](../../docs/BLUETOOTH_CHEATSHEET.en.md#show-paired-devices) |
| Check active connections | [Show connected devices](../../docs/BLUETOOTH_CHEATSHEET.en.md#show-connected-devices) |
| Use familiar headphones | [Reconnect and choose music output](../../docs/BLUETOOTH_CHEATSHEET.en.md#reconnect-and-choose-music-output) |
| Discover and pair new headphones | [First connection](../../docs/BLUETOOTH_CHEATSHEET.en.md#connect-new-headphones-for-the-first-time) |
| End one connection | [Disconnect, keep pairing](../../docs/BLUETOOTH_CHEATSHEET.en.md#disconnect-only) |
| Delete one device from the box | [Forget a device](../../docs/BLUETOOTH_CHEATSHEET.en.md#forget-a-device-permanently) |

<a id="temporarily-use-the-headphones-on-a-pc"></a>

## ⏸️ Temporarily use the headphones on a PC

`t95-bluetooth off` on the T95 pauses all box Bluetooth radio. Pairings are
remembered; the home server and Samba keep running. The
[everyday guide](../../docs/BLUETOOTH_CHEATSHEET.en.md#use-headphones-with-a-pc-or-phone)
walks through switching to a PC/phone and back.

<a id="remove-the-player-and-disable-bluetooth"></a>
<a id="-remove-the-player-and-disable-bluetooth"></a>
<a id="restore-the-previous-audio-setup"></a>

## ↩️ Restore the previous audio setup

This section removes the player setup. To disconnect or forget only one
headphone device, use [device controls](../../docs/BLUETOOTH_CHEATSHEET.en.md#disconnect-only).

**In the normal T95 terminal window:**

This command removes the setup and its newly added target packages:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-bluetooth remove --remove-packages
```

**Check after successful rollback — on the T95, normal SSH user:**

```bash
t95-bluetooth status
```

Expect `Setup: removed`. Read each named service against its saved baseline;
`active` alone does not indicate a leftover when that service was active before.
Shared backups and music are intentionally retained. To only pause Bluetooth,
use `t95-bluetooth off` instead of uninstalling.

Alternatively, use the dedicated download launcher without a menu:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/uninstall-t95-bluetooth.sh)
```

<details>
<summary>What removal keeps and how conflicts are handled</summary>

Removal restores the files and active/autostart states recorded before setup.
Previously running services are restarted with their restored configuration;
previously inactive services are stopped. For example, a preexisting and active
`mpris-proxy` or PipeWire service may be active again after successful removal.
The installer does not change global service enablement for all users.
A firmware alias created by setup is removed; a preexisting alias remains.

Only **newly installed, explicitly requested target packages** are removed with
`--remove-packages`, after an APT simulation rejects removing additional packages.
Preinstalled audio packages and shared dependencies remain. Upgraded package
versions are not downgraded; no `autoremove` or configuration purge runs.
Without `--remove-packages`, target packages stay installed; an inherited global
autostart that cannot be returned to its baseline causes an error rather than
an unconditional success message.

If an existing Samba/USB user service uses the session bus, `dbus-user-session`
also remains even if audio originally installed it. This runtime dependency
is not represented by APT package dependencies.

Music, playlists, pairings, original firmware, shared linger, command helpers,
source cache, and private recovery backups remain. Linger can also serve Samba/USB.
The runtime service checks must pass before `Setup: removed` is recorded.
Failure leaves a retryable state such as `restoring`, with the backup retained.

**Older installations:** the download removal launcher also reconciles journals
already marked `removed`. It preserves files changed after that earlier removal.
The old journal cannot reconstruct a radio setting it never recorded; the tool
states this explicitly. New installations save Bluetooth software blocks and,
when readable, the controller power state before changing them.

Later edits to managed files block removal. Save/check them before
deliberately using `t95-bluetooth remove --force --remove-packages`, which
overwrites those edits with the saved files.

</details>

<details>
<summary>Technical background and test evidence</summary>

<a id="technical-requirements-and-evidence"></a>

## 🛠️ Technical requirements and evidence

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
play/pause/next/previous with MX42H headphones. The setup scripts also passed
temporary-filesystem/simulated APT/systemd tests. On **2026-10-17**, the project
maintainer confirmed after testing that the documented Bluetooth steps work.
Separate fresh-SD, removal, and cold-boot checks are tracked in the
[test matrix](../../docs/VALIDATION.en.md#dashboard-and-bluetooth).

[Bluetooth cheat sheet](../../docs/BLUETOOTH_CHEATSHEET.en.md) ·
[Music player cheat sheet](../../docs/MUSIKPLAYER_CHEATSHEET.en.md) ·
[General help](../../docs/TROUBLESHOOTING.en.md)

**2026-10-19 update:** configuration backup and restoration of the previous
service state are covered by automated fixtures. This changed rollback has
not yet been confirmed by a full run on a separate T95 SD card.

Official references: [WirePlumber Bluetooth](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html),
[MPD PipeWire output](https://mpd.readthedocs.io/en/stable/plugins.html#pipewire),
[PipeWire client rules](https://docs.pipewire.org/page_man_pipewire-client_conf_5.html),
[WirePlumber linking](https://pipewire.pages.freedesktop.org/wireplumber/policies/linking.html),
[BlueZ bluetoothctl](https://manpages.debian.org/trixie/bluez/bluetoothctl.1.en.html).

</details>

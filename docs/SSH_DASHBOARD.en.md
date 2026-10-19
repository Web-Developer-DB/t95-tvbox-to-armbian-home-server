<a id="set-up-the-ssh-dashboard"></a>

# 📊 Set up the SSH dashboard

<a id="ssh-login-dashboard-install-and-restore"></a>

[Deutsch](SSH_DASHBOARD.md) | **English**

The script-installed custom dashboard adds storage information to Armbian's
login display. At each SSH login, alongside load and memory information, you see:

| Display | What it tells you |
| --- | --- |
| ✍️ **`SD-Writes`** | Amount written to SD since the last boot; starts over after a reboot. |
| 🔌 **Drives** | Mounted filesystems, including mounted USB sticks, SSDs, and hard drives: device name (e.g. `sda1`) and mount path. |
| 📊 **Storage** | Total capacity, free space, and usage per filesystem; **90% or more** is highlighted in red. |
| ⏏️ **Tips: USB quick help** | Replaces rotating promotions: when `usb-eject` is installed, shows status, eject by share name and safe-unplug guidance. |

The overview refreshes at a new SSH login. You do not need a separate web interface.

> [!TIP]
> **Already installed?** Open a new SSH connection to refresh the values. An already open window does not update automatically.

| Your goal | Go here |
| --- | --- |
| 🚀 First setup | [Requirements](#requirements) → [Set up](#set-up) |
| ✅ Check the display | [Check status and log in again](#verify-success) |
| 🧭 Already installed | [Use it](#use-it) |
| ↩️ Return to the previous state | [Remove dashboard](#remove) |

<a id="requirements"></a>

## 📋 Requirements

The T95 is running and you are logged in over SSH as a normal user.
Complete [base setup and kernel holds](INSTALLATION.en.md) first.
A [full SD backup](BACKUP.en.md) is optional.
[Launcher tools](../server/setup/README.en.md#requirements) must exist; the
launcher installs display packages.

**Tested:** the maintainer confirmed the documented dashboard steps work on
**2026-10-17**. [Test evidence](VALIDATION.en.md#dashboard-and-bluetooth).

<a id="install-and-remove"></a>

<a id="set-up"></a>

## 🚀 Set up

**On the T95, normal SSH user with `sudo`:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/install-t95-dashboard.sh)
```

Enter your T95 user's Linux password if asked. No letters or stars appear.
**Success:** setup finishes with `Fertig.`. For errors, use
[module help](TROUBLESHOOTING.en.md#dashboard-or-bluetooth-fails) first.

<a id="verify-success"></a>

## ✅ Verify success

**On the T95, normal SSH user:**

```bash
t95-dashboard status
```

**Expected:** `Setup: installed` and `Abweichende Dateien: 0`. For a different
state, use [module help](TROUBLESHOOTING.en.md#dashboard-or-bluetooth-fails).

Open a **second terminal window on the PC** and connect again. Replace sample
user `alex` and address `192.168.178.50` with your normal T95 user and router address.

**On the PC, normal user; adapt the example first:**

```bash
ssh alex@192.168.178.50
```

**Success:** the new SSH login shows the system overview. A
[redacted example](images/t95-ssh-status-redacted.png) illustrates its layout;
values and available drives vary.

<a id="use-it"></a>

## 🧭 Use it

The dashboard appears automatically at later SSH logins. It does not continuously
refresh an already open window. Continue with normal shell commands after the display.

### ⏏️ Safely remove USB drives

With the [Samba/USB extension](../server/samba-usb/README.en.md) installed,
the existing **Tips** section shows this fixed quick reference at the next
SSH login, replacing rotating Armbian recommendations:

```text
Safely remove USB drives
  Status and shares: sudo usb-eject --status
  Eject a drive:     sudo usb-eject "NAME"
  Replace NAME with the share name shown by status.
  Ejects the whole USB drive, including all its partitions.
  Finish file transfers. Unplug only after the success message.
```

The display does not run these commands. It stays hidden without `usb-eject`.
German or English follows the login session's language.
[Eject and success messages](../server/samba-usb/README.en.md#safely-eject-usb-storage).

**Add to an existing dashboard:** rerun the current dashboard launcher or use
a current repository copy from its root directory:

**On the T95, normal SSH user with `sudo`:**

```bash
sudo python3 server/setup/t95_setup.py dashboard install --user "$(id -un)"
```

For an already recorded installation this adds/updates only the USB help.
Other dashboard files, custom settings and the original backup are preserved;
no packages are reinstalled for this update. Manual changes to the managed
hint are reported. Log in again and use `t95-dashboard status` to check the
managed files. The new display is automatically tested; the
[earlier hardware confirmation](VALIDATION.en.md#dashboard-and-bluetooth)
still applies to the previously tested dashboard version.

<a id="remove"></a>

## ↩️ Remove

Run this only to undo setup.

**On the T95, normal SSH user:**

```bash
t95-dashboard remove
```

**Success:** files saved before setup are restored. Unrelated added modules remain.
If old files were identical, the display may look unchanged. Later manual edits
must be saved/checked first; `--force` overwrites those edits with the backup.
Packages remain installed by default.

<details>
<summary>Alternative removal through download</summary>

This is an alternative to local `remove`, not an additional step.

**On the T95, normal SSH user with `sudo`:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/uninstall-t95-dashboard.sh)
```

</details>

<details>
<summary>Archive, technical details, and manual restoration</summary>

<a id="archive-and-display-contents"></a>

## 📦 Archive and display contents

The **2026-10-16** archive at `server/ssh-dashboard/2026-10-16/` contains
14 actual source files, SHA-256 hashes, and Unix modes from the running T95.
Baseline: Armbian BSP 26.8.4, Debian Trixie,
`6.18.48-current-sunxi64`. Existing Armbian licenses are retained; see the
[archive notice](../server/ssh-dashboard/2026-10-16/NOTICE.md).

The [redacted capture](reference-logs/ssh-dashboard-2026-10-16.txt) preserves
the recorded display. Load, temperatures, storage, container info, tips, and
upgrade counts are snapshots and are recalculated on later logins.

| Files | Purpose |
| --- | --- |
| `10-armbian-header` | Logo, board/kernel/package status |
| `15-ap-info`, `20-ip-info`, `25-containers-info` | AP, network, containers |
| `30-armbian-sysinfo` | Load, RAM, temperature, uptime, storage |
| `35-armbian-tips`, `quotes.txt`, `41-commands` | Tips and commands |
| `95-sd-card-stats` | SD write counters and drive overview |
| `00-clear`, `98-armbian-autoreboot-warn`, `99-blank` | Other existing MOTD parts |
| `/etc/default/armbian-motd` | Display settings |
| `/usr/lib/armbian/armbian-allwinner-battery` | System-info helper |

`manifest.json` records destinations, modes, and hashes; `SHA256SUMS` checks
the same payloads. Keep unredacted captures, credentials, and private keys private.

The current setup installer uses `/etc/update-motd.d/35-armbian-tips` for
USB help. The 14 historical source files remain archived as a reference;
their capture still shows the former tips. The setup journal preserves the
original tips file and restores it on `remove`. For an older recorded
installation, setup updates only this tips component.

The launcher installs display/system packages via APT and preserves its
first backup at `/var/lib/t95-setup/dashboard`. Reinstalling does not replace
that backup. Later file edits block removal; save/check them before using
`remove --force`. `remove --remove-packages` requests checked removal of newly
added target packages only. See [shared setup](../server/setup/README.en.md).

From a [local checkout](../server/setup/README.en.md#local-checkout), an alternative
installation invocation is:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo python3 server/setup/t95_setup.py dashboard install
```

For later removal, instead of the local helper:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo python3 server/setup/t95_setup.py dashboard remove
```

<a id="manual-restore-alternative-with-preview"></a>

## 🛠️ Manual restore alternative with preview

This alternative is not an extra step after launcher installation. From the
local repository root, preview **as normal user on the Linux PC or T95**:

**On the Linux PC, normal user:**

```bash
python3 tools/restore-ssh-dashboard.py
```

To apply, run **on the T95 with `sudo`**:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo python3 tools/restore-ssh-dashboard.py --apply
```

It verifies payloads/targets, backs up existing managed files and state under
`/var/backups/t95-dashboard/<time-random>/`, then atomically installs the
14 files. Identical installation stays unchanged without an extra backup.
An installation failure restores the previous state automatically.

For rollback, replace `BACKUP-NAME` with the actual printed backup directory
and run **on the T95 with `sudo`**:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
read -r -p 'Full printed backup directory: ' T95_DASHBOARD_BACKUP
```

Enter the actual backup directory and press Enter. Then run on the T95:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo python3 tools/restore-ssh-dashboard.py --rollback "$T95_DASHBOARD_BACKUP"
```

Previous content/mode/ownership is restored; files newly introduced by the
installation are removed. SSH need not restart; the next login runs MOTD.
This manual tool uses its own backup location, separate from the new setup journal.

<a id="requirements-and-limits"></a>

## ℹ️ Requirements and limits

The target requires Armbian with `/etc/armbian-release`, Bash, Python 3.9+,
and standard SSH/PAM-MOTD integration. The reference already contains
`pam_motd.so motd=/run/motd.dynamic` and `pam_motd.so noupdate` in SSH PAM;
the authentication file is not modified. Check other distributions separately.

Modules use coreutils, awk, sed, grep, procps, iproute2, and util-linux.
`figlet` draws the logo with a text fallback. `curl` retrieves public IP
addresses. Optional `jq` has a sed fallback for tips. WLAN/container display
depends on services actually present.

The archived settings disable clear, hide typical virtual adapters, set
`STORAGE=/dev/sda1`, and use temperature offset 0. SD stats read
`/sys/block/mmcblk0/stat`; inspect both device references on another system.
No UUIDs, mounts, or disk contents are restored. Additional MOTD modules,
board/OS identities, caches, and the nonexecuted `95-sd-card-stats+` backup
are not installed. Recorded formatting quirks remain; the origin of a `28GB`
line seen only in the private full capture was not identified and is not
hardcoded by the restore tool.

<a id="verification"></a>

## 🧪 Verification

Temporary-filesystem checks covered preview, byte/mode-exact installation,
idempotence, rollback, rejected redirected targets, rejected modified
payloads, and automatic rollback after interruption. Original source collection
only read the running box; no root restore was applied during that collection.
On **2026-10-17**, the project maintainer confirmed after testing that the
documented dashboard steps work. Separate fresh-SD, removal, and cold-boot
checks are tracked in the [test matrix](VALIDATION.en.md#dashboard-and-bluetooth).
The tool does not configure boot parameters, voltages, Bluetooth, Samba,
or SSH authentication.

</details>

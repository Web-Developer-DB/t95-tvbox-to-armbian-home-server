<a id="shared-t95-setup-entry"></a>

# 🧩 Shared T95 setup entry

[Deutsch](README.md) | **English**

Install the SSH dashboard and Bluetooth music player through one menu.
They are optional additions to an already running T95; this menu does not
create an Armbian SD card or set up Samba.

| Your goal | Go here |
| --- | --- |
| 🚀 Choose and install modules | [Requirements](#requirements) → [Open menu](#quick-start-on-the-running-t95) |
| ✅ Check setup | [Check module status](#verify-success) |
| 🧭 Use the modules | [Everyday overview](../../docs/DAILY_USE.en.md) |
| ↩️ Undo one setup | [Remove a module](#remove-a-module) |

> [!NOTE]
> **Choose what to add:** dashboard, Bluetooth player, or both. The menu extends a running T95; base installation and Samba use their own guides.

<a id="requirements"></a>

## 📋 Requirements

Finish [base setup and kernel holds](../../docs/INSTALLATION.en.md)
and log in as your normal T95 user. A [full SD backup](../../docs/BACKUP.en.md)
is optional. Bash, curl, tar, Python 3, and sudo must
exist. If tools are missing, prepare them first:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo apt update
sudo apt install -y bash curl tar python3 sudo
```

The setup installs module packages afterward; the download method does not require Git.
The maintainer confirmed the documented dashboard/Bluetooth steps work on
**2026-10-17**. [Evidence and individual open checks](../../docs/VALIDATION.en.md#dashboard-and-bluetooth).

<a id="quick-start-on-the-running-t95"></a>

## 🚀 Quick start on the running T95

**On the T95, normal SSH user; `sudo` where shown:**

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/t95-setup.sh)
```

**When the menu asks for a selection, type the number and press Enter:**

| Your goal | Selection |
| --- | --- |
| Install both modules | `0` |
| Install dashboard only | `1` |
| Install Bluetooth/player only | `3` |

Enter your T95 user's Linux password if asked; no letters or stars appear.
Setup runs the selected action. With option `0`, dashboard finishes first,
then Bluetooth starts. Each installed module reports `Fertig.`.
For errors, stop and use [module help](../../docs/TROUBLESHOOTING.en.md#dashboard-or-bluetooth-fails).

<a id="verify-success"></a>

## ✅ Verify success

For the installed dashboard:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-dashboard status
```

Then open a new SSH session; see [dashboard verification](../../docs/SSH_DASHBOARD.en.md#verify-success).
For the installed player:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-bluetooth status
```

Then follow [Bluetooth made simple](../../docs/BLUETOOTH_CHEATSHEET.en.md) to pair
and select headphones, followed by [first music playback](../../docs/MUSIKPLAYER_CHEATSHEET.en.md).
Installation alone does not start music.

<a id="remove-a-module"></a>

## ↩️ Remove a module

Choose only the action you need. To restore the previous dashboard:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-dashboard remove
```

To undo the audio setup and restore its previous state:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
t95-bluetooth remove --remove-packages
```

Music and pairings remain. Read the [Bluetooth removal details](../bluetooth/README.en.md#remove-the-player-and-disable-bluetooth)
before removing it from an existing setup. Kernel holds remain enabled.

<details>
<summary>Technical behavior, local checkout, and verification</summary>

<a id="behavior-and-individual-launchers"></a>

## ⚙️ Behavior and individual launchers

The launcher downloads one GitHub source archive and runs
`server/setup/t95_setup.py` with root privileges. Bash, curl, tar, Python 3,
and sudo must already exist on the box; APT installs the module packages.
Git is unnecessary for the download method.

| Launcher under `tools/` | Fixed action |
| --- | --- |
| `install-t95-dashboard.sh` | Install dashboard |
| `uninstall-t95-dashboard.sh` | Restore the previous dashboard state |
| `install-t95-bluetooth.sh` | Install Bluetooth and music player |
| `uninstall-t95-bluetooth.sh` | Restore previous audio configuration/services and remove newly added target packages |

These launchers skip the menu. See the authoritative
[dashboard](../../docs/SSH_DASHBOARD.en.md) and
[Bluetooth](../bluetooth/README.en.md) guides for their download commands.
Options such as `--user NAME` and removal's `--force` are forwarded. Local
launchers use the adjacent shared script; downloaded ones load it from the
same Git ref.

| Component | Actions |
| --- | --- |
| `dashboard` | `install`, `remove`, `status` |
| `bluetooth` | `install`, `remove`, `status`, `pair`, `audio ADDRESS`, `off`, `on`, `restart` |

Combined installation is `bash tools/t95-setup.sh all install` from a local
checkout. Both components use one source archive and independent journals.
If the second fails, the first remains installed and can be removed separately.
Choose `--music-dir` through the separate Bluetooth invocation.

The default ref is `main`. `T95_SETUP_REF` may select
another existing branch/tag/commit in the same repository. HTTPS protects
transport; it is not an independent release signature.

<a id="local-checkout"></a>

## 📁 Local checkout

**T95 · normal SSH user with `sudo` for package preparation, then Git as that user.**
Use a separate checkout of `main`; the PC's `v1.0.1` release tools do
not include them:

**On the T95, normal SSH user; `sudo` where shown:**

```bash
sudo apt update
sudo apt install -y git
git clone --branch main --depth 1 \
  https://github.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server.git "$HOME/t95-server-tools"
cd "$HOME/t95-server-tools"
git branch --show-current
```

**Expected:** `main`, with `server/setup/t95_setup.py`
present. If the directory exists already, inspect its branch and local
changes instead of overwriting it. Local commands in module guides run from
this repository root.

<a id="state-and-removal"></a>

## ↩️ State and removal

Each component keeps a private journal at
`/var/lib/t95-setup/<component>/state.json`. Existing files are backed up with
content, mode, and owner. Repeated installation preserves the initial backup.
Later edits block removal; save/check those files before deliberately using
`remove --force`. Old journals are archived on reinstallation.

For an installed dashboard, repeating `install` replaces rotating tips with the
[USB quick help](../../docs/SSH_DASHBOARD.en.md#-safely-remove-usb-drives).
Other dashboard files and their original backups are preserved;
this update does not reinstall packages. The hint shows `usb-eject` commands
only when the tool is available.

The shared cache at `/usr/local/lib/t95-setup`, command helpers in
`/usr/local/bin`, and private backups remain for diagnosis/reinstallation.
By default packages remain. `remove --remove-packages` proposes only packages
that were absent before setup and explicitly requested by it. An APT
simulation rejects removing additional packages; new transitive dependencies
remain. Existing-package upgrades are not reverted and no `autoremove` runs.

Bluetooth removal restores the saved configuration and service baseline,
including previously running player, PipeWire, and Bluetooth services. The
private `audio-before-setup.tar.gz` reference archive and per-file backups are
created before package changes. Service failures prevent a false `removed`
status. Old removed journals can also be reconciled; a radio state missing
from an older journal cannot be reconstructed. A session-bus package needed by the existing Samba automounter is retained. Shared linger, music, pairings,
and recovery tools remain. [Backup and rollback details](../bluetooth/README.en.md#automatic-configuration-backup).

<a id="verify-before-publishing"></a>

## 🧪 Verify before publishing

**Linux PC · normal user · from the repository root:**

**On the Linux PC, normal user; repository root:**

```bash
for script in tools/t95-setup.sh tools/{install,uninstall}-t95-{dashboard,bluetooth}.sh; do bash -n "$script"; done
python3 -m unittest discover -s server/setup/tests -v
python3 tools/restore-ssh-dashboard.py
git diff --check
```

The 37 automated tests use temporary filesystems and simulated APT/systemd/BlueZ;
they do not change PC packages or services. They cover dashboard install,
idempotence, rollback, hashes, redirected targets, later edits, Bluetooth
configuration/output choice, data and firmware-alias preservation, service
failure rollback, bounded package removal, wrong hardware, offline on/off,
individual starters, and the combined menu. Ownership changes are simulated;
the original firmware payload is not copied into tests.
The USB hint is checked for German/English output, at most 80 characters per
display line, hiding without the tool and never executing shown commands.
Other cases cover updating an old dashboard's tips without APT, preserving the first
backup, rollback and protecting manual edits.

New rollback fixtures cover backup before package mutation, private archive
permissions, legacy MPD configuration, restoration of previously active services,
failed stops, false service success, failed package removal, runtime enablement,
old removed journals, rfkill-package absence, and a non-activating status query.

The MPD routing rule was additionally parsed with the reference box's
`pw-config` from a temporary file. Its syntax and properties were recognized;
actual routing with headphones absent remains unverified. No active
configuration or service was changed by that check.

The project maintainer additionally tested the documented dashboard and
Bluetooth steps on **2026-10-17** and confirmed they work. Separate fresh-SD,
removal, and cold-boot checks are tracked in the
[test matrix](../../docs/VALIDATION.en.md#dashboard-and-bluetooth).

[Bluetooth cheat sheet](../../docs/BLUETOOTH_CHEATSHEET.en.md) ·
[Music player cheat sheet](../../docs/MUSIKPLAYER_CHEATSHEET.en.md)

</details>

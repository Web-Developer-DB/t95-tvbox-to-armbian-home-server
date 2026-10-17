# Shared T95 setup entry

[Deutsch](README.md) | **English**

**Run on: T95, normal SSH user with `sudo`.** Complete
[base installation, kernel holds, and backup](../../docs/INSTALLATION.en.md)
first. This menu installs optional modules on a running box; it does not
prepare an Armbian SD or set up Samba.

> [!NOTE]
> **Verified and tested:** the project maintainer tested the documented
> dashboard and Bluetooth steps on **2026-10-17** and confirmed they work.
> [Test evidence and remaining individual checks](../../docs/VALIDATION.en.md#dashboard-and-bluetooth).

## Requirements

Bash, curl, tar, Python 3, and sudo must already exist. If missing, install
**on the T95 as normal user with sudo, after kernel holds**:

```bash
sudo apt update
sudo apt install -y bash curl tar python3 sudo
```

The setup installs actual dashboard/audio packages afterward. Git is not
needed for the download launcher.

## Quick start on the running T95

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/main/tools/t95-setup.sh)
```

Select an action; `0` installs dashboard and Bluetooth/player sequentially.
Then inspect `t95-dashboard status` or `t95-bluetooth status`. Pairing and
music require the additional [Bluetooth steps](../bluetooth/README.en.md).

## Behavior and individual launchers

The launcher downloads one GitHub source archive and runs
`server/setup/t95_setup.py` with root privileges. Bash, curl, tar, Python 3,
and sudo must already exist on the box; APT installs the module packages.
Git is unnecessary for the download method.

| Launcher under `tools/` | Fixed action |
| --- | --- |
| `install-t95-dashboard.sh` | Install dashboard |
| `uninstall-t95-dashboard.sh` | Restore the previous dashboard state |
| `install-t95-bluetooth.sh` | Install Bluetooth and music player |
| `uninstall-t95-bluetooth.sh` | Remove player, disable Bluetooth, request checked removal of newly added target packages |

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

## Local checkout

**T95 · normal SSH user with `sudo` for package preparation, then Git as that user.**
Use a separate checkout of `main`; the PC's `v1.0.1` release tools do
not include them:

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

## State and removal

Each component keeps a private journal at
`/var/lib/t95-setup/<component>/state.json`. Existing files are backed up with
content, mode, and owner. Repeated installation preserves the initial backup.
Later edits block removal; save/check those files before deliberately using
`remove --force`. Old journals are archived on reinstallation.

The shared cache at `/usr/local/lib/t95-setup`, command helpers in
`/usr/local/bin`, and private backups remain for diagnosis/reinstallation.
By default packages remain. `remove --remove-packages` proposes only packages
that were absent before setup and explicitly requested by it. An APT
simulation rejects removing additional packages; new transitive dependencies
remain. Existing-package upgrades are not reverted and no `autoremove` runs.

Bluetooth removal intentionally disables player and Bluetooth even when an
older manual setup existed; old files are restored. Shared linger and
previously running PipeWire/WirePlumber services remain. Music and pairings
are retained.

## Verify before publishing

**Linux PC · normal user · from the repository root:**

```bash
for script in tools/t95-setup.sh tools/{install,uninstall}-t95-{dashboard,bluetooth}.sh; do bash -n "$script"; done
python3 -m unittest discover -s server/setup/tests -v
python3 tools/restore-ssh-dashboard.py
git diff --check
```

The sixteen tests use temporary filesystems and simulated APT/systemd/BlueZ;
they do not change PC packages or services. They cover dashboard install,
idempotence, rollback, hashes, redirected targets, later edits, Bluetooth
configuration/output choice, data and firmware-alias preservation, service
failure rollback, bounded package removal, wrong hardware, offline on/off,
individual starters, and the combined menu. Ownership changes are simulated;
the original firmware payload is not copied into tests.

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

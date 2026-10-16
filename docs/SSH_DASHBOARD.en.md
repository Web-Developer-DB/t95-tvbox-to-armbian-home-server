# SSH login dashboard: install and restore

[Deutsch](SSH_DASHBOARD.md) | **English**

**Run on: running T95, normal SSH user with `sudo`.** Complete
[base system, kernel holds, and SD backup](INSTALLATION.en.md) first.
This dashboard displays system information at SSH login; it is not a web interface.

Launcher requirements: [Bash, curl, tar, Python 3, sudo](../server/setup/README.en.md#requirements).

> [!NOTE]
> The archived display comes from the reference box. New installation/removal
> scripts passed simulated-service tests; a full fresh-T95-SD run and cold
> boot remain open.

## Install and remove

The download commands use `codex/archive-ssh-dashboard`. On the T95:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/install-t95-dashboard.sh)
```

Inspect the state locally, then open a new SSH session to see the display:

```bash
t95-dashboard status
```

Restore the previous dashboard locally:

```bash
t95-dashboard remove
```

A separate download launcher performs the same removal without a menu:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Web-Developer-DB/t95-tvbox-to-armbian-home-server/codex/archive-ssh-dashboard/tools/uninstall-t95-dashboard.sh)
```

Removal restores files present before installation; it does not delete the
Armbian dashboard wholesale. If the prior files were identical, the restored
display looks the same. Additional unrelated MOTD modules remain.

The launcher installs display/system packages via APT and keeps the first
backup in `/var/lib/t95-setup/dashboard`. Repeated installs preserve it.
Later manual edits block removal; save/check them before `remove --force`.
Packages remain by default; `remove --remove-packages` requests checked
removal of newly added target packages only. See [shared setup](../server/setup/README.en.md).

From a [local review-branch checkout](../server/setup/README.en.md#local-checkout),
run at the repository root **on the T95 as normal SSH user with `sudo`**:

```bash
sudo python3 server/setup/t95_setup.py dashboard install
sudo python3 server/setup/t95_setup.py dashboard remove
```

## Archive and display contents

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

## Manual restore alternative with preview

This alternative is not an extra step after launcher installation. From the
review-branch repository root, preview **as normal user on the Linux PC or T95**:

```bash
python3 tools/restore-ssh-dashboard.py
```

To apply, run **on the T95 with `sudo`**:

```bash
sudo python3 tools/restore-ssh-dashboard.py --apply
```

It verifies payloads/targets, backs up existing managed files and state under
`/var/backups/t95-dashboard/<time-random>/`, then atomically installs the
14 files. Identical installation stays unchanged without an extra backup.
An installation failure restores the previous state automatically.

For rollback, replace `BACKUP-NAME` with the actual printed backup directory
and run **on the T95 with `sudo`**:

```bash
sudo python3 tools/restore-ssh-dashboard.py --rollback /var/backups/t95-dashboard/BACKUP-NAME
```

Previous content/mode/ownership is restored; files newly introduced by the
installation are removed. SSH need not restart; the next login runs MOTD.
This manual tool uses its own backup location, separate from the new setup journal.

## Requirements and limits

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

## Verification

Temporary-filesystem checks covered preview, byte/mode-exact installation,
idempotence, rollback, rejected redirected targets, rejected modified
payloads, and automatic rollback after interruption. Source collection read
the running box only; no root restore was applied to it. Full reinstall/cold
boot acceptance remains open. The tool does not configure boot parameters,
voltages, Bluetooth, Samba, or SSH authentication.

<a id="restore-checklist"></a>

# ↩️ Restore checklist

[Deutsch](RESTORE-CHECKLIST.md) | **English**

Technical checklist for the already prepared eMMC reference installation.
For a new SD installation, use the [Samba quick start](../README.en.md); do not
repeat these manual steps after its script finishes.

Replace `__T95_USER__` and `__T95_MOUNT_BASE__` in templates with the actual
username and `/media/<username>` before applying them. Copying unchanged
Polkit/Samba templates does not expand shell variables. For this eMMC path,
`/srv/T95-DATA` must already be mounted persistently and verified.

| Part | Check |
| --- | --- |
| 🔎 Before starting | Existing user, verified eMMC mount, replaced template placeholders |
| 📦 Steps 1–5 | Packages, Samba account, group, data path, and share configuration |
| ⚙️ Steps 6–11 | Helpers, Polkit, udiskie, and persistent user service |
| ✅ Step 12 | Configuration, client access, USB automount, and safe eject |

<a id="prepare"></a>

## 📋 Prepare

**On the T95 as administrator; adapt technical examples before running them.**

These examples assume an existing Linux user;
replace `serveruser` with the desired name:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

<a id="check-manual-restoration"></a>

## ✅ Check manual restoration

1. Install `samba`, `samba-common-bin`, `udisks2`, `udiskie`,
   `dbus-user-session`, `polkitd`, `exfatprogs`, and `ntfs-3g`.
2. Ensure `$T95_USER` exists; set its Samba password with
   `smbpasswd -a $T95_USER`.
3. Add `$T95_USER` to `sambashare`; set `/var/lib/samba/usershares` to
   `root:sambashare`, mode `1770`.
4. Create `/srv/T95-DATA/Share`, owned by `$T95_USER:$T95_USER`, mode `2770`.
5. Apply global usershare options and `[T95-DATA]` from
   `config/samba/smb.conf.fragment`; do not create a static `[USB]` share.
6. Install `t95-usb-share` and `usb-eject` from `scripts/` into
   `/usr/local/bin/`, mode `0755`.
7. Replace the user placeholder in the Polkit rule and copy it to `/etc/polkit-1/rules.d/50-t95-udisks.rules`.
8. Copy `config.json` to `/home/$T95_USER/.config/udiskie/config.json`.
9. Copy `udiskie.service` to
   `/home/$T95_USER/.config/systemd/user/udiskie.service`.
10. Set user-file ownership to `$T95_USER:$T95_USER` and run
    `loginctl enable-linger $T95_USER`.
11. Start with `systemctl --user enable --now udiskie.service`.
12. Test `testparm`, automount, `net usershare list`, client access to
    `smb://SERVER-IP/`, and `usb-eject`.

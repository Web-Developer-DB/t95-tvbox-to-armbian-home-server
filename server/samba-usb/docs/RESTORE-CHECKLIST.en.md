# Restore checklist

[Deutsch](RESTORE-CHECKLIST.md) | **English**

For a fast manual restore. These examples assume an existing Linux user;
replace `serveruser` with the desired name:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

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
7. Copy the Polkit rule to `/etc/polkit-1/rules.d/50-t95-udisks.rules`.
8. Copy `config.json` to `/home/$T95_USER/.config/udiskie/config.json`.
9. Copy `udiskie.service` to
   `/home/$T95_USER/.config/systemd/user/udiskie.service`.
10. Set user-file ownership to `$T95_USER:$T95_USER` and run
    `loginctl enable-linger $T95_USER`.
11. Start with `systemctl --user enable --now udiskie.service`.
12. Test `testparm`, automount, `net usershare list`, client access to
    `smb://SERVER-IP/`, and `usb-eject`.

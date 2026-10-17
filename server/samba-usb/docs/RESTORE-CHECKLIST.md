<a id="restore-checkliste"></a>

# ↩️ Restore-Checkliste

**Deutsch** | [English](RESTORE-CHECKLIST.en.md)

Technische Checkliste für die bereits vorbereitete eMMC-Referenzinstallation.
Für eine neue SD-Installation den [Samba-Schnellstart](../README.md) verwenden;
nach dessen Skriptlauf diese manuellen Schritte nicht zusätzlich ausführen.

`__T95_USER__` und `__T95_MOUNT_BASE__` in Konfigurationsvorlagen müssen vor
der Übernahme durch den tatsächlichen Benutzer bzw. `/media/<Benutzer>`
ersetzt werden. Ein bloßes Kopieren der unveränderten Polkit-/Samba-Vorlagen
übernimmt keine Werte aus den Shell-Variablen. `/srv/T95-DATA` muss für den
hier beschriebenen eMMC-Pfad bereits dauerhaft eingehängt und geprüft sein.

| Teil | Kontrolle |
| --- | --- |
| 🔎 Vor Beginn | Vorhandener Benutzer, geprüfter eMMC-Mount und ersetzte Vorlagenplatzhalter |
| 📦 Schritte 1–5 | Pakete, Samba-Konto, Gruppe, Datenpfad und Freigabekonfiguration |
| ⚙️ Schritte 6–11 | Helfer, Polkit, udiskie und dauerhafter Benutzerdienst |
| ✅ Schritt 12 | Konfiguration, Clientzugriff, USB-Automount und sicherer Auswurf |

<a id="vorbereiten"></a>

## 📋 Vorbereiten

**Auf der T95 als Administrator; technische Beispiele vor dem Ausführen anpassen.**

Die folgenden Beispiele setzen einen vorhandenen Linux-Benutzer voraus. Ersetze
`serveruser` durch den gewünschten Namen:

```bash
export T95_USER=serveruser
export T95_UID="$(id -u "$T95_USER")"
```

<a id="manuelle-wiederherstellung-prüfen"></a>

## ✅ Manuelle Wiederherstellung prüfen

1. Pakete installieren: `samba`, `samba-common-bin`, `udisks2`, `udiskie`, `dbus-user-session`, `polkitd`, `exfatprogs`, `ntfs-3g`.
2. Linux-Benutzer `$T95_USER` muss existieren; Samba-Passwort mit `smbpasswd -a $T95_USER` setzen.
3. `$T95_USER` der Gruppe `sambashare` hinzufügen und `/var/lib/samba/usershares` auf `root:sambashare`, Mode `1770` setzen.
4. `/srv/T95-DATA/Share` anlegen, `$T95_USER:$T95_USER`, Mode `2770`.
5. Samba-Globaloptionen für Usershares und `[T95-DATA]` aus `config/samba/smb.conf.fragment` übernehmen. Keine statische `[USB]`-Freigabe anlegen.
6. `/usr/local/bin/t95-usb-share` und `/usr/local/bin/usb-eject` aus `scripts/` installieren, Mode `0755`.
7. Den Benutzerplatzhalter in der Polkit-Regel ersetzen und sie nach `/etc/polkit-1/rules.d/50-t95-udisks.rules` kopieren.
8. `config.json` nach `/home/$T95_USER/.config/udiskie/config.json` kopieren.
9. `udiskie.service` nach `/home/$T95_USER/.config/systemd/user/udiskie.service` kopieren.
10. Eigentümer der Benutzerdateien auf `$T95_USER:$T95_USER` setzen und `loginctl enable-linger $T95_USER` aktivieren.
11. User-Service mit `systemctl --user enable --now udiskie.service` starten.
12. `testparm`, USB-Automount, `net usershare list`, Client-Zugriff auf `smb://SERVER-IP/` und `usb-eject` testen.

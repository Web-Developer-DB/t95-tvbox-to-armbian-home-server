#!/usr/bin/env bash
# Reproduziert die dokumentierte T95-Samba-/USB-Konfiguration.
# Für eine frische Debian-/Armbian-Installation gedacht.
# ACHTUNG: Dieses Skript installiert Pakete, aktiviert Dienste und ersetzt
# /etc/samba/smb.conf nach einer Sicherung durch eine minimale Konfiguration.

set -Eeuo pipefail

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH

T95_USER="${T95_USER:?T95_USER muss gesetzt sein, z. B. T95_USER=serveruser}"
NETBIOS_NAME="${NETBIOS_NAME:-T95-SERVER}"
DATA_PATH="${DATA_PATH:-/srv/T95-DATA/Share}"

if [[ ! "$T95_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    echo "FEHLER: T95_USER enthält ungültige Zeichen: '$T95_USER'"
    exit 1
fi
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "Bitte als root ausführen: sudo $0"
    exit 1
fi

if ! id "$T95_USER" >/dev/null 2>&1; then
    echo "FEHLER: Linux-Benutzer '$T95_USER' existiert nicht."
    echo "Lege ihn zuerst an oder starte mit T95_USER=<name>."
    exit 1
fi

USER_UID="$(id -u "$T95_USER")"
USER_GID="$(id -g "$T95_USER")"
USER_HOME="$(getent passwd "$T95_USER" | cut -d: -f6)"
MOUNT_BASE="/media/$T95_USER"
STATE_DIR="$USER_HOME/.local/state/t95-usb-shares"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
    samba samba-common-bin \
    udisks2 udiskie dbus-user-session polkitd \
    exfatprogs ntfs-3g

# Samba usershares
if getent group sambashare >/dev/null 2>&1; then
    usermod -aG sambashare "$T95_USER"
else
    groupadd sambashare
    usermod -aG sambashare "$T95_USER"
fi

install -d -o root -g sambashare -m 1770 /var/lib/samba/usershares
install -d -o "$T95_USER" -g "$T95_USER" -m 0755 "$MOUNT_BASE"
install -d -o "$T95_USER" -g "$T95_USER" -m 0775 "$STATE_DIR"
install -d -o "$T95_USER" -g "$T95_USER" -m 0755 "$USER_HOME/.config/udiskie"
install -d -o "$T95_USER" -g "$T95_USER" -m 0755 "$USER_HOME/.config/systemd/user"

# Feste T95-DATA-Freigabe vorbereiten.
install -d -o "$T95_USER" -g "$T95_USER" -m 2770 "$DATA_PATH"

# Skripte installieren. Beide ermitteln den Benutzer und den Mountpfad
# dynamisch; dadurch gelangen keine lokalen Benutzernamen ins Repository.
install -o root -g root -m 0755 \
    "$ROOT_DIR/scripts/t95-usb-share" /usr/local/bin/t95-usb-share
install -o root -g root -m 0755 \
    "$ROOT_DIR/scripts/usb-eject" /usr/local/bin/usb-eject

# udiskie-Konfiguration + User-Service
install -o "$T95_USER" -g "$T95_USER" -m 0644 \
    "$ROOT_DIR/config/udiskie/config.json" \
    "$USER_HOME/.config/udiskie/config.json"

install -o "$T95_USER" -g "$T95_USER" -m 0644 \
    "$ROOT_DIR/config/systemd-user/udiskie.service" \
    "$USER_HOME/.config/systemd/user/udiskie.service"

# Polkit-Regel mit gewähltem Benutzer erzeugen.
sed "s/subject.user != \"__T95_USER__\"/subject.user != \"$T95_USER\"/" \
    "$ROOT_DIR/config/polkit/50-t95-udisks.rules" \
    > /etc/polkit-1/rules.d/50-t95-udisks.rules
chmod 0644 /etc/polkit-1/rules.d/50-t95-udisks.rules

# Samba-Konfiguration sichern und als bekannte Minimal-Konfiguration neu schreiben.
if [[ -f /etc/samba/smb.conf ]]; then
    cp -a /etc/samba/smb.conf "/etc/samba/smb.conf.before-t95.$(date +%Y%m%d-%H%M%S)"
fi

cat > /etc/samba/smb.conf <<SMBEOF
[global]
    workgroup = WORKGROUP
    server role = standalone server
    security = user
    map to guest = Bad User
    netbios name = $NETBIOS_NAME
    server min protocol = SMB2
    log file = /var/log/samba/log.%m
    max log size = 1000

    usershare path = /var/lib/samba/usershares
    usershare max shares = 20
    usershare owner only = no
    usershare allow guests = no
    usershare prefix allow list = $MOUNT_BASE

[T95-DATA]
    path = $DATA_PATH
    browseable = yes
    read only = no
    guest ok = no
    valid users = $T95_USER
    create mask = 0660
    directory mask = 0770
SMBEOF

# Keine statische [USB]-Freigabe: jedes Medium erhält einen eigenen usershare.
testparm -s

systemctl enable --now smbd
systemctl enable --now nmbd || true
systemctl start udisks2
systemctl try-restart polkit.service || true

# Samba-Benutzer anlegen, wenn noch nicht vorhanden. Passwort wird interaktiv gesetzt.
if ! pdbedit -L 2>/dev/null | cut -d: -f1 | grep -Fxq "$T95_USER"; then
    echo
    echo "Samba-Passwort für '$T95_USER' festlegen:"
    smbpasswd -a "$T95_USER"
fi

# User-Systemd ohne interaktive Anmeldung verfügbar machen.
loginctl enable-linger "$T95_USER"
systemctl start "user@${USER_UID}.service"

sudo -u "$T95_USER" XDG_RUNTIME_DIR="/run/user/$USER_UID" \
    systemctl --user daemon-reload
sudo -u "$T95_USER" XDG_RUNTIME_DIR="/run/user/$USER_UID" \
    systemctl --user enable --now udiskie.service

systemctl restart smbd

cat <<EOFMSG

Fertig.

Wichtige Tests:
  testparm -s
  sudo -u $T95_USER net usershare list
  sudo -u $T95_USER XDG_RUNTIME_DIR=/run/user/$USER_UID systemctl --user status udiskie.service --no-pager

Client-Zugriff (Beispiel):
  smb://<SERVER-IP>/

Dort erscheinen T95-DATA und alle aktuell eingesteckten USB-/SSD-Freigaben gemeinsam.
Sicher auswerfen:
  sudo usb-eject <Freigabename>
EOFMSG

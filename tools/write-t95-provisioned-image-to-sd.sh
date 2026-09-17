#!/usr/bin/env bash
# Write one locally provisioned T95 image to a removable USB SD card. The
# selected card is the only block device opened; T95 eMMC and FEL are excluded.
# CHANGE-ID: RELEASE HARDEN
# T95-CHANGE: accept only a locally personalized, manifest-matched image.
# PORTING-NOTE: replace /dev/sdX with the current removable SD device.
set -euo pipefail
umask 022

device=${1:-}
image=${2:-}
manifest=${3:-}
confirmation=${4:-}
expected_confirmation='WRITE-T95-PROVISIONED-TO-SDX'

die() { printf 'ABBRUCH: %s\n' "$*" >&2; exit 1; }
[[ $# -eq 4 ]] || die "Aufruf: $0 /dev/sdX PERSOENLICHES_IMAGE.img MANIFEST $expected_confirmation"
[[ "$device" =~ ^/dev/sd[a-z]+$ && -b "$device" ]] || die 'Ziel muss genau ein vorhandenes /dev/sdX sein'
[[ -f "$image" && ! -b "$image" && ! -L "$image" ]] || die 'Persönliches Image muss eine reguläre Datei sein'
[[ -f "$manifest" && ! -b "$manifest" && ! -L "$manifest" ]] || die 'Personalisierungsmanifest fehlt'
[[ "$confirmation" == "$expected_confirmation" ]] || die 'Bestätigungstoken stimmt nicht'
for tool in awk dd e2fsck findmnt grep head lsblk partprobe sed sha256sum stat sudo sync udevadm umount; do
    command -v "$tool" >/dev/null || die "Werkzeug fehlt: $tool"
done

field() { sed -n "s/^$1=//p" "$manifest"; }
[[ $(field format) == T95-PROVISIONED-IMAGE-1 ]] || die 'Unbekanntes Personalisierungsmanifest'
expected_name=$(field personalized_image_filename)
expected_size=$(field personalized_image_size)
expected_sha=$(field personalized_image_sha256)
[[ "$expected_name" == "$(basename "$image")" && "$expected_size" =~ ^[0-9]+$ && "$expected_sha" =~ ^[0-9a-f]{64}$ ]] \
    || die 'Personalisierungsmanifest passt nicht zum Image'
[[ $(field root_password_hash) == excluded && $(field purpose) == local_only_not_a_public_release_asset ]] \
    || die 'Manifest kennzeichnet keine sichere lokale Personalisierung'
actual_size=$(stat -c %s "$image")
actual_sha=$(sha256sum "$image" | awk '{print $1}')
[[ "$actual_size" == "$expected_size" && "$actual_sha" == "$expected_sha" ]] || die 'Persönliches Image wurde seit dem Provisionieren verändert'
[[ $((actual_size % 4194304)) -eq 0 && $(head -c 8 <(dd if="$image" bs=1 skip=8192 count=8 status=none)) == TOC0.GLH ]] \
    || die 'Persönliches Image ist kein erwartetes T95-TOC0-Image'

size=$(lsblk -dnbo SIZE "$device")
transport=$(lsblk -dno TRAN "$device" | sed 's/[[:space:]]*$//')
removable=$(lsblk -dno RM "$device" | sed 's/[[:space:]]*$//')
kind=$(lsblk -dno TYPE "$device" | sed 's/[[:space:]]*$//')
[[ "$size" =~ ^[0-9]+$ && "$size" -gt "$actual_size" ]] || die 'Ziel ist kleiner als das Image'
[[ "$transport" == usb && "$removable" == 1 && "$kind" == disk ]] || die 'Ziel ist keine wechselbare USB-SD-Karte'
while IFS= read -r partition; do
    [[ "$partition" == "$device" ]] && continue
    if findmnt -rn -S "$partition" -o TARGET | grep -Fxq /; then
        die 'Das Ziel enthält das laufende Root-Dateisystem'
    fi
done < <(lsblk -nrpo NAME "$device")

printf '%s\n' 'Sicherheitsprüfung bestanden:'
printf '  Image:       %s\n  Ziel:        %s (%s Byte, USB, wechselbar)\n' "$(basename "$image")" "$device" "$size"
printf '  Wirkung:     Der bisherige Inhalt von %s wird vollständig überschrieben.\n' "$device"
printf '  Ausgeschlossen: interne T95-eMMC, FEL und Android-Speicher.\n'
sudo -v
while IFS= read -r partition; do
    [[ "$partition" == "$device" ]] && continue
    if findmnt -rn -S "$partition" >/dev/null; then
        printf 'Hänge %s aus.\n' "$partition"
        sudo umount "$partition"
    fi
done < <(lsblk -nrpo NAME "$device")

printf 'Schreibe das lokal geprüfte persönliche Image nach %s.\n' "$device"
dd if="$image" | sudo dd of="$device" bs=4M conv=fsync status=progress
sync
sudo partprobe "$device"
sudo udevadm settle
blocks=$((actual_size / 4194304))
readback_sha=$(sudo dd if="$device" bs=4M count="$blocks" status=none | sha256sum | awk '{print $1}')
[[ "$readback_sha" == "$actual_sha" ]] || die 'Rückgelesenes SD-Image hat falschen Hash'
[[ $(sudo dd if="$device" bs=1 skip=8192 count=8 status=none) == TOC0.GLH ]] || die 'TOC0-Header fehlt nach Schreiben'
sudo e2fsck -fn "${device}1" >/dev/null || die 'Geschriebenes ext4-Dateisystem ist nicht prüfbar'
printf '\nERFOLG: Personalisierte SD wurde vollständig zurückgelesen und geprüft.\n'
printf 'Karte nur bei ausgeschalteter T95 einsetzen oder entnehmen.\n'
